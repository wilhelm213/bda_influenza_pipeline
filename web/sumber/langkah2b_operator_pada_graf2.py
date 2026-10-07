import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window

s = (SparkSession.builder.appName("langkah2b-operator").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "64")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

def ada(p):
    try:
        s.read.parquet(H + p).limit(1).count()
        return True
    except Exception:
        return False

N = None
for n in (30000, 15000, 5000):
    if ada("graph2/lineage_n%d" % n):
        N = n
        break
if N is None:
    print("graph2/lineage_n* belum ada. Jalankan langkah24 lebih dulu.")
    s.stop()
    raise SystemExit(1)
print("memakai graph2/lineage_n%d" % N)
OUT["tahap"] = N

lin = s.read.parquet(H + "graph2/lineage_n%d" % N).select(
    F.col("id").alias("accession"), "lineage_id", "segmen")
meta = (s.read.parquet(H + "features/kmer_k8")
         .select("accession", "isolat", "subtipe", "inang", "wilayah",
                 "tahun_koleksi")
         .withColumn("galur", F.coalesce(
             F.nullif(F.trim(F.col("isolat")), F.lit("")), F.col("accession"))))
d = lin.join(meta, "accession", "inner").cache()

per = d.groupBy("galur").agg(F.countDistinct("segmen").alias("ns"))
print("sebaran segmen per galur:")
per.groupBy("ns").count().orderBy("ns").show(10)
layak = per.filter(F.col("ns") >= 4).select("galur")
n_layak = layak.count()
print("galur dengan >= 4 segmen berklaster: %d" % n_layak)
OUT["galur_layak"] = n_layak

dl = d.join(layak, "galur", "inner")
a = dl.select("galur", F.col("lineage_id").alias("ki"),
              F.col("segmen").alias("si"))
b = dl.select("galur", F.col("lineage_id").alias("kj"),
              F.col("segmen").alias("sj"))
pas = (a.join(b, "galur").filter(F.col("si") < F.col("sj"))
        .select("galur", "ki", "kj", "si", "sj").distinct().cache())

dukung = pas.groupBy("ki", "kj").agg(
    F.countDistinct("galur").alias("dukungan"))
derajat = (pas.select(F.col("ki").alias("k"), F.col("kj").alias("lain"))
              .union(pas.select(F.col("kj").alias("k"),
                                F.col("ki").alias("lain")))
              .groupBy("k").agg(F.countDistinct("lain").alias("derajat")))
qd = derajat.approxQuantile("derajat", [0.5, 0.75], 0.01)
print("derajat klaster: median %.0f  p75 %.0f" % (qd[0], qd[1]))
OUT["derajat"] = {"median": qd[0], "p75": qd[1]}

pd_ = (pas.join(dukung, ["ki", "kj"])
          .join(derajat.withColumnRenamed("k", "ki")
                       .withColumnRenamed("derajat", "dki"), "ki")
          .join(derajat.withColumnRenamed("k", "kj")
                       .withColumnRenamed("derajat", "dkj"), "kj")
          .withColumn("derajat_min", F.least("dki", "dkj"))
          .withColumn("skor", F.col("derajat_min") / F.col("dukungan")))
w = Window.partitionBy("galur").orderBy(F.desc("skor"))
sg = (pd_.withColumn("r", F.row_number().over(w)).filter(F.col("r") == 1)
         .select("galur", "ki", "kj", "si", "sj", "dukungan",
                 "derajat_min", "skor").cache())

qs = sg.approxQuantile("skor", [0.5, 0.9, 0.95, 0.99], 0.001)
print("skor: median %.3f  p90 %.3f  p95 %.3f  p99 %.3f" % tuple(qs))
OUT["kuantil_skor"] = dict(zip(["p50", "p90", "p95", "p99"],
                               [round(q, 4) for q in qs]))

amb_der = max(2.0, qd[0])
kand = sg.filter((F.col("dukungan") == 1) & (F.col("derajat_min") >= amb_der))
n_k = kand.count()
print("ambang: dukungan == 1 dan derajat_min >= %.0f" % amb_der)
print("kandidat: %d dari %d galur layak (%.2f%%)"
      % (n_k, n_layak, 100 * n_k / n_layak if n_layak else 0))
OUT["ambang"] = {"dukungan": 1, "derajat_min": amb_der}
OUT["kandidat"] = n_k

acc = (dl.join(kand.select("galur"), "galur", "inner")
         .select("accession", "galur").distinct())
acc.write.mode("overwrite").parquet(H + "graph2/kandidat_n%d" % N)
print("ditulis graph2/kandidat_n%d (%d accession)" % (N, acc.count()))

BABI = F.lower(F.col("inang")).startswith("sus ")
gi = (dl.select("galur", "inang").distinct()
        .withColumn("babi", F.when(BABI, 1).otherwise(0))
        .groupBy("galur").agg(F.max("babi").alias("babi")))
pop_g = sg.select("galur").join(gi, "galur", "left").fillna({"babi": 0})
tot = pop_g.count()
p0 = pop_g.filter(F.col("babi") == 1).count() / tot
kg = kand.select("galur").join(gi, "galur", "left").fillna({"babi": 0})
if kg.count():
    p1 = kg.filter(F.col("babi") == 1).count() / kg.count()
    print("pangsa babi: populasi %.2f%%  kandidat %.2f%%  pengayaan %.2f x"
          % (100 * p0, 100 * p1, p1 / p0 if p0 else float("nan")))
    OUT["pengayaan_babi"] = {"populasi": round(100 * p0, 3),
                             "kandidat": round(100 * p1, 3),
                             "pengayaan": round(p1 / p0, 3) if p0 else None}

OUT["contoh"] = [r.asDict() for r in
                 kand.orderBy(F.desc("skor")).limit(25).collect()]
with open("/tmp/operator_graf2.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("ditulis /tmp/operator_graf2.json")
s.stop()
