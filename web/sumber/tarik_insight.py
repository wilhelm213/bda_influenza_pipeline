import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s = (SparkSession.builder.appName("tarik-insight").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "32")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

def rec(df, n=None):
    d = df.limit(n) if n else df
    return [r.asDict() for r in d.collect()]

kol = ["accession", "hash_seq", "n_duplikat_seq", "wakil_unik", "panjang",
       "n_acgt", "pct_ambigu", "gc_pct", "segmen", "segmen_sumber", "subtipe",
       "subtipe_sumber", "inang", "negara", "wilayah", "isolat",
       "tahun_koleksi", "presisi_tanggal", "tahun_rilis", "kelengkapan"]
q = s.read.parquet(H + "stage/sequences").select(*kol)
q.cache()
n_total = q.count()

OUT["ringkas"] = {
    "sekuens": n_total,
    "accession_unik": q.select("accession").distinct().count(),
    "sekuens_unik": q.select("hash_seq").distinct().count(),
    "wakil_unik": q.filter(F.col("wakil_unik")).count(),
    "negara": q.select("negara").distinct().count(),
    "subtipe": q.filter(F.col("subtipe").isNotNull()).select("subtipe").distinct().count(),
    "inang": q.filter(F.col("inang").isNotNull()).select("inang").distinct().count(),
    "galur": q.select("isolat").distinct().count(),
    "tahun_min": q.agg(F.min("tahun_koleksi")).first()[0],
    "tahun_maks": q.agg(F.max("tahun_koleksi")).first()[0],
    "basa_total": q.agg(F.sum("panjang")).first()[0],
}

OUT["per_tahun_rilis"] = rec(
    q.groupBy("tahun_rilis").count().orderBy("tahun_rilis"))
OUT["per_tahun_koleksi"] = rec(
    q.filter(F.col("tahun_koleksi").between(1918, 2026))
     .groupBy("tahun_koleksi").count().orderBy("tahun_koleksi"))

jeda = (q.filter(F.col("tahun_koleksi").between(1990, 2026)
                 & F.col("tahun_rilis").isNotNull())
         .withColumn("jeda", F.col("tahun_rilis") - F.col("tahun_koleksi"))
         .filter(F.col("jeda").between(0, 30)))
jeda.cache()
OUT["jeda_ringkas"] = {
    "n": jeda.count(),
    "rata": round(jeda.agg(F.avg("jeda")).first()[0], 2),
    "median": jeda.approxQuantile("jeda", [0.5], 0.001)[0],
    "p90": jeda.approxQuantile("jeda", [0.9], 0.001)[0],
}
OUT["jeda_sebaran"] = rec(jeda.groupBy("jeda").count().orderBy("jeda"))
OUT["jeda_per_tahun"] = rec(
    jeda.groupBy("tahun_koleksi")
        .agg(F.avg("jeda").alias("rata"), F.count("*").alias("n"))
        .orderBy("tahun_koleksi"))

OUT["presisi_tanggal"] = rec(
    q.groupBy("presisi_tanggal").count().orderBy(F.desc("count")))
OUT["kelengkapan"] = rec(
    q.groupBy("kelengkapan").count().orderBy(F.desc("count")))
OUT["sumber_segmen"] = rec(
    q.groupBy("segmen_sumber").count().orderBy(F.desc("count")))
OUT["sumber_subtipe"] = rec(
    q.groupBy("subtipe_sumber").count().orderBy(F.desc("count")))
OUT["ambigu_ember"] = rec(
    q.withColumn("ember", F.when(F.col("pct_ambigu") == 0, "0 (bersih)")
                  .when(F.col("pct_ambigu") < 0.1, "< 0,1%")
                  .when(F.col("pct_ambigu") < 1, "0,1 - 1%")
                  .when(F.col("pct_ambigu") < 5, "1 - 5%")
                  .otherwise(">= 5%"))
     .groupBy("ember").count())
OUT["rongga"] = [
    {"kolom": c,
     "kosong": q.filter(F.col(c).isNull() | (F.trim(F.col(c).cast("string")) == "")).count()}
    for c in ["subtipe", "inang", "negara", "tahun_koleksi", "isolat", "segmen"]]
OUT["duplikat_ember"] = rec(
    q.withColumn("ember", F.when(F.col("n_duplikat_seq") <= 1, "1 (tunggal)")
                  .when(F.col("n_duplikat_seq") <= 5, "2 - 5")
                  .when(F.col("n_duplikat_seq") <= 20, "6 - 20")
                  .when(F.col("n_duplikat_seq") <= 100, "21 - 100")
                  .otherwise("> 100"))
     .groupBy("ember").count())

OUT["per_segmen"] = rec(
    q.groupBy("segmen").agg(
        F.count("*").alias("n"),
        F.round(F.avg("panjang"), 1).alias("panjang_rata"),
        F.round(F.avg("gc_pct"), 2).alias("gc_rata"),
        F.round(F.avg("pct_ambigu"), 4).alias("ambigu_rata"),
        F.countDistinct("subtipe").alias("subtipe_unik")).orderBy("segmen"))
OUT["per_subtipe"] = rec(
    q.filter(F.col("subtipe").isNotNull()).groupBy("subtipe").count()
     .orderBy(F.desc("count")), 20)
OUT["per_negara"] = rec(
    q.filter(F.col("negara").isNotNull()).groupBy("negara").count()
     .orderBy(F.desc("count")), 25)
OUT["per_wilayah"] = rec(
    q.groupBy("wilayah").count().orderBy(F.desc("count")))
OUT["per_inang"] = rec(
    q.filter(F.col("inang").isNotNull()).groupBy("inang").count()
     .orderBy(F.desc("count")), 15)

top_sub = [r["subtipe"] for r in OUT["per_subtipe"][:8]]
OUT["subtipe_tahun"] = rec(
    q.filter(F.col("subtipe").isin(top_sub)
             & F.col("tahun_koleksi").between(1990, 2026))
     .groupBy("tahun_koleksi", "subtipe").count().orderBy("tahun_koleksi"))

top_inang = [r["inang"] for r in OUT["per_inang"][:6]]
OUT["inang_subtipe"] = rec(
    q.filter(F.col("inang").isin(top_inang) & F.col("subtipe").isin(top_sub[:6]))
     .groupBy("inang", "subtipe").count())

OUT["wilayah_tahun"] = rec(
    q.filter(F.col("tahun_koleksi").between(1995, 2026))
     .groupBy("tahun_koleksi", "wilayah").count().orderBy("tahun_koleksi"))

q.unpersist()
jeda.unpersist()

tepi = s.read.parquet(H + "graph/tepi")
OUT["graf_per_segmen"] = rec(
    tepi.groupBy("segmen").agg(
        F.count("*").alias("tepi"),
        F.round(F.avg("kemiripan"), 4).alias("kemiripan_rata"),
        F.round(F.min("kemiripan"), 4).alias("kemiripan_min")).orderBy("segmen"))
OUT["graf_total_tepi"] = tepi.count()

lin = s.read.parquet(H + "graph/lineage")
OUT["klaster_per_segmen"] = rec(
    lin.groupBy("segmen").agg(
        F.countDistinct("lineage_id").alias("klaster"),
        F.count("*").alias("simpul")).orderBy("segmen"))
uk = lin.groupBy("lineage_id").count()
OUT["klaster_ukuran"] = rec(
    uk.withColumn("ember", F.when(F.col("count") == 1, "1 (tunggal)")
                   .when(F.col("count") <= 5, "2 - 5")
                   .when(F.col("count") <= 20, "6 - 20")
                   .when(F.col("count") <= 100, "21 - 100")
                   .otherwise("> 100"))
      .groupBy("ember").count())
OUT["klaster_terbesar"] = rec(uk.orderBy(F.desc("count")), 12)

co = s.read.parquet(H + "graph/co_occurs")
OUT["co_total"] = co.count()
OUT["co_pasangan_segmen"] = rec(
    co.groupBy("seg_src", "seg_dst").agg(
        F.count("*").alias("tepi"),
        F.sum("n_galur").alias("galur")).orderBy(F.desc("tepi")))
OUT["co_teratas"] = rec(co.orderBy(F.desc("n_galur")), 20)

kd = s.read.parquet(H + "models/kandidat_reassortant")
kd.cache()
OUT["kandidat_ringkas"] = {
    "baris": kd.count(),
    "galur": kd.select("galur").distinct().count(),
    "keyakinan_rata": round(kd.agg(F.avg("keyakinan")).first()[0], 4),
}
OUT["kandidat_per_segmen"] = rec(
    kd.groupBy("segmen").count().orderBy("segmen"))
OUT["kandidat_per_wilayah"] = rec(
    kd.groupBy("wilayah").count().orderBy(F.desc("count")))
OUT["kandidat_per_tahun"] = rec(
    kd.filter(F.col("tahun_koleksi").between(1990, 2026))
      .groupBy("tahun_koleksi").count().orderBy("tahun_koleksi"))
OUT["kandidat_per_inang"] = rec(
    kd.groupBy("inang").count().orderBy(F.desc("count")), 12)
OUT["kandidat_silang"] = rec(
    kd.groupBy("subtipe_kelas", "prediksi_subtipe").count()
      .orderBy(F.desc("count")), 25)
OUT["kandidat_keyakinan"] = rec(
    kd.withColumn("ember", F.when(F.col("keyakinan") < 0.5, "< 0,50")
                   .when(F.col("keyakinan") < 0.7, "0,50 - 0,70")
                   .when(F.col("keyakinan") < 0.9, "0,70 - 0,90")
                   .otherwise(">= 0,90"))
      .groupBy("ember").count())
OUT["kandidat_teratas"] = rec(
    kd.orderBy(F.desc("keyakinan")).select(
        "accession", "galur", "segmen", "subtipe_kelas", "prediksi_subtipe",
        "keyakinan", "negara", "tahun_koleksi", "inang"), 25)

with open("/tmp/insight.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("KUNCI:", " ".join(sorted(OUT)))
print("SELESAI")
s.stop()
