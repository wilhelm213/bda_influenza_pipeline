import json
import os
import time

from pyspark.ml.feature import MinHashLSH
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

AMBANG = 0.12
HASH = 3
TAHAP = [2500, 5000, 10000, 20000, 40000]
TEPI_MAKS = 25_000_000
HDFS_MIN_GB = 60
LOKAL_MIN_GB = 40

s = (SparkSession.builder.appName("langkah4-kurva").master("local[4]")
     .config("spark.driver.memory", "5g")
     .config("spark.sql.shuffle.partitions", "96")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
sc = s.sparkContext
H = "hdfs://namenode:8020/bda/"

def ruang():
    fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(
        sc._jsc.hadoopConfiguration())
    hdfs_gb = fs.getStatus().getRemaining() / 1e9
    st = os.statvfs("/tmp")
    lokal_gb = st.f_bavail * st.f_frsize / 1e9
    return hdfs_gb, lokal_gb

fitur = s.read.parquet(H + "features/kmer_k8").select(
    "accession", "features", "segmen")
hasil = []

for seg in (3, 4):
    pop = fitur.filter(F.col("segmen") == seg).select("accession", "features")
    n_pop = pop.count()
    print("\n===== segmen %d: populasi unik %d =====" % (seg, n_pop))
    for n in TAHAP:
        if n > n_pop:
            print("  %6d simpul: melebihi populasi, dilewati" % n)
            continue
        hg, lg = ruang()
        if hg < HDFS_MIN_GB or lg < LOKAL_MIN_GB:
            print("  BERHENTI: ruang bebas HDFS %.1f GB / lokal %.1f GB "
                  "di bawah ambang" % (hg, lg))
            break

        sub = pop.orderBy("accession").limit(n).cache()
        sub.count()
        t0 = time.time()
        mh = MinHashLSH(inputCol="features", outputCol="h",
                        numHashTables=HASH, seed=42).fit(sub)
        pas = (mh.approxSimilarityJoin(sub, sub, AMBANG, distCol="jarak")
                 .select(F.col("datasetA.accession").alias("src"),
                         F.col("datasetB.accession").alias("dst"))
                 .filter(F.col("src") < F.col("dst")))
        n_tepi = pas.count()
        dt = time.time() - t0
        hg2, lg2 = ruang()
        baris = {"segmen": seg, "simpul": n, "tepi": n_tepi,
                 "detik": round(dt, 1),
                 "tepi_per_simpul": round(n_tepi / n, 3),
                 "hdfs_bebas_gb": round(hg2, 1),
                 "lokal_bebas_gb": round(lg2, 1)}
        hasil.append(baris)
        print("  %6d simpul -> %12d tepi  %7.1f s  %8.2f tepi/simpul  "
              "(HDFS %.0f GB, lokal %.0f GB bebas)"
              % (n, n_tepi, dt, n_tepi / n, hg2, lg2))
        sub.unpersist()
        if n_tepi > TEPI_MAKS:
            print("  BERHENTI: anggaran tepi %d dilampaui" % TEPI_MAKS)
            break

ring = {"ambang": AMBANG, "hash": HASH, "tahap": hasil}
if len(hasil) >= 3:
    import numpy as np
    for seg in (3, 4):
        h = [r for r in hasil if r["segmen"] == seg and r["tepi"] > 0]
        if len(h) < 3:
            continue
        x = np.log([r["simpul"] for r in h])
        y = np.log([r["tepi"] for r in h])
        b, a = np.polyfit(x, y, 1)

        ring["pangkat_seg%d" % seg] = round(float(b), 3)
        n_pop = int(fitur.filter(F.col("segmen") == seg).count())
        ring["ramal_penuh_seg%d" % seg] = {
            "simpul": n_pop,
            "tepi": int(np.exp(a) * n_pop ** b)}
        print("\nsegmen %d: tepi ~ simpul^%.2f  ->  ramalan pada %d simpul "
              "= %.0f juta tepi" % (seg, b, n_pop,
                                    np.exp(a) * n_pop ** b / 1e6))

with open("/tmp/kurva_skala.json", "w") as f:
    json.dump(ring, f, indent=1)
print("\nditulis /tmp/kurva_skala.json")
s.stop()
