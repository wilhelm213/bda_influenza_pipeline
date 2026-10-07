import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s = (SparkSession.builder.appName("babi").master("local[4]")
     .config("spark.driver.memory", "3g")
     .config("spark.sql.shuffle.partitions", "24")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"

BABI = F.lower(F.col("inang")).startswith("sus ")
UNGGAS = F.lower(F.col("inang")).rlike(
    "gallus|anas|anatidae|meleagris|anser|branta|aves|avian|duck|chicken|turkey")

arsip = s.read.parquet(H + "stage/sequences").select("inang", "subtipe", "segmen")
arsip.cache()
n_arsip = arsip.count()
kd = s.read.parquet(H + "models/kandidat_reassortant").select(
    "inang", "subtipe_kelas", "prediksi_subtipe", "keyakinan", "galur")
kd.cache()
n_kd = kd.count()

out = {
    "arsip_total": n_arsip,
    "arsip_babi": arsip.filter(BABI).count(),
    "arsip_unggas": arsip.filter(UNGGAS).count(),
    "arsip_manusia": arsip.filter(F.col("inang") == "Homo sapiens").count(),
    "kd_total": n_kd,
    "kd_babi": kd.filter(BABI).count(),
    "kd_unggas": kd.filter(UNGGAS).count(),
    "kd_manusia": kd.filter(F.col("inang") == "Homo sapiens").count(),
    "kd_galur_babi": kd.filter(BABI).select("galur").distinct().count(),
}
for nama in ("babi", "unggas", "manusia"):
    pa = out["arsip_" + nama] / n_arsip
    pk = out["kd_" + nama] / n_kd
    out["pangsa_arsip_" + nama] = round(pa * 100, 2)
    out["pangsa_kd_" + nama] = round(pk * 100, 2)
    out["pengayaan_" + nama] = round(pk / pa, 2) if pa else None

print(json.dumps(out, indent=1))
with open("/tmp/babi.json", "w") as f:
    json.dump(out, f, indent=1)
s.stop()
