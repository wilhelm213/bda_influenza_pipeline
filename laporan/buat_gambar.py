# -*- coding: utf-8 -*-
import csv
import glob
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BDA = r"D:\BDA"
KEL = os.path.join(BDA, "laporan", "gambar")
SP = (r"C:\Users\WILLYB~1\AppData\Local\Temp\claude\d--BDA"
      r"\c86e8dff-b26f-487f-8cc6-2e17c473a70f\scratchpad")
os.makedirs(KEL, exist_ok=True)

TINTA = "#10140d"
TINTA2 = "#3d4738"
GARIS = "#cdd4c4"
GARIS2 = "#e0e5d7"
KERTAS = "#ffffff"
D1, D2, D3, D4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
D5, D6, D7, D8 = "#e87ba4", "#008300", "#4a3aa7", "#e34948"
AKSEN = "#1d5c3a"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "text.color": TINTA,
    "axes.labelcolor": TINTA,
    "axes.edgecolor": GARIS,
    "xtick.color": TINTA2,
    "ytick.color": TINTA2,
    "axes.facecolor": KERTAS,
    "figure.facecolor": KERTAS,
    "savefig.facecolor": KERTAS,
    "axes.grid": True,
    "grid.color": GARIS2,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})

SEG = {1: "PB2", 2: "PB1", 3: "PA", 4: "HA", 5: "NP", 6: "NA", 7: "M", 8: "NS"}


def rb(n, d=0):
    s = ("%,." + str(d) + "f") % n if False else format(round(n, d), ",." + str(d) + "f")
    return s.replace(",", "\u00ad").replace(".", ",").replace("\u00ad", ".")


def js(p):
    return json.load(io.open(p, encoding="utf-8"))


def csvread(p):
    with io.open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


INS = js(os.path.join(SP, "insight.json"))
MODEL = csvread(os.path.join(BDA, "models", "metrik_model.csv"))
SKALA = csvread(os.path.join(BDA, "models", "metrik_skalabilitas.csv"))
KD_WIL = INS["kandidat_per_wilayah"]
KD_INANG = [r for r in INS["kandidat_per_inang"] if r["inang"]]

_th = {}
for _f in glob.glob(os.path.join(BDA, "audit", "*.jsonl")):
    for _ln in io.open(_f, encoding="utf-8").read().strip().splitlines():
        try:
            _d = json.loads(_ln)
        except ValueError:
            continue
        if _d.get("status", "").startswith("OK") and _d.get("detik"):
            _th[(_d.get("lapisan", "?"), _d.get("tahap", "?"))] = max(
                _th.get((_d.get("lapisan", "?"), _d.get("tahap", "?")), 0),
                float(_d["detik"]))

dibuat = []


def simpan(fig, nama, judul):
    p = os.path.join(KEL, nama)
    fig.savefig(p, dpi=200, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    kb = os.path.getsize(p) / 1024
    dibuat.append((nama, judul, kb))
    print("  %-34s %6.1f KB  %s" % (nama, kb, judul))


def rapikan(ax, xlab=None, ylab=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GARIS)
    if xlab:
        ax.set_xlabel(xlab, color=TINTA2, fontsize=8.5)
    if ylab:
        ax.set_ylabel(ylab, color=TINTA2, fontsize=8.5)


def hbar(nama, judul, labels, nilai, warna, lebar=7.4, satuan=""):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(lebar, 0.34 * n + 0.9))
    y = np.arange(n)[::-1]
    ax.barh(y, nilai, height=0.62, color=warna)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, max(nilai) * 1.24)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, p: rb(v)))
    ax.grid(axis="y", visible=False)
    for yi, v in zip(y, nilai):
        ax.text(v + max(nilai) * 0.012, yi, rb(v) + satuan, va="center",
                fontsize=8.5, color=TINTA)
    rapikan(ax)
    simpan(fig, nama, judul)


def garis(nama, judul, x, seri, xlab, ylab, lebar=7.4, tinggi=3.3,
          tandai_gagal=None):
    fig, ax = plt.subplots(figsize=(lebar, tinggi))
    warna = [D1, D2, D3, D4]
    for i, (nm, v) in enumerate(seri):
        vv = [np.nan if (t is None or t == "") else float(t) for t in v]
        ax.plot(range(len(x)), vv, marker="o", markersize=4.5, linewidth=2,
                color=warna[i % len(warna)], label=nm, zorder=3)
    if tandai_gagal:
        semua = [float(t2) for _, v in seri for t2 in v if t2 not in (None, "")]
        tinggi_y = max(semua) * 0.055 if semua else 1
        for i in tandai_gagal:
            ax.plot(i, tinggi_y, marker="x", markersize=10,
                    markeredgewidth=2.4, color=D2, zorder=5, clip_on=False)
            ax.annotate("gagal", (i, tinggi_y), textcoords="offset points",
                        xytext=(0, 12), ha="center", fontsize=8.2,
                        color=D2, annotation_clip=False)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x, fontsize=8.5)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, p: rb(v)))
    ax.set_ylim(bottom=0)
    ax.margins(x=0.04)
    rapikan(ax, xlab, ylab)
    lg = ax.legend(frameon=False, fontsize=8.8, loc="best")
    for t in lg.get_texts():
        t.set_color(TINTA)
    simpan(fig, nama, judul)


def grup(nama, judul, kat, seri, ylab, lebar=7.4, tinggi=3.4, fmt=None):
    fig, ax = plt.subplots(figsize=(lebar, tinggi))
    warna = [D1, D2, D3, D4]
    n = len(seri)
    w = 0.78 / n
    x = np.arange(len(kat))
    for i, (nm, v) in enumerate(seri):
        ax.bar(x + (i - (n - 1) / 2) * w, v, width=w * 0.92,
               color=warna[i % len(warna)], label=nm)
    ax.set_xticks(x)
    ax.set_xticklabels(kat, fontsize=9)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(fmt or (lambda v, p: rb(v, 2))))
    ax.grid(axis="x", visible=False)
    rapikan(ax, None, ylab)
    lg = ax.legend(frameon=False, fontsize=8.8)
    for t in lg.get_texts():
        t.set_color(TINTA)
    simpan(fig, nama, judul)


print("Membuat gambar laporan Assignment II\n")

# 1 pertumbuhan rilis
r = [(x["tahun_rilis"], x["count"]) for x in INS["per_tahun_rilis"]
     if x["tahun_rilis"] and x["tahun_rilis"] >= 1990]
fig, ax = plt.subplots(figsize=(7.4, 3.2))
ax.fill_between([a for a, b in r], [b for a, b in r], color=AKSEN, alpha=0.13)
ax.plot([a for a, b in r], [b for a, b in r], color=AKSEN, linewidth=2.2)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: rb(v)))
ax.set_ylim(bottom=0)
rapikan(ax, "Tahun rilis", "Sekuens")
simpan(fig, "01-pertumbuhan-rilis.png",
       "Sekuens dirilis NCBI per tahun")

# 2 jeda pelaporan
jt = [(x["tahun_koleksi"], float(x["rata"])) for x in INS["jeda_per_tahun"]
      if 1995 <= x["tahun_koleksi"] <= 2025]
fig, ax = plt.subplots(figsize=(7.4, 3.2))
ax.plot([a for a, b in jt], [b for a, b in jt], color=AKSEN, linewidth=2.2,
        marker="o", markersize=3.5)
ax.yaxis.set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda v, p: rb(v, 1)))
ax.set_ylim(bottom=0)
rapikan(ax, "Tahun koleksi", "Jeda rata-rata (tahun)")
simpan(fig, "02-jeda-pelaporan.png",
       "Jeda koleksi ke rilis menurut tahun koleksi")

# 3 subtipe
s12 = INS["per_subtipe"][:12]
hbar("03-subtipe-teratas.png", "Dua belas subtipe teratas",
     [x["subtipe"] for x in s12], [x["count"] for x in s12], D3)

# 4 inang
i10 = [x for x in INS["per_inang"] if x["inang"]][:10]
hbar("04-inang-teratas.png", "Sepuluh spesies inang teratas",
     [x["inang"] for x in i10], [x["count"] for x in i10], D2)

# 5 tepi per segmen
gs = INS["graf_per_segmen"]
hbar("05-tepi-per-segmen.png", "Tepi kemiripan per segmen",
     ["%d %s" % (x["segmen"], SEG[x["segmen"]]) for x in gs],
     [x["tepi"] for x in gs], AKSEN)

# 6-7 skalabilitas
sp = [r for r in SKALA if r["jalur"] == "Spark MLlib"]
sk = [r for r in SKALA if r["jalur"] != "Spark MLlib"]
kat = [rb(float(r["fraksi"]) * 100) + "%" for r in sp]
garis("06-skalabilitas-waktu.png",
      "Waktu pelatihan terhadap fraksi data",
      kat, [("Spark MLlib", [r["detik"] for r in sp]),
            ("scikit-learn 1 node", [r["detik"] for r in sk])],
      "Fraksi data latih", "Detik", tandai_gagal=[2, 3, 4])
garis("07-skalabilitas-throughput.png",
      "Throughput pelatihan dalam baris per detik",
      kat, [("Spark MLlib", [r["throughput_baris_per_detik"] for r in sp]),
            ("scikit-learn 1 node", [r["throughput_baris_per_detik"] for r in sk])],
      "Fraksi data latih", "Baris per detik")

# 8-9 model
tugas = []
for r in MODEL:
    if r["tugas"] not in tugas:
        tugas.append(r["tugas"])
alg = []
for r in MODEL:
    if r["algoritma"] not in alg:
        alg.append(r["algoritma"])


def ambil(t, a, kol):
    for r in MODEL:
        if r["tugas"] == t and r["algoritma"] == a:
            return float(r[kol])
    return np.nan


grup("08-f1-per-algoritma.png", "F1 makro per tugas dan algoritma",
     [t.split(":")[0] for t in tugas],
     [(a, [ambil(t, a, "f1_makro") for t in tugas]) for a in alg],
     "F1 makro")
grup("09-waktu-latih.png", "Waktu pelatihan per tugas dan algoritma",
     [t.split(":")[0] for t in tugas],
     [(a, [ambil(t, a, "detik_latih") / 60 for t in tugas]) for a in alg],
     "Menit", fmt=lambda v, p: rb(v, 0))

# 10-11 kandidat
kw = [x for x in KD_WIL if x["wilayah"]]
hbar("10-kandidat-per-wilayah.png", "Kandidat reassortment menurut wilayah",
     [x["wilayah"] for x in kw], [x["count"] for x in kw], D2, lebar=6.6)
ki = KD_INANG[:8]
hbar("11-kandidat-per-inang.png", "Delapan inang teratas di antara kandidat",
     [x["inang"] for x in ki], [x["count"] for x in ki], D4, lebar=6.6)

print("\n%d gambar ditulis ke %s" % (len(dibuat), KEL))
io.open(os.path.join(KEL, "DAFTAR-GAMBAR.txt"), "w",
        encoding="utf-8").write(
    "Daftar gambar laporan Assignment II\n"
    + "=" * 50 + "\n\n"
    + "\n".join("%-34s %s" % (n, j) for n, j, _ in dibuat) + "\n")
print("daftar ditulis ke DAFTAR-GAMBAR.txt")
