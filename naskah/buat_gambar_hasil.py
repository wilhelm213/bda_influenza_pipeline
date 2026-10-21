# -*- coding: utf-8 -*-
"""Gambar hasil untuk naskah artikel, dibangkitkan dari keluaran pipeline.

Palet delapan warna yang dipakai sudah lolos uji simulasi buta warna
(deuteranopia, protanopia, tritanopia) pada proyek ini, sehingga setiap seri
tetap terbedakan ketika gambar dicetak atau dibaca penyandang CVD."""
import csv
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

AKAR = Path(__file__).resolve().parent.parent
KELUARAN = Path(__file__).resolve().parent
DPI = 300

D1, D2, D3 = "#2a78d6", "#eb6834", "#1baf7a"
D4, D5, D6 = "#eda100", "#e87ba4", "#008300"
D7, D8 = "#4a3aa7", "#e34948"
TINTA, TINTA_2, TINTA_3 = "#10140d", "#3d4738", "#6c7865"
GARIS, GARIS_2, PUTIH = "#cdd4c4", "#e8ece2", "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "text.color": TINTA, "axes.labelcolor": TINTA_2,
    "axes.edgecolor": GARIS, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.facecolor": PUTIH, "figure.facecolor": PUTIH,
    "savefig.facecolor": PUTIH, "axes.grid": True,
    "grid.color": GARIS_2, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False,
})

SEG = {1: "PB2", 2: "PB1", 3: "PA", 4: "HA", 5: "NP", 6: "NA", 7: "M", 8: "NS"}
dibuat = []


def js(p):
    return json.load(io.open(p, encoding="utf-8"))


def csvread(p):
    with io.open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


INS = js(AKAR / "web" / "sumber" / "insight.json")
MODEL = csvread(AKAR / "models" / "metrik_model.csv")
SKALA = csvread(AKAR / "models" / "metrik_skalabilitas.csv")
STRAT = js(AKAR / "web" / "stratifikasi.json")


def rapi(ax, xl=None, yl=None, jdl=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if xl:
        ax.set_xlabel(xl, fontsize=8.5)
    if yl:
        ax.set_ylabel(yl, fontsize=8.5)
    if jdl:
        ax.set_title(jdl, fontsize=9.5, color=TINTA, fontweight="bold",
                     pad=8, loc="left")


def ribu(v, p=None):
    return format(int(round(v)), ",")


def simpan(fig, nama, ket):
    p = KELUARAN / nama
    fig.savefig(p, dpi=DPI, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    dibuat.append((nama, ket))
    print("  %-30s %7.1f KB  %s" % (nama, p.stat().st_size / 1024, ket))


# ── Gambar 2: karakteristik arsip ────────────────────────────────────
fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.2))

r = [(x["tahun_rilis"], x["count"]) for x in INS["per_tahun_rilis"]
     if x["tahun_rilis"] and x["tahun_rilis"] >= 1995]
ax[0].fill_between([a for a, _ in r], [b for _, b in r], color=D1, alpha=.16)
ax[0].plot([a for a, _ in r], [b for _, b in r], color=D1, linewidth=2.2)
ax[0].yaxis.set_major_formatter(FuncFormatter(ribu))
ax[0].set_ylim(bottom=0)
rapi(ax[0], "Release year", "Sequences", "(a) Archive growth")

j = [(x["tahun_koleksi"], float(x["rata"])) for x in INS["jeda_per_tahun"]
     if 1995 <= x["tahun_koleksi"] <= 2025]
ax[1].plot([a for a, _ in j], [b for _, b in j], color=D2, linewidth=2.2,
           marker="o", markersize=3.2)
ax[1].annotate("0.40 years", xy=(2025, j[-1][1]), xytext=(2017, 3.2),
               fontsize=8, color=D2, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=D2, lw=1.1))
ax[1].set_ylim(bottom=0)
rapi(ax[1], "Collection year", "Mean lag (years)",
     "(b) Collection-to-release lag")
fig.tight_layout()
simpan(fig, "gambar2-arsip.png",
       "Archive growth and shrinking reporting lag")

# ── Gambar 3: kinerja klasifikasi ────────────────────────────────────
tugas, algo = [], []
for x in MODEL:
    if x["tugas"] not in tugas:
        tugas.append(x["tugas"])
    if x["algoritma"] not in algo:
        algo.append(x["algoritma"])
NAMA_T = {t: t.split(":")[0] for t in tugas}
WARNA_A = {algo[0]: D1, algo[1]: D2, algo[2]: D3}


def ambil(t, a, k):
    for x in MODEL:
        if x["tugas"] == t and x["algoritma"] == a:
            return float(x[k])
    return np.nan


fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.4))
w = 0.78 / len(algo)
xs = np.arange(len(tugas))
for i, a in enumerate(algo):
    ax[0].bar(xs + (i - 1) * w, [ambil(t, a, "f1_makro") for t in tugas],
              width=w * .9, color=WARNA_A[a], label=a)
for i, a in enumerate(algo):
    for k, t in enumerate(tugas):
        v = ambil(t, a, "f1_makro")
        ax[0].text(k + (i - 1) * w, v + .02, "%.4f" % v,
                   ha="center", fontsize=6.2, color=TINTA_2, rotation=90)
ax[0].set_xticks(xs)
ax[0].set_xticklabels([NAMA_T[t] for t in tugas])
ax[0].set_ylim(0, 1.16)
ax[0].grid(axis="x", visible=False)
ax[0].legend(fontsize=7.6, ncol=1, loc="lower left")
rapi(ax[0], None, "Macro F1", "(a) Macro F1 by task and algorithm")

for i, a in enumerate(algo):
    ax[1].bar(xs + (i - 1) * w, [ambil(t, a, "log_loss") for t in tugas],
              width=w * .9, color=WARNA_A[a], label=a)
for k, t in enumerate(tugas):
    acak = ambil(t, algo[0], "log_loss_acak")
    ax[1].plot([k - .45, k + .45], [acak, acak], color=D8, linewidth=1.6,
               linestyle=(0, (4, 2)), zorder=5)
ax[1].text(-0.42, 2.45, "random guess", fontsize=7.4, color=D8,
           fontweight="bold", ha="left", va="bottom")
ax[1].annotate("Naive Bayes B2\nexceeds random", xy=(2 + w, 3.3654),
               xytext=(1.08, 7.4), fontsize=7.4, color=D8,
               fontweight="bold", ha="center",
               arrowprops=dict(arrowstyle="->", color=D8, lw=1.1,
                               connectionstyle="arc3,rad=-0.18"))
ax[1].set_xticks(xs)
ax[1].set_xticklabels([NAMA_T[t] for t in tugas])
ax[1].set_ylim(0.0008, 14)
ax[1].set_yscale("log")
ax[1].grid(axis="x", visible=False)
rapi(ax[1], None, "Log loss (log scale)", "(b) Log loss against random guessing")
fig.tight_layout()
simpan(fig, "gambar3-klasifikasi.png",
       "Macro F1 and log loss of nine models")

# ── Gambar 4: penskalaan ─────────────────────────────────────────────
sp = [x for x in SKALA if x["jalur"].startswith("Spark")]
sk = [x for x in SKALA if not x["jalur"].startswith("Spark")]
baris = [int(float(x["n_latih"])) for x in sp]
sk_b = [int(float(x["n_latih"])) for x in sk if x["n_latih"]]
gagal = [baris[i] for i, x in enumerate(sk) if not x["detik"]]

fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.3))
ax[0].plot(baris, [float(x["detik"]) for x in sp], marker="o", color=D1,
           linewidth=2.2, label="Spark ML")
ax[0].plot(sk_b, [float(x["detik"]) for x in sk if x["detik"]], marker="o",
           color=D2, linewidth=2.2, label="Single node")
for g in gagal:
    ax[0].plot(g, 18, marker="X", markersize=9, color=D8, zorder=6,
               clip_on=False)
ax[0].annotate("failed: Py4JJavaError", xy=(gagal[0], 18),
               xytext=(gagal[0] * .62, 300), fontsize=7.8, color=D8,
               fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=D8, lw=1.1))
ax[0].set_xscale("log")
ax[0].set_ylim(bottom=0)
ax[0].legend(fontsize=8)
rapi(ax[0], "Training rows", "Training time (s)", "(a) Time against volume")

ax[1].plot(baris, [float(x["throughput_baris_per_detik"]) for x in sp],
           marker="o", color=D1, linewidth=2.2, label="Spark ML")
ax[1].plot(sk_b, [float(x["throughput_baris_per_detik"]) for x in sk
                  if x["throughput_baris_per_detik"]], marker="o", color=D2,
           linewidth=2.2, label="Single node")
ax[1].annotate("15× increase", xy=(baris[-1], 1439), xytext=(60000, 1180),
               fontsize=8, color=D1, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=D1, lw=1.1))
ax[1].annotate("decreasing", xy=(sk_b[-1], 169), xytext=(60000, 330),
               fontsize=8, color=D2, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=D2, lw=1.1))
ax[1].set_xscale("log")
ax[1].set_ylim(bottom=0)
ax[1].yaxis.set_major_formatter(FuncFormatter(ribu))
rapi(ax[1], "Training rows", "Rows per second", "(b) Throughput")
fig.tight_layout()
simpan(fig, "gambar4-penskalaan.png",
       "Training time and throughput against data volume")

# ── Gambar 5: struktur graf ──────────────────────────────────────────
gs = sorted(INS["graf_per_segmen"], key=lambda x: x["segmen"])
kl = {k["segmen"]: k for k in INS["klaster_per_segmen"]}
PAL = [D1, D2, D3, D8, D5, D4, D6, D7]

fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.3))
lab = ["%d\n%s" % (x["segmen"], SEG[x["segmen"]]) for x in gs]
nilai = [x["tepi"] for x in gs]
bar = ax[0].bar(range(8), nilai, color=[PAL[i] for i in range(8)], width=.68)
bar[3].set_edgecolor(TINTA)
bar[3].set_linewidth(1.6)
for i, v in enumerate(nilai):
    ax[0].text(i, v + 2200, ribu(v), ha="center", fontsize=7, color=TINTA_2)
ax[0].set_xticks(range(8))
ax[0].set_xticklabels(lab, fontsize=8)
ax[0].set_ylim(0, max(nilai) * 1.2)
ax[0].yaxis.set_major_formatter(FuncFormatter(ribu))
ax[0].grid(axis="x", visible=False)
ax[0].annotate("HA sparsest:\nprimary antibody target", xy=(3, 21800),
               xytext=(3.05, 40000), fontsize=7.4, color=TINTA,
               fontweight="bold", ha="center",
               arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.1))
rapi(ax[0], None, "Similarity edges", "(a) Graph density by segment")

uk = INS["klaster_ukuran"]
urut = ["2 - 5", "6 - 20", "21 - 100", "> 100"]
pet = {u["ember"]: u["count"] for u in uk}
nilai2 = [pet.get(u, 0) for u in urut]
nama2 = ["2–5", "6–20", "21–100", "> 100"]
ax[1].bar(range(4), nilai2, color=[D3, D4, D2, D8], width=.6)
for i, v in enumerate(nilai2):
    ax[1].text(i, v + 18, ribu(v), ha="center", fontsize=7.6, color=TINTA_2)
ax[1].set_xticks(range(4))
ax[1].set_xticklabels(nama2, fontsize=8)
ax[1].set_ylim(0, max(nilai2) * 1.18)
ax[1].grid(axis="x", visible=False)
rapi(ax[1], "Nodes per cluster", "Number of clusters",
     "(b) Cluster size distribution")
fig.tight_layout()
simpan(fig, "gambar5-graf.png",
       "Graph density by segment and cluster size distribution")

# ── Gambar 6: pengayaan inang dan forest plot ────────────────────────
NAMA_I = {"babi": "Swine", "unggas": "Avian", "manusia": "Human",
          "lain": "Other"}
ks = [x for x in STRAT["kasar"] if x["kelas_inang"] in NAMA_I]
ks.sort(key=lambda x: -x["pengayaan"])

fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.5))
xs = np.arange(len(ks))
ax[0].bar(xs - .19, [x["pangsa_pop"] for x in ks], width=.36, color=D1,
          label="Share of scored population")
ax[0].bar(xs + .19, [x["pangsa_kand"] for x in ks], width=.36, color=D8,
          label="Share of candidates")
for i, x in enumerate(ks):
    ax[0].text(i, max(x["pangsa_pop"], x["pangsa_kand"]) + 3.4,
               "%.2f×" % x["pengayaan"],
               ha="center", fontsize=8.4, color=TINTA, fontweight="bold")
ax[0].set_xticks(xs)
ax[0].set_xticklabels([NAMA_I[x["kelas_inang"]] for x in ks], fontsize=8.6)
ax[0].set_ylim(0, 76)
ax[0].yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%d%%" % v))
ax[0].grid(axis="x", visible=False)
ax[0].legend(fontsize=7.8, loc="upper center", ncol=2,
             bbox_to_anchor=(.5, 1.02))
rapi(ax[0], None, "Share", "(a) Candidate enrichment by host")

st = [s for s in STRAT["per_strata"] if s["or_strata"] and
      0 < float(s["or_strata"]) < 400]
st.sort(key=lambda s: float(s["or_strata"]))
y = np.arange(len(st))
ax[1].scatter([float(s["or_strata"]) for s in st], y, s=26, color=D7,
              zorder=4)
cmh = STRAT["cmh"]
ax[1].axvline(cmh["or"], color=D8, linewidth=1.8, zorder=3)
ax[1].axvspan(cmh["ci_lo"], cmh["ci_hi"], color=D8, alpha=.13, zorder=2)
ax[1].axvline(1, color=TINTA_3, linewidth=1.1, linestyle=(0, (4, 3)),
              zorder=3)
ax[1].set_yticks(y)
ax[1].set_yticklabels(["%s %s" % (s["wil"], int(s["dekade"])) for s in st],
                      fontsize=6.8)
ax[1].set_xscale("log")
ax[1].set_xlim(.4, 400)
ax[1].grid(axis="y", visible=False)
ax[1].text(.02, .97, "Pooled Mantel–Haenszel OR\n10.86  (95% CI 9.69–12.17)",
           transform=ax[1].transAxes, fontsize=7.4, color=D8,
           fontweight="bold", va="top", ha="left",
           bbox=dict(boxstyle="round,pad=0.3", facecolor=PUTIH,
                     edgecolor="none", alpha=.92))
ax[1].text(1.08, .2, "OR = 1", fontsize=7, color=TINTA_3, ha="left")
rapi(ax[1], "Odds ratio per stratum (log scale)", None,
     "(b) Confounder control, %d of %d strata"
     % (len(st), cmh["strata"]))
fig.tight_layout()
simpan(fig, "gambar6-pengayaan.png",
       "Host enrichment and per-stratum odds ratios")

io.open(KELUARAN / "DAFTAR-GAMBAR.txt", "w", encoding="utf-8").write(
    "Figures for the manuscript\n" + "=" * 52 + "\n\n"
    + "Figure 1  gambar1-metodologi.png   Eight-stage methodology flow\n"
    + "".join("Figure %d  %-26s %s\n" % (i + 2, n, k)
             for i, (n, k) in enumerate(dibuat)))
print("\n%d result figures written to %s" % (len(dibuat), KELUARAN))
