import json

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

s = (SparkSession.builder.appName("langkah1-stratifikasi").master("local[4]")
     .config("spark.driver.memory", "4g")
     .config("spark.sql.shuffle.partitions", "32")
     .config("spark.ui.enabled", "false").getOrCreate())
s.sparkContext.setLogLevel("ERROR")
H = "hdfs://namenode:8020/bda/"
OUT = {}

skor = (s.read.parquet(H + "features/kmer_k8")
         .select("accession").distinct())
n_skor = skor.count()
print("populasi terskor (punya vektor fitur k=8): %d" % n_skor)

meta = (s.read.parquet(H + "stage/sequences")
         .select("accession", "inang", "negara", "wilayah", "tahun_koleksi",
                 "subtipe"))
pop = skor.join(meta, "accession", "inner")

kand = (s.read.parquet(H + "models/kandidat_reassortant")
         .select("accession").distinct().withColumn("kandidat", F.lit(1)))

BABI = F.lower(F.col("inang")).startswith("sus ")
UNGGAS = F.lower(F.col("inang")).rlike(
    "gallus|anas|anatidae|meleagris|anser|branta|aves|avian|duck|chicken|turkey")

d = (pop.join(kand, "accession", "left")
        .withColumn("kandidat", F.coalesce(F.col("kandidat"), F.lit(0)))
        .withColumn("kelas_inang",
                    F.when(BABI, "babi").when(F.col("inang") == "Homo sapiens",
                                              "manusia")
                     .when(UNGGAS, "unggas").otherwise("lain"))
        .withColumn("dekade",
                    (F.floor(F.col("tahun_koleksi") / 10) * 10).cast("int"))
        .withColumn("wil", F.coalesce(F.col("wilayah"), F.lit("tidak tercatat")))
        .withColumn("sub_grup",
                    F.when(F.col("subtipe").isin(
                        "H1N1", "H3N2", "H1N2", "H5N1", "H9N2", "H7N9"),
                        F.col("subtipe")).otherwise("lain")))
d.cache()
n_pop = d.count()
n_kand = d.filter(F.col("kandidat") == 1).count()
print("populasi dianalisis : %d" % n_pop)
print("kandidat di dalamnya: %d" % n_kand)

OUT["populasi"] = {"terskor": n_skor, "dianalisis": n_pop, "kandidat": n_kand}

kasar = (d.groupBy("kelas_inang")
          .agg(F.count("*").alias("n"), F.sum("kandidat").alias("k"))
          .toPandas())
kasar["pangsa_pop"] = 100 * kasar["n"] / n_pop
kasar["pangsa_kand"] = 100 * kasar["k"] / n_kand
kasar["laju"] = 100 * kasar["k"] / kasar["n"]
laju_global = n_kand / n_pop
kasar["pengayaan"] = (kasar["k"] / kasar["n"]) / laju_global
print("\n== pengayaan mentah (penyebut = populasi terskor) ==")
print(kasar.sort_values("pengayaan", ascending=False).to_string(index=False))
OUT["kasar"] = kasar.to_dict("records")

st = (d.filter(F.col("dekade").isNotNull() & (F.col("dekade") >= 1990))
       .groupBy("wil", "dekade", "kelas_inang")
       .agg(F.count("*").alias("n"), F.sum("kandidat").alias("k"))
       .toPandas())

piv = st.assign(babi=np.where(st.kelas_inang == "babi", "babi", "bukan"))
piv = (piv.groupby(["wil", "dekade", "babi"], as_index=False)[["n", "k"]].sum()
          .pivot(index=["wil", "dekade"], columns="babi",
                 values=["n", "k"]).fillna(0))
piv.columns = ["_".join(c) for c in piv.columns]
piv = piv.reset_index()
for c in ("n_babi", "n_bukan", "k_babi", "k_bukan"):
    if c not in piv:
        piv[c] = 0.0

piv["a"] = piv.k_babi
piv["b"] = piv.n_babi - piv.k_babi
piv["c"] = piv.k_bukan
piv["dd"] = piv.n_bukan - piv.k_bukan
piv["N"] = piv.a + piv.b + piv.c + piv.dd

val = piv[(piv.n_babi > 0) & (piv.n_bukan > 0) & ((piv.a + piv.c) > 0)].copy()
val["or_strata"] = np.where((val.b > 0) & (val.c > 0),
                            (val.a * val.dd) / (val.b * val.c), np.nan)
val["laju_babi"] = 100 * val.a / val.n_babi
val["laju_bukan"] = 100 * val.c / val.n_bukan

num = (val.a * val.dd / val.N).sum()
den = (val.b * val.c / val.N).sum()
or_mh = num / den if den else float("nan")

E = (val.n_babi * (val.a + val.c) / val.N).sum()
Var = ((val.n_babi * val.n_bukan * (val.a + val.c) * (val.b + val.dd))
       / (val.N ** 2 * (val.N - 1))).replace([np.inf, -np.inf], np.nan).sum()
chi = (abs(val.a.sum() - E) - 0.5) ** 2 / Var if Var else float("nan")
from scipy import stats
p_cmh = 1 - stats.chi2.cdf(chi, 1)

P = (val.a + val.dd) / val.N
Q = (val.b + val.c) / val.N
R = val.a * val.dd / val.N
S = val.b * val.c / val.N
se = np.sqrt((P * R).sum() / (2 * R.sum() ** 2)
             + ((P * S).sum() + (Q * R).sum()) / (2 * R.sum() * S.sum())
             + (Q * S).sum() / (2 * S.sum() ** 2))
lo, hi = np.exp(np.log(or_mh) - 1.96 * se), np.exp(np.log(or_mh) + 1.96 * se)

print("\n== Cochran-Mantel-Haenszel, babi vs bukan babi ==")
print("  strata informatif : %d (wilayah x dekade)" % len(val))
print("  OR MH             : %.3f  (95%% CI %.3f - %.3f)" % (or_mh, lo, hi))
print("  chi2 CMH          : %.1f   p = %.3g" % (chi, p_cmh))
OUT["cmh"] = {"strata": int(len(val)), "or": float(or_mh),
              "ci_lo": float(lo), "ci_hi": float(hi),
              "chi2": float(chi), "p": float(p_cmh)}
OUT["per_strata"] = val[["wil", "dekade", "n_babi", "a", "n_bukan", "c",
                         "laju_babi", "laju_bukan", "or_strata"]] \
    .sort_values(["wil", "dekade"]).round(4).to_dict("records")

print("\n== laju kandidat per strata (hanya strata dengan >=30 sekuens babi) ==")
tam = val[val.n_babi >= 30].sort_values("or_strata", ascending=False)
print(tam[["wil", "dekade", "n_babi", "laju_babi", "n_bukan", "laju_bukan",
           "or_strata"]].round(3).to_string(index=False))

sel = (d.filter(F.col("dekade").isNotNull() & (F.col("dekade") >= 1990))
        .groupBy("kelas_inang", "wil", "dekade", "sub_grup")
        .agg(F.count("*").alias("n"), F.sum("kandidat").alias("k"))
        .toPandas())
baris = pd.concat([
    sel.assign(y=1, w=sel.k),
    sel.assign(y=0, w=sel.n - sel.k)], ignore_index=True)
baris = baris[baris.w > 0]
X = pd.get_dummies(
    baris[["kelas_inang", "wil", "sub_grup"]].assign(dekade=baris.dekade.astype(str)),
    drop_first=False).astype(float)

for ref in ("kelas_inang_manusia", "wil_Asia", "sub_grup_lain", "dekade_2020"):
    if ref in X:
        X = X.drop(columns=[ref])
from sklearn.linear_model import LogisticRegression
lr = LogisticRegression(penalty=None, max_iter=4000, solver="lbfgs")
lr.fit(X.values, baris.y.values, sample_weight=baris.w.values)
koef = pd.DataFrame({"peubah": X.columns, "koef": lr.coef_[0]})
koef["OR"] = np.exp(koef.koef)
print("\n== regresi logistik: kandidat ~ inang + wilayah + dekade + subtipe ==")
print("   (rujukan: inang manusia, wilayah Asia, subtipe lain, dekade 2020)")
print(koef[koef.peubah.str.startswith("kelas_inang")]
      .round(4).to_string(index=False))
OUT["logit"] = koef.round(5).to_dict("records")
OUT["logit_babi_or"] = float(
    koef.loc[koef.peubah == "kelas_inang_babi", "OR"].iloc[0])

with open("/tmp/stratifikasi.json", "w") as f:
    json.dump(OUT, f, indent=1, default=str)
print("\nditulis /tmp/stratifikasi.json")
s.stop()
