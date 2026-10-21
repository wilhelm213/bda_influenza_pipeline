# -*- coding: utf-8 -*-
"""Gambar Bab 7 laporan sebagai berkas PNG.

Sebelumnya kelima gambar ini digambar sebagai SVG langsung di halaman,
sehingga tidak dapat disalin-tempel ke pengolah kata. Di sini keduanya
dibangkitkan sebagai PNG dari berkas data yang sama."""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter

BDA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEL = os.path.join(BDA, "laporan", "gambar")
os.makedirs(KEL, exist_ok=True)
DPI = 200

TINTA, TINTA2, TINTA3 = "#10140d", "#3d4738", "#6c7865"
GARIS, GARIS2, KERTAS = "#cdd4c4", "#e0e5d7", "#ffffff"
D1, D2, D3, D4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
D5, D6, D7, D8 = "#e87ba4", "#008300", "#4a3aa7", "#e34948"
AKSEN, AKSEN_BG = "#1d5c3a", "#dfeee5"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "text.color": TINTA, "axes.labelcolor": TINTA,
    "axes.edgecolor": GARIS, "xtick.color": TINTA2, "ytick.color": TINTA2,
    "axes.facecolor": KERTAS, "figure.facecolor": KERTAS,
    "savefig.facecolor": KERTAS, "axes.grid": True,
    "grid.color": GARIS2, "grid.linewidth": .8, "axes.axisbelow": True,
    "legend.frameon": False,
})

SEG = {1: "PB2", 2: "PB1", 3: "PA", 4: "HA", 5: "NP", 6: "NA", 7: "M", 8: "NS"}
SP = (r"C:\Users\WILLYB~1\AppData\Local\Temp\claude\d--BDA"
      r"\c86e8dff-b26f-487f-8cc6-2e17c473a70f\scratchpad")
PKT = os.path.join(BDA, "web", "sumber", "paket_data.json")
D = json.load(io.open(PKT, encoding="utf-8"))
STR = json.load(io.open(os.path.join(BDA, "web", "stratifikasi.json"),
                        encoding="utf-8"))
dibuat = []


def rb(n, d=0):
    s = format(round(n, d), ",." + str(d) + "f")
    return s.replace(",", "\u00ad").replace(".", ",").replace("\u00ad", ".")


def rapi(ax, xl=None, yl=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if xl:
        ax.set_xlabel(xl, fontsize=8.5)
    if yl:
        ax.set_ylabel(yl, fontsize=8.5)


def simpan(fig, nama, ket):
    p = os.path.join(KEL, nama)
    fig.savefig(p, dpi=DPI, bbox_inches="tight", pad_inches=.14)
    plt.close(fig)
    dibuat.append((nama, ket))
    print("  %-30s %6.1f KB  %s" % (nama, os.path.getsize(p) / 1024, ket))


def hbar(nama, ket, label, nilai, warna, vf=None, lebar=7.0):
    n = len(label)
    fig, ax = plt.subplots(figsize=(lebar, .36 * n + .8))
    y = np.arange(n)[::-1]
    ax.barh(y, nilai, height=.62, color=warna)
    ax.set_yticks(y)
    ax.set_yticklabels(label, fontsize=9)
    ax.set_xlim(0, max(nilai) * 1.22)
    ax.grid(axis="y", visible=False)
    for yi, v in zip(y, nilai):
        ax.text(v + max(nilai) * .012, yi, vf(v) if vf else rb(v),
                va="center", fontsize=8.4, color=TINTA2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: rb(v)))
    rapi(ax)
    simpan(fig, nama, ket)


# ── Gambar 12: rantai data ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9.2, 1.5))
ax.set_xlim(0, 920)
ax.set_ylim(120, 0)
ax.axis("off")
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
kotak = [("HDFS zona gold", "Parquet agregat"),
         ("Spark SQL", "agregasi akhir"),
         ("MySQL", "skema bintang, 13 tabel"),
         ("Ekstrak JSON", "agregat 118 KB"),
         ("Dashboard", "HTML mandiri")]
w, celah = 160, 30
x = 0
for i, (judul, ket) in enumerate(kotak):
    ax.add_patch(FancyBboxPatch((x, 86), w, -56,
                                boxstyle="round,pad=0,rounding_size=3",
                                linewidth=1.3, edgecolor=AKSEN,
                                facecolor=AKSEN_BG if i in (0, 4) else KERTAS))
    ax.text(x + w / 2, 52, judul, fontsize=9.5, fontweight="bold",
            ha="center", va="center", color=TINTA)
    ax.text(x + w / 2, 70, ket, fontsize=7.6, ha="center", va="center",
            color=TINTA3, family="DejaVu Sans Mono")
    if i < len(kotak) - 1:
        ax.add_patch(FancyArrowPatch((x + w + 4, 58), (x + w + celah - 4, 58),
                                     arrowstyle="-|>", mutation_scale=11,
                                     linewidth=1.4, color=AKSEN))
    x += w + celah
ax.text(460, 110, "satu sumber angka, tidak dihitung ulang di peramban",
        fontsize=7.8, ha="center", color=TINTA3, family="DejaVu Sans Mono")
simpan(fig, "12-rantai-data.png",
       "Rantai data dari zona gold sampai dashboard")

# ── Gambar 13: pengulangan untai ─────────────────────────────────────
NAMA_D = {"1 (tunggal)": "1 (tunggal)", "2 - 5": "2 sampai 5",
          "6 - 20": "6 sampai 20", "21 - 100": "21 sampai 100",
          "> 100": "di atas 100"}
urut_d = ["1 (tunggal)", "2 - 5", "6 - 20", "21 - 100", "> 100"]
pet = {d["ember"]: d["count"] for d in D["dup"]}
hbar("13-pengulangan-untai.png",
     "Berapa kali satu untai basa yang identik berulang di arsip",
     [NAMA_D[e] for e in urut_d], [pet[e] for e in urut_d], D4)

# ── Gambar 14: sekuens menurut wilayah ───────────────────────────────
wil = [w for w in D["wilayah"] if w["wilayah"]]
hbar("14-sekuens-per-wilayah.png",
     "Jumlah sekuens menurut wilayah",
     [w["wilayah"] for w in wil], [w["count"] for w in wil], AKSEN)

# ── Gambar 15: tepi per simpul ───────────────────────────────────────
kl = {k["segmen"]: k["simpul"] for k in D["klaster_seg"]}
rows = sorted(((g["segmen"], g["tepi"] / kl[g["segmen"]])
               for g in D["graf_seg"]), key=lambda r: -r[1])
hbar("15-tepi-per-simpul.png",
     "Tepi kemiripan per simpul pada tiap segmen",
     ["%d %s" % (s, SEG[s]) for s, _ in rows], [v for _, v in rows], D7,
     vf=lambda v: rb(v, 1))

# ── Gambar 16: pengayaan inang ───────────────────────────────────────
NAMA_I = {"babi": "Babi (Sus)", "unggas": "Unggas", "manusia": "Manusia"}
ks = [k for k in STR["kasar"] if k["kelas_inang"] in NAMA_I]
ks.sort(key=lambda k: -k["pengayaan"])
fig, ax = plt.subplots(figsize=(7.0, 3.3))
xs = np.arange(len(ks))
ax.bar(xs - .19, [k["pangsa_pop"] for k in ks], width=.36, color=D1,
       label="Pangsa populasi terskor")
ax.bar(xs + .19, [k["pangsa_kand"] for k in ks], width=.36, color=D8,
       label="Pangsa kandidat")
for i, k in enumerate(ks):
    ax.text(i, max(k["pangsa_pop"], k["pangsa_kand"]) + 2.6,
            rb(k["pengayaan"], 2) + "\u00d7", ha="center", fontsize=9,
            fontweight="bold", color=TINTA)
ax.set_xticks(xs)
ax.set_xticklabels([NAMA_I[k["kelas_inang"]] for k in ks], fontsize=9.5)
ax.set_ylim(0, 72)
ax.grid(axis="x", visible=False)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: "%d%%" % v))
ax.legend(fontsize=8.4, loc="upper center", ncol=2, bbox_to_anchor=(.5, 1.02))
rapi(ax, None, "Pangsa")
simpan(fig, "16-pengayaan-inang.png",
       "Pangsa tiap kelas inang pada populasi terskor dan di antara kandidat")

print("\n%d gambar Bab 7 ditulis ke %s" % (len(dibuat), KEL))
