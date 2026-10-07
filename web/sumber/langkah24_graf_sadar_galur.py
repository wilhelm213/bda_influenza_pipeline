import json
import os
import time

from pyspark.ml.feature import MinHashLSH
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

AMBANG, HASH = 0.12, 3
TAHAP = [5000, 15000, 30000]
TEPI_MAKS = 30_000_000
HDFS_MIN_GB, LOKAL_MIN_GB = 60, 40
PAGU_HDFS_GB = 260

s = (SparkSession.builder.appName("langkah24-sadar-galur").master("local[4]")
     .config("spark.driver.memory", "5g")
     .config("spark.sql.shuffle.partitions", "96")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
sc = s.sparkContext
sc.setCheckpointDir("hdfs://namenode:8020/bda/graph2/_ckpt")
H = "hdfs://namenode:8020/bda/"
OUT = {"ambang": AMBANG, "hash": HASH, "tahap": []}

def ruang():
    fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(
        sc._jsc.hadoopConfiguration())
    st_ = fs.getStatus()
    terpakai_gb = st_.getUsed() / 1e9
    sisa_pagu_gb = PAGU_HDFS_GB - terpakai_gb
    akar = os.statvfs("/")
    akar_gb = akar.f_bavail * akar.f_frsize / 1e9
    return (sisa_pagu_gb, akar_gb)

def komponen(tepi, maks=20):
    e = (tepi.select("src", "dst")
             .union(tepi.select(F.col("dst").alias("src"),
                                F.col("src").alias("dst")))
             .distinct().checkpoint(eager=True))
    lab = e.select(F.col("src").alias("id")).distinct() \
           .withColumn("komp", F.col("id"))
    for i in range(maks):
        baru = (e.join(lab, e.src == lab.id)
                 .groupBy(F.col("dst").alias("id"))
                 .agg(F.min("komp").alias("kand")))
        lab2 = (lab.join(baru, "id", "left")
                   .withColumn("komp2", F.least(
                       F.col("komp"), F.coalesce(F.col("kand"), F.col("komp"))))
                   .select("id", F.col("komp2").alias("komp"))
                   .checkpoint(eager=True))
        ubah = (lab2.join(lab.withColumnRenamed("komp", "lama"), "id")
                    .filter(F.col("komp") != F.col("lama")).count())
        lab = lab2
        if ubah == 0:
            break
    return lab

fit = s.read.parquet(H + "features/kmer_k8").select(
    "accession", "features", "segmen", "isolat", "inang", "subtipe",
    "negara", "wilayah", "tahun_koleksi")
fit = fit.withColumn("galur", F.coalesce(
    F.nullif(F.trim(F.col("isolat")), F.lit("")), F.col("accession")))
utuh = (fit.groupBy("galur").agg(F.countDistinct("segmen").alias("ns"))
           .filter(F.col("ns") == 8).select("galur"))
utuh.cache()
n_utuh = utuh.count()
print("galur bergenom utuh (8 segmen): %d" % n_utuh)
OUT["galur_utuh"] = n_utuh

utuh = utuh.withColumn("urut", F.crc32(F.col("galur")))
dipakai = None

for n in TAHAP:
    if n > n_utuh:
        print("  %d galur melebihi populasi, dilewati" % n)
        continue
    hg, lg = ruang()
    if hg < HDFS_MIN_GB or lg < LOKAL_MIN_GB:
        print("  BERHENTI: HDFS %.0f GB / lokal %.0f GB di bawah ambang"
              % (hg, lg))
        break
    pilih = utuh.orderBy("urut").limit(n).select("galur")
    sub = fit.join(pilih, "galur", "inner").cache()
    n_sek = sub.count()
    print("\n== %d galur -> %d sekuens ==" % (n, n_sek))
    t0 = time.time()
    tot_tepi, per_seg = 0, []
    for seg in range(1, 9):
        ss = sub.filter(F.col("segmen") == seg).select("accession", "features")
        mh = MinHashLSH(inputCol="features", outputCol="h",
                        numHashTables=HASH, seed=42).fit(ss)
        pas = (mh.approxSimilarityJoin(ss, ss, AMBANG, distCol="jarak")
                 .select(F.col("datasetA.accession").alias("src"),
                         F.col("datasetB.accession").alias("dst"),
                         (1 - F.col("jarak")).alias("kemiripan"))
                 .filter(F.col("src") < F.col("dst"))
                 .withColumn("segmen", F.lit(seg)))
        (pas.write.mode("overwrite" if seg == 1 else "append")
            .parquet(H + "graph2/tepi_n%d" % n))
        nt = s.read.parquet(H + "graph2/tepi_n%d" % n) \
              .filter(F.col("segmen") == seg).count()
        per_seg.append({"segmen": seg, "tepi": nt})
        tot_tepi += nt
        print("   segmen %d: %d tepi" % (seg, nt))
        if tot_tepi > TEPI_MAKS:
            print("   BERHENTI: anggaran tepi dilampaui")
            break
    dt = time.time() - t0
    hg2, lg2 = ruang()
    OUT["tahap"].append({"galur": n, "sekuens": n_sek, "tepi": tot_tepi,
                         "detik": round(dt, 1), "per_segmen": per_seg,
                         "hdfs_bebas_gb": round(hg2, 1),
                         "lokal_bebas_gb": round(lg2, 1)})
    print("   total %d tepi dalam %.0f s (HDFS %.0f GB bebas)"
          % (tot_tepi, dt, hg2))
    dipakai = n
    sub.unpersist()
    if tot_tepi > TEPI_MAKS:
        break

OUT["tahap_dipakai"] = dipakai
if dipakai is None:
    print("tidak ada tahap yang selesai")
    with open("/tmp/sadar_galur.json", "w") as f:
        json.dump(OUT, f, indent=1)
    s.stop()
    raise SystemExit(0)

tepi = s.read.parquet(H + "graph2/tepi_n%d" % dipakai)
klas = []
for seg in range(1, 9):
    t = tepi.filter(F.col("segmen") == seg).select("src", "dst")
    if t.limit(1).count() == 0:
        continue
    k = komponen(t).withColumn("segmen", F.lit(seg))
    klas.append(k)
    print("  segmen %d: %d simpul berklaster" % (seg, k.count()))
from functools import reduce
lin = reduce(lambda a, b: a.union(b), klas).withColumn(
    "lineage_id", F.concat_ws("_", F.lit("S"), F.col("segmen"), F.col("komp")))
lin.write.mode("overwrite").parquet(H + "graph2/lineage_n%d" % dipakai)
print("klaster ditulis ke graph2/lineage_n%d" % dipakai)

with open("/tmp/sadar_galur.json", "w") as f:
    json.dump(OUT, f, indent=1)
print("ditulis /tmp/sadar_galur.json")
s.stop()
