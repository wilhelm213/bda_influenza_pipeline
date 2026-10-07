import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s = (SparkSession.builder.appName("tarik-graf").master("local[3]")
     .config("spark.driver.memory", "3g")
     .config("spark.sql.shuffle.partitions", "24")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

def baca(p):
    try:
        return s.read.parquet(H + p)
    except Exception as e:
        print("  %s tidak terbaca (%s)" % (p, type(e).__name__))
        return None

def rec(df, n=None):
    return [r.asDict() for r in (df.limit(n) if n else df).collect()]

co = baca("graph/co_occurs")
if co is not None:
    OUT["co_semua"] = rec(co.orderBy(F.desc("n_galur")))
    print("tepi co-occurs : %d" % len(OUT["co_semua"]))

lin = baca("graph/lineage")
tepi = baca("graph/tepi")
OUT["sub_klaster"] = None
if lin is not None and tepi is not None:
    uk = (lin.groupBy("lineage_id", "segmen").count()
             .filter((F.col("count") >= 12) & (F.col("count") <= 55))
             .orderBy(F.desc("count")))
    pil = uk.first()
    if pil:
        lid, seg, n = pil["lineage_id"], pil["segmen"], pil["count"]
        ang = [r["id"] for r in
               lin.filter(F.col("lineage_id") == lid).select("id").collect()]
        sub = (tepi.filter((F.col("segmen") == seg)
                           & F.col("src").isin(ang) & F.col("dst").isin(ang))
                   .orderBy(F.desc("kemiripan")).limit(500))
        OUT["sub_klaster"] = {"lineage_id": lid, "segmen": int(seg),
                              "simpul": int(n), "tepi": rec(sub)}
        print("subgraf klaster: %s seg %d, %d simpul, %d tepi"
              % (lid, seg, n, len(OUT["sub_klaster"]["tepi"])))

sen = baca("graph/metrik_sentralitas")
if sen is not None:
    print("skema sentralitas:", [f.name for f in sen.schema.fields])
    kol = [f.name for f in sen.schema.fields]
    urut = "skor" if "skor" in kol else kol[-1]
    OUT["sentralitas"] = rec(sen.orderBy(F.desc(urut)), 30)
    OUT["sentralitas_n"] = sen.count()
    if "derajat" in kol:
        OUT["sentral_derajat"] = rec(
            sen.groupBy("derajat").count().orderBy("derajat"))

gs = baca("graph/geo_sentralitas")
if gs is not None:
    print("skema geo_sentralitas:", [f.name for f in gs.schema.fields])
    kol = [f.name for f in gs.schema.fields]
    urut = next((c for c in ("skor", "pagerank", "derajat") if c in kol),
                kol[-1])
    OUT["geo_sentral"] = rec(gs.orderBy(F.desc(urut)), 25)

gt = baca("graph/geo_tepi")
if gt is not None:
    print("skema geo_tepi:", [f.name for f in gt.schema.fields])
    kol = [f.name for f in gt.schema.fields]
    urut = next((c for c in ("lineage_bersama", "bobot", "n") if c in kol),
                kol[-1])
    OUT["geo_tepi"] = rec(gt.orderBy(F.desc(urut)), 60)
    OUT["geo_tepi_n"] = gt.count()

kb = baca("graph/kandidat_bersilang")
if kb is not None:
    print("skema kandidat_bersilang:", [f.name for f in kb.schema.fields])
    OUT["kandidat_silang_graf"] = rec(kb, 30)
    OUT["kandidat_silang_graf_n"] = kb.count()

with open("/tmp/graf.json", "w") as f:
    json.dump(OUT, f, default=str)
print("\nditulis /tmp/graf.json dengan kunci:", " ".join(sorted(OUT)))
s.stop()
