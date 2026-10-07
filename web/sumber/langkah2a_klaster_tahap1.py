from functools import reduce

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

N = 5000
s = (SparkSession.builder.appName("langkah2a-klaster").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "64")
     .config("spark.cleaner.referenceTracking.cleanCheckpoints", "true")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
s.sparkContext.setCheckpointDir(
    "hdfs://namenode:8020/bda/graph2/_ckpt_klaster")
H = "hdfs://namenode:8020/bda/"

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
        print("      iterasi %d: %d simpul berubah" % (i + 1, ubah))
        if ubah == 0:
            break
    return lab

tepi = s.read.parquet(H + "graph2/tepi_n%d" % N)
print("tepi dimuat: %d" % tepi.count())
klas = []
for seg in range(1, 9):
    t = tepi.filter(F.col("segmen") == seg).select("src", "dst")
    if t.limit(1).count() == 0:
        print("  segmen %d: tanpa tepi, dilewati" % seg)
        continue
    print("  segmen %d:" % seg)
    k = komponen(t).withColumn("segmen", F.lit(seg))
    n_s = k.count()
    n_k = k.select("komp").distinct().count()
    print("    %d simpul -> %d klaster" % (n_s, n_k))
    klas.append(k)

lin = (reduce(lambda a, b: a.union(b), klas)
       .withColumn("lineage_id",
                   F.concat_ws("_", F.lit("S"), F.col("segmen"), F.col("komp")))
       .withColumnRenamed("id", "id"))
lin.write.mode("overwrite").parquet(H + "graph2/lineage_n%d" % N)
print("ditulis graph2/lineage_n%d : %d baris, %d klaster"
      % (N, lin.count(), lin.select("lineage_id").distinct().count()))
s.stop()
