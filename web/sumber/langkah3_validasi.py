import json
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s = (SparkSession.builder.appName("langkah3-validasi").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "48")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

pop = (s.read.parquet(H + "features/kmer_k8")
        .select("accession", "isolat", "subtipe", "inang", "negara",
                "wilayah", "tahun_koleksi")
        .withColumn("galur", F.coalesce(
            F.nullif(F.trim(F.col("isolat")), F.lit("")), F.col("accession"))))

MAN = F.col("inang") == "Homo sapiens"
UNGGAS = F.lower(F.col("inang")).rlike(
    "anas|anatidae|anser|branta|aves|avian|duck|goose|teal|shorebird|arenaria")
H5X = (F.col("subtipe").startswith("H5")
       & (F.col("subtipe") != "H5N1") & (F.col("tahun_koleksi") >= 2014))

lab = pop.withColumn(
    "label",
    F.when(MAN & (F.col("subtipe") == "H1N1")
           & (F.col("tahun_koleksi") >= 2009), 1)
     .when((F.col("subtipe") == "H7N9") & (F.col("tahun_koleksi") >= 2013), 1)
     .when(F.col("subtipe") == "H1N2", 1)
     .when(H5X, 1)
     .when(MAN & (F.col("subtipe") == "H1N1")
           & F.col("tahun_koleksi").between(1977, 2008), 0)
     .when(MAN & (F.col("subtipe") == "H3N2")
           & F.col("tahun_koleksi").between(1970, 2008), 0)
     .when(UNGGAS & F.col("subtipe").isin("H3N8", "H4N6"), 0)
     .otherwise(None))

berlabel = lab.filter(F.col("label").isNotNull())
berlabel.cache()
n_pos = berlabel.filter(F.col("label") == 1).count()
n_neg = berlabel.filter(F.col("label") == 0).count()
print("himpunan berlabel: %d positif, %d negatif" % (n_pos, n_neg))
OUT["himpunan"] = {"positif": n_pos, "negatif": n_neg}
OUT["rincian"] = (berlabel.groupBy("label", "subtipe").count()
                  .orderBy("label", F.desc("count")).limit(30)
                  .toPandas().to_dict("records"))

def metrik(nama, tertandai_df, catatan=""):
    j = (berlabel.join(tertandai_df.withColumn("tandai", F.lit(1)),
                       "accession", "left")
                 .withColumn("tandai", F.coalesce(F.col("tandai"), F.lit(0))))
    tp = j.filter((F.col("label") == 1) & (F.col("tandai") == 1)).count()
    fn = j.filter((F.col("label") == 1) & (F.col("tandai") == 0)).count()
    fp = j.filter((F.col("label") == 0) & (F.col("tandai") == 1)).count()
    tn = j.filter((F.col("label") == 0) & (F.col("tandai") == 0)).count()
    sens = tp / (tp + fn) if tp + fn else float("nan")
    spes = tn / (tn + fp) if tn + fp else float("nan")
    pres = tp / (tp + fp) if tp + fp else float("nan")
    r = {"penapisan": nama, "tp": tp, "fn": fn, "fp": fp, "tn": tn,
         "sensitivitas": round(sens, 4), "spesifisitas": round(spes, 4),
         "presisi": round(pres, 4), "catatan": catatan}
    print("\n== %s ==" % nama)
    print("  TP %d  FN %d  FP %d  TN %d" % (tp, fn, fp, tn))
    print("  sensitivitas %.4f  spesifisitas %.4f  presisi %.4f"
          % (sens, spes, pres))
    if catatan:
        print("  CATATAN: %s" % catatan)
    return r

OUT["hasil"] = []

ml = (s.read.parquet(H + "models/kandidat_reassortant")
       .select("accession").distinct())
OUT["hasil"].append(metrik(
    "ketidaksesuaian subtipe (ML, notebook 05)", ml,
    "SIRKULAR: label disusun dari subtipe, dan penapisan ini juga memakai "
    "subtipe. Angka ini tidak dapat ditafsirkan sebagai kinerja."))

def ada(p):
    try:
        s.read.parquet(H + p).limit(1).count()
        return True
    except Exception:
        return False

kand_graf = None
for n in (30000, 15000, 5000):
    p = "graph2/kandidat_n%d" % n
    if ada(p):
        kand_graf = s.read.parquet(H + p).select("accession").distinct()
        print("\nmemakai kandidat operator graf dari %s" % p)
        break

if kand_graf is not None:
    OUT["hasil"].append(metrik(
        "operator konstelasi graf", kand_graf,
        "Tidak sirkular: operator hanya memakai konstelasi klaster dan "
        "tidak pernah melihat subtipe."))
else:
    print("\nKandidat operator graf belum ada.")
    print("Jalankan langkah24_graf_sadar_galur.py lalu")
    print("langkah2b_operator_pada_graf2.py terlebih dahulu.")
    OUT["operator_graf"] = "belum tersedia"

with open("/tmp/validasi.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("\nditulis /tmp/validasi.json")
s.stop()
