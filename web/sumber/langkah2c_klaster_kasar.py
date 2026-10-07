import json
import os
import time
from functools import reduce

from pyspark.ml.feature import MinHashLSH
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window

AMBANG_UJI = [0.30]
N_GALUR = 5000
TEPI_MAKS = 20_000_000
HDFS_MIN_GB, LOKAL_MIN_GB = 60, 40
PAGU_HDFS_GB = 260

s = (SparkSession.builder.appName("langkah2c-kasar").master("local[4]")
     .config("spark.driver.memory", "5g")
     .config("spark.sql.shuffle.partitions", "96")
     .config("spark.cleaner.referenceTracking.cleanCheckpoints", "true")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
sc = s.sparkContext
sc.setCheckpointDir("hdfs://namenode:8020/bda/graph2/_ckpt_kasar")
H = "hdfs://namenode:8020/bda/"
OUT = {"catatan": "ambang 0,12 sudah diukur: sens 0,0892 spes 0,8322 "
                  "pres 0,5010 pengayaan_babi 1,30", "hasil": []}

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
    lab = (e.select(F.col("src").alias("id")).distinct()
            .withColumn("komp", F.col("id")))
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

fit = (s.read.parquet(H + "features/kmer_k8")
        .select("accession", "features", "segmen", "isolat", "inang",
                "subtipe", "tahun_koleksi")
        .withColumn("galur", F.coalesce(
            F.nullif(F.trim(F.col("isolat")), F.lit("")), F.col("accession"))))
utuh = (fit.groupBy("galur").agg(F.countDistinct("segmen").alias("ns"))
           .filter(F.col("ns") == 8).select("galur")
           .withColumn("urut", F.crc32(F.col("galur"))))
pilih = utuh.orderBy("urut").limit(N_GALUR).select("galur")
sub = fit.join(pilih, "galur", "inner").cache()
print("populasi: %d galur, %d sekuens" % (N_GALUR, sub.count()))

MAN = F.col("inang") == "Homo sapiens"
UNG = F.lower(F.col("inang")).rlike(
    "anas|anatidae|anser|branta|aves|avian|duck|goose|teal|arenaria")
H5X = (F.col("subtipe").startswith("H5") & (F.col("subtipe") != "H5N1")
       & (F.col("tahun_koleksi") >= 2014))
lab = (sub.withColumn("label",
       F.when(MAN & (F.col("subtipe") == "H1N1")
              & (F.col("tahun_koleksi") >= 2009), 1)
        .when((F.col("subtipe") == "H7N9") & (F.col("tahun_koleksi") >= 2013), 1)
        .when(F.col("subtipe") == "H1N2", 1).when(H5X, 1)
        .when(MAN & (F.col("subtipe") == "H1N1")
              & F.col("tahun_koleksi").between(1977, 2008), 0)
        .when(MAN & (F.col("subtipe") == "H3N2")
              & F.col("tahun_koleksi").between(1970, 2008), 0)
        .when(UNG & F.col("subtipe").isin("H3N8", "H4N6"), 0).otherwise(None))
       .filter(F.col("label").isNotNull())
       .select("accession", "label").distinct())
lab.cache()
print("berlabel di populasi ini: %d positif, %d negatif"
      % (lab.filter(F.col("label") == 1).count(),
         lab.filter(F.col("label") == 0).count()))

for amb in AMBANG_UJI:
    hg, lg = ruang()
    if hg < HDFS_MIN_GB or lg < LOKAL_MIN_GB:
        print("BERHENTI: ruang bebas HDFS %.0f / lokal %.0f GB" % (hg, lg))
        break
    tag = str(amb).replace(".", "")
    print("\n===== ambang jarak %.2f =====" % amb)
    t0 = time.time()
    tot = 0
    for seg in range(1, 9):
        ss = sub.filter(F.col("segmen") == seg).select("accession", "features")
        mh = MinHashLSH(inputCol="features", outputCol="h",
                        numHashTables=3, seed=42).fit(ss)
        pas = (mh.approxSimilarityJoin(ss, ss, amb, distCol="jarak")
                 .select(F.col("datasetA.accession").alias("src"),
                         F.col("datasetB.accession").alias("dst"))
                 .filter(F.col("src") < F.col("dst"))
                 .withColumn("segmen", F.lit(seg)))
        (pas.write.mode("overwrite" if seg == 1 else "append")
            .parquet(H + "graph2/kasar_%s" % tag))
        nt = (s.read.parquet(H + "graph2/kasar_%s" % tag)
               .filter(F.col("segmen") == seg).count())
        tot += nt
        print("   segmen %d: %d tepi" % (seg, nt))
        if tot > TEPI_MAKS:
            print("   BERHENTI: anggaran tepi dilampaui")
            break
    print("   total %d tepi dalam %.0f s" % (tot, time.time() - t0))

    tepi = s.read.parquet(H + "graph2/kasar_%s" % tag)
    kl = []
    for seg in range(1, 9):
        t = tepi.filter(F.col("segmen") == seg).select("src", "dst")
        if t.limit(1).count() == 0:
            continue
        kl.append(komponen(t).withColumn("segmen", F.lit(seg)))
    lin = (reduce(lambda a, b: a.union(b), kl)
           .withColumn("lineage_id", F.concat_ws(
               "_", F.lit("S"), F.col("segmen"), F.col("komp"))))
    lin.cache()
    n_simpul = lin.count()
    n_klaster = lin.select("lineage_id").distinct().count()
    per_seg = (lin.groupBy("segmen")
                  .agg(F.countDistinct("lineage_id").alias("klaster"))
                  .orderBy("segmen").toPandas().to_dict("records"))
    print("   %d simpul -> %d klaster (%.1f simpul/klaster)"
          % (n_simpul, n_klaster, n_simpul / n_klaster))
    print("   klaster per segmen:", [r["klaster"] for r in per_seg])

    d = (lin.select(F.col("id").alias("accession"), "lineage_id", "segmen")
            .join(sub.select("accession", "galur").distinct(),
                  "accession", "inner"))
    per = d.groupBy("galur").agg(F.countDistinct("segmen").alias("ns"))
    layak = per.filter(F.col("ns") >= 4).select("galur")
    n_layak = layak.count()
    dl = d.join(layak, "galur", "inner")
    a_ = dl.select("galur", F.col("lineage_id").alias("ki"),
                   F.col("segmen").alias("si"))
    b_ = dl.select("galur", F.col("lineage_id").alias("kj"),
                   F.col("segmen").alias("sj"))
    pas2 = (a_.join(b_, "galur").filter(F.col("si") < F.col("sj"))
              .select("galur", "ki", "kj").distinct().cache())
    duk = pas2.groupBy("ki", "kj").agg(
        F.countDistinct("galur").alias("dukungan"))
    der = (pas2.select(F.col("ki").alias("k"), F.col("kj").alias("l"))
               .union(pas2.select(F.col("kj").alias("k"),
                                  F.col("ki").alias("l")))
               .groupBy("k").agg(F.countDistinct("l").alias("derajat")))
    qd = der.approxQuantile("derajat", [0.5], 0.01)[0]
    qduk = duk.approxQuantile("dukungan", [0.5, 0.9], 0.01)
    print("   derajat median %.0f | dukungan median %.0f p90 %.0f"
          % (qd, qduk[0], qduk[1]))
    pdd = (pas2.join(duk, ["ki", "kj"])
               .join(der.withColumnRenamed("k", "ki")
                        .withColumnRenamed("derajat", "dki"), "ki")
               .join(der.withColumnRenamed("k", "kj")
                        .withColumnRenamed("derajat", "dkj"), "kj")
               .withColumn("dmin", F.least("dki", "dkj"))
               .withColumn("skor", F.col("dmin") / F.col("dukungan")))
    w = Window.partitionBy("galur").orderBy(F.desc("skor"))
    sg = (pdd.withColumn("r", F.row_number().over(w))
             .filter(F.col("r") == 1)
             .select("galur", "dukungan", "dmin", "skor").cache())
    kand = sg.filter((F.col("dukungan") == 1) & (F.col("dmin") >= max(2.0, qd)))
    n_k = kand.count()
    print("   galur layak %d | kandidat %d (%.2f%%)"
          % (n_layak, n_k, 100 * n_k / n_layak if n_layak else 0))

    acc = (dl.join(kand.select("galur"), "galur", "inner")
             .select("accession").distinct().withColumn("t", F.lit(1)))
    j = lab.join(acc, "accession", "left").withColumn(
        "t", F.coalesce(F.col("t"), F.lit(0)))
    tp = j.filter((F.col("label") == 1) & (F.col("t") == 1)).count()
    fn = j.filter((F.col("label") == 1) & (F.col("t") == 0)).count()
    fp = j.filter((F.col("label") == 0) & (F.col("t") == 1)).count()
    tn = j.filter((F.col("label") == 0) & (F.col("t") == 0)).count()
    sens = tp / (tp + fn) if tp + fn else float("nan")
    spes = tn / (tn + fp) if tn + fp else float("nan")
    pres = tp / (tp + fp) if tp + fp else float("nan")
    fpr = 1 - spes
    print("   TP %d FN %d FP %d TN %d" % (tp, fn, fp, tn))
    print("   sens %.4f  spes %.4f  pres %.4f  TPR-FPR %+.4f"
          % (sens, spes, pres, sens - fpr))

    BABI = F.lower(F.col("inang")).startswith("sus ")
    gi = (dl.join(sub.select("galur", "inang").distinct(), "galur", "inner")
            .withColumn("babi", F.when(BABI, 1).otherwise(0))
            .groupBy("galur").agg(F.max("babi").alias("babi")))
    p0 = (gi.filter(F.col("babi") == 1).count() / gi.count()) if gi.count() else 0
    kg = kand.select("galur").join(gi, "galur", "inner")
    p1 = (kg.filter(F.col("babi") == 1).count() / kg.count()) if kg.count() else 0
    peng = p1 / p0 if p0 else None
    print("   pengayaan babi %.2f x" % peng if peng else "   pengayaan babi n/a")

    OUT["hasil"].append({
        "ambang": amb, "tepi": tot, "simpul": n_simpul, "klaster": n_klaster,
        "simpul_per_klaster": round(n_simpul / n_klaster, 2),
        "klaster_per_segmen": per_seg, "galur_layak": n_layak,
        "kandidat": n_k, "tp": tp, "fn": fn, "fp": fp, "tn": tn,
        "sensitivitas": round(sens, 4), "spesifisitas": round(spes, 4),
        "presisi": round(pres, 4), "tpr_minus_fpr": round(sens - fpr, 4),
        "pengayaan_babi": round(peng, 3) if peng else None})
    lin.unpersist()
    pas2.unpersist()
    sg.unpersist()

with open("/tmp/klaster_kasar.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("\nditulis /tmp/klaster_kasar.json")
s.stop()
