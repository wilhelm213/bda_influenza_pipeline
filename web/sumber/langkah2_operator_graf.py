import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window

s = (SparkSession.builder.appName("langkah2-operator").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "48")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

lin = s.read.parquet(H + "graph/lineage").select(
    F.col("id").alias("accession"), "lineage_id", "segmen")
meta = s.read.parquet(H + "stage/sequences").select(
    "accession", "isolat", "subtipe", "inang", "negara", "wilayah",
    "tahun_koleksi")
d = (lin.join(meta, "accession", "inner")
        .withColumn("galur", F.coalesce(
            F.nullif(F.trim(F.col("isolat")), F.lit("")), F.col("accession"))))
d.cache()
OUT["simpul_graf"] = d.count()

per_galur = (d.groupBy("galur")
              .agg(F.countDistinct("segmen").alias("n_segmen"),
                   F.count("*").alias("n_sekuens")))
sebaran = (per_galur.groupBy("n_segmen").count()
                    .orderBy("n_segmen").toPandas())
print("sebaran jumlah segmen per galur di dalam graf:")
print(sebaran.to_string(index=False))
OUT["segmen_per_galur"] = sebaran.to_dict("records")

layak = per_galur.filter(F.col("n_segmen") >= 2).select("galur")
n_layak = layak.count()
print("\ngalur dengan >= 2 segmen di graf : %d" % n_layak)
OUT["galur_layak"] = n_layak

if n_layak < 30:
    print("\nTERLALU SEDIKIT untuk mengevaluasi operator.")
    print("Sebabnya struktural: graf dibangun atas sampel maksimum 2.500")
    print("simpul per segmen yang diambil per segmen secara terpisah,")
    print("sehingga peluang satu galur terwakili di dua segmen sekaligus")
    print("kecil. Operator ini baru bermakna setelah graf dinaikkan")
    print("skalanya (langkah 4) atau penyampelan dibuat sadar-galur.")
    OUT["status"] = "tertahan: perlu graf berskala atau sampel sadar-galur"
    with open("/tmp/operator_graf.json", "w") as f:
        json.dump(OUT, f, indent=1, default=str)
    s.stop()
    raise SystemExit(0)

OUT["status"] = "dievaluasi"
dl = d.join(layak, "galur", "inner")

a = dl.select("galur", F.col("lineage_id").alias("ki"),
              F.col("segmen").alias("si"))
b = dl.select("galur", F.col("lineage_id").alias("kj"),
              F.col("segmen").alias("sj"))
pas = (a.join(b, "galur").filter(F.col("si") < F.col("sj"))
        .select("galur", "ki", "kj", "si", "sj").distinct())
pas.cache()

dukung = (pas.groupBy("ki", "kj")
             .agg(F.countDistinct("galur").alias("dukungan")))
derajat = (pas.select(F.col("ki").alias("k"), F.col("kj").alias("lain"))
              .union(pas.select(F.col("kj").alias("k"),
                                F.col("ki").alias("lain")))
              .groupBy("k").agg(F.countDistinct("lain").alias("derajat")))

pd_ = (pas.join(dukung, ["ki", "kj"])
          .join(derajat.withColumnRenamed("k", "ki")
                       .withColumnRenamed("derajat", "dki"), "ki")
          .join(derajat.withColumnRenamed("k", "kj")
                       .withColumnRenamed("derajat", "dkj"), "kj")
          .withColumn("derajat_min", F.least("dki", "dkj"))
          .withColumn("skor", F.col("derajat_min") / F.col("dukungan")))

w = Window.partitionBy("galur").orderBy(F.desc("skor"))
skor_galur = (pd_.withColumn("r", F.row_number().over(w))
                 .filter(F.col("r") == 1)
                 .select("galur", "ki", "kj", "si", "sj", "dukungan",
                         "derajat_min", "skor"))
skor_galur.cache()

print("\nsebaran skor operator:")
qs = skor_galur.approxQuantile("skor", [0.5, 0.75, 0.9, 0.95, 0.99], 0.001)
print("  median %.3f  p75 %.3f  p90 %.3f  p95 %.3f  p99 %.3f"
      % tuple(qs))
OUT["kuantil_skor"] = dict(zip(["p50", "p75", "p90", "p95", "p99"],
                               [round(q, 4) for q in qs]))

med_der = derajat.approxQuantile("derajat", [0.5], 0.01)[0]
kand_graf = skor_galur.filter((F.col("dukungan") <= 2)
                              & (F.col("derajat_min") >= med_der))
n_kg = kand_graf.count()
print("\nambang: dukungan <= 2 dan derajat_min >= %.0f (median derajat)"
      % med_der)
print("kandidat dari graf : %d dari %d galur layak (%.2f%%)"
      % (n_kg, n_layak, 100 * n_kg / n_layak))
OUT["ambang"] = {"dukungan_maks": 2, "derajat_min": med_der}
OUT["kandidat_graf"] = n_kg

ml = (s.read.parquet(H + "models/kandidat_reassortant")
       .select("galur").distinct().withColumn("ml", F.lit(1)))
gab = (skor_galur.select("galur")
        .withColumn("graf", F.when(F.col("galur").isin(
            [r["galur"] for r in kand_graf.select("galur").collect()]), 1)
            .otherwise(0))
        .join(ml, "galur", "left")
        .withColumn("ml", F.coalesce(F.col("ml"), F.lit(0))))
sil = gab.groupBy("graf", "ml").count().toPandas()
print("\nkesepakatan graf vs ML (pada galur layak):")
print(sil.to_string(index=False))
OUT["silang_graf_ml"] = sil.to_dict("records")

BABI = F.lower(F.col("inang")).startswith("sus ")
inf = (dl.select("galur", "inang").distinct()
         .withColumn("babi", F.when(BABI, 1).otherwise(0))
         .groupBy("galur").agg(F.max("babi").alias("babi")))
ug = gab.join(inf, "galur", "left").fillna({"babi": 0})
tot = ug.count()
p_babi = ug.filter(F.col("babi") == 1).count() / tot
kg = ug.filter(F.col("graf") == 1)
if kg.count():
    p_kg = kg.filter(F.col("babi") == 1).count() / kg.count()
    print("\npangsa babi: populasi layak %.2f%%, kandidat graf %.2f%% "
          "-> pengayaan %.2f x" % (100 * p_babi, 100 * p_kg,
                                   p_kg / p_babi if p_babi else float("nan")))
    OUT["pengayaan_babi_graf"] = {
        "pangsa_populasi": round(100 * p_babi, 3),
        "pangsa_kandidat": round(100 * p_kg, 3),
        "pengayaan": round(p_kg / p_babi, 3) if p_babi else None}

OUT["contoh_kandidat"] = [r.asDict() for r in
                          kand_graf.orderBy(F.desc("skor")).limit(25).collect()]

with open("/tmp/operator_graf.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("\nditulis /tmp/operator_graf.json")
s.stop()
