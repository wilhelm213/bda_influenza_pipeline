# -*- coding: utf-8 -*-
"""Diagram metodologi untuk naskah artikel: alur penuh dari penarikan arsip
sampai validasi statistik, beserta angka yang benar-benar terukur tiap tahap.

Lebar tiap baris teks diperiksa terhadap lebar kotaknya sebelum digambar,
sehingga tidak ada tulisan yang melimpah keluar."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

KELUARAN = Path(__file__).parent
DPI = 300

AKSEN = "#1d5c3a"
AKSEN_BG = "#dfeee5"

# satu rona per jenis operasi; palet sudah lolos uji simulasi buta warna
BIRU, BIRU_BG = "#2a78d6", "#e3edfb"       # akuisisi dan penyimpanan
JINGGA, JINGGA_BG = "#eb6834", "#fdeae2"   # kendali mutu
UNGU, UNGU_BG = "#4a3aa7", "#e8e6f6"       # representasi fitur
HIJAU, HIJAU_BG = "#1baf7a", "#e0f5ee"     # pemodelan
AMBER, AMBER_BG = "#c98500", "#fcf0d9"     # analitik graf
MERAH, MERAH_BG = "#d6342f", "#fce4e3"     # penapisan
TOSCA, TOSCA_BG = "#0f7b8a", "#def0f3"     # validasi statistik
TANAH = "#f1f4ec"
PUTIH = "#ffffff"
TINTA = "#10140d"
TINTA_2 = "#3d4738"
TINTA_3 = "#6c7865"
GARIS = "#cdd4c4"
GARIS_2 = "#e0e5d7"

F = "DejaVu Sans"
FM = "DejaVu Sans Mono"

# lebar rata-rata satu karakter, dalam satuan kanvas, per ukuran huruf
LEBAR_MONO = 0.74      # DejaVu Sans Mono
LEBAR_SANS = 0.62      # DejaVu Sans, perkiraan aman

L, R = 160, 944
TENGAH = (L + R) / 2
PITA_X, PITA_W = 20, 120


def lebar(s, uk, font=FM, tebal="normal"):
    f = LEBAR_MONO if font == FM else LEBAR_SANS
    if tebal == "bold":
        f *= 1.09
    return len(s) * uk * f


def kanvas(w, h):
    fig, ax = plt.subplots(figsize=(w / 100, h / 100))
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax


def kotak(ax, x, y, w, h, isi=PUTIH, tepi=GARIS, tebal=1.0, putus=None, r=3):
    ax.add_patch(FancyBboxPatch(
        (x, y + h), w, -h,
        boxstyle="round,pad=0,rounding_size=%d" % r,
        linewidth=tebal, edgecolor=tepi, facecolor=isi,
        linestyle=(0, putus) if putus else "solid", zorder=2))


def teks(ax, x, y, s, uk=11.5, warna=TINTA, tebal="normal", font=F,
         rata="left", muat=None):
    if muat is not None:
        w = lebar(s, uk, font, tebal)
        if w > muat:
            raise SystemExit("teks melimpah (%.0f > %.0f): %r" % (w, muat, s))
    ax.text(x, y, s, fontsize=uk, color=warna, fontweight=tebal,
            fontfamily=font, ha=rata, va="baseline", zorder=4)


def panah(ax, x1, y1, x2, y2, warna=TINTA_3, tebal=1.4):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
        linewidth=tebal, color=warna, shrinkA=0, shrinkB=0, zorder=3))


def tahap(ax, ax_no, judul, y, h, baris, rona=AKSEN, isi=PUTIH,
          tebal=1.2, catatan=None):
    dalam = R - L - 46 - 14
    kotak(ax, L, y, R - L, h, isi=isi, tepi=rona, tebal=tebal)
    kotak(ax, L, y, 30, h, isi=rona, tepi=rona)
    teks(ax, L + 15, y + h / 2 + 5, ax_no, 13, PUTIH, "bold", rata="center")
    teks(ax, L + 46, y + 22, judul, 12, TINTA, "bold", muat=dalam * 0.62)
    if catatan:
        teks(ax, R - 14, y + 22, catatan, 8.5, TINTA_3, font=FM, rata="right")
    for i, b in enumerate(baris):
        teks(ax, L + 46, y + 41 + i * 16, b, 8.5, TINTA_2, font=FM,
             muat=dalam)


def gambar():
    W, H = 964, 800
    fig, ax = kanvas(W, H)

    # ── pita infrastruktur ────────────────────────────────────────────
    kotak(ax, PITA_X, 20, PITA_W, 770, isi=TANAH, tepi=GARIS,
          putus=(4, 3))
    rel = [
        ("HDFS", ["3 datanodes", "replication 2", "128 MB blocks"], BIRU),
        ("YARN", ["1 RM + 3 NM", "12 vCores", "18,432 MB"], JINGGA),
        ("Spark 3.5.9", ["DataFrame API", "Spark ML", "MinHash LSH"], UNGU),
        ("MapReduce", ["Hadoop Streaming", "awk mapper"], HIJAU),
        ("Neo4j 5.26", ["property graph", "Cypher + GDS"], AMBER),
    ]
    bx, bw = PITA_X + 8, PITA_W - 16
    tinggi = [22 + len(b) * 11 for _, b, _w in rel]
    total = sum(tinggi) + 14 * (len(rel) - 1) + 34
    ty = 20 + (770 - total) / 2
    teks(ax, bx + bw / 2, ty, "INFRASTRUCTURE", 7.4, AKSEN, "bold",
         rata="center", muat=bw)
    ty += 16
    for (nama, baris, warna), t in zip(rel, tinggi):
        kotak(ax, bx, ty, bw, t, isi=PUTIH, tepi=warna, tebal=1.2)
        kotak(ax, bx, ty, bw, 3.5, isi=warna, tepi=warna, r=1)
        teks(ax, bx + bw / 2, ty + 15, nama, 7.8, TINTA, "bold",
             rata="center", muat=bw - 6)
        for i, s in enumerate(baris):
            teks(ax, bx + bw / 2, ty + 26 + i * 11, s, 6.4, TINTA_3, font=FM,
                 rata="center", muat=bw - 6)
        ty += t + 14

    def aliran(y1, y2, label=None):
        panah(ax, TENGAH, y1, TENGAH, y2)
        if label:
            teks(ax, TENGAH + 10, (y1 + y2) / 2 + 3.5, label, 8.5, AKSEN,
                 "bold", font=FM)

    # ── 1. penarikan data ─────────────────────────────────────────────
    y, h = 20, 92
    kotak(ax, L, y, R - L, h, isi=BIRU_BG, tepi=BIRU, tebal=1.2)
    kotak(ax, L, y, 30, h, isi=BIRU, tepi=BIRU)
    teks(ax, L + 15, y + h / 2 + 5, "1", 13, PUTIH, "bold", rata="center")
    teks(ax, L + 46, y + 22, "Data retrieval", 12, TINTA, "bold")
    teks(ax, R - 14, y + 22, "42 partitions · idempotent · "
         "joined on accession number", 8.5, TINTA_3, font=FM, rata="right")
    for dx, judul, ket in [
            (0, "Path A — NCBI E-utilities",
             "esearch + efetch · FASTA"),
            (376, "Path B — NCBI Virus vvsearch2",
             "metadata CSV · 12 columns")]:
        kotak(ax, L + 46 + dx, y + 32, 352, 46, isi=PUTIH, tepi=BIRU)
        teks(ax, L + 60 + dx, y + 51, judul, 9, TINTA, "bold", muat=324)
        teks(ax, L + 60 + dx, y + 68, ket, 8, TINTA_3, font=FM, muat=324)
    aliran(y + h, y + h + 34, "1,627,536 sequences")

    # ── 2. zona bronze ────────────────────────────────────────────────
    y = 146
    tahap(ax, "2", "Bronze zone — HDFS", y, 48,
          ["raw downloads, never modified · source of truth for "
           "re-running the pipeline"], rona=BIRU, isi=BIRU_BG)
    aliran(y + 48, y + 48 + 26)

    # ── 3. gerbang mutu ───────────────────────────────────────────────
    y = 220
    tahap(ax, "3", "Quality gate and deduplication", y, 76,
          ["length ≥ 500 bp (36,388 dropped) · length ≤ "
           "2,600 bp (49 dropped)",
           "ambiguous bases ≤ 5% (4,187 dropped) · SHA-1 "
           "deduplication"], rona=JINGGA, isi=JINGGA_BG)
    aliran(y + 76, y + 76 + 34,
           "1,586,912 passed · 893,599 unique representatives")

    # ── 4. zona silver ────────────────────────────────────────────────
    y = 330
    tahap(ax, "4", "Silver zone — Parquet partitioned by segment", y, 48,
          ["source columns + derived: hash, duplicate count, label "
           "provenance, date precision"], rona=BIRU, isi=BIRU_BG)
    aliran(y + 48, y + 48 + 26)

    # ── 5. rekayasa fitur ─────────────────────────────────────────────
    y, h = 404, 88
    kotak(ax, L, y, R - L, h, isi=UNGU_BG, tepi=UNGU, tebal=1.6)
    kotak(ax, L, y, 30, h, isi=UNGU, tepi=UNGU)
    teks(ax, L + 15, y + h / 2 + 5, "5", 13, PUTIH, "bold", rata="center")
    teks(ax, L + 46, y + 22, "Alignment-free feature engineering", 12, TINTA,
         "bold")
    pipa = ["k-mer, k = 8", "CountVectorizer", "IDF", "Normalizer L2"]
    px, pw = L + 46, 160
    for i, s in enumerate(pipa):
        kotak(ax, px, y + 32, pw, 30, isi=PUTIH, tepi=UNGU)
        teks(ax, px + pw / 2, y + 51, s, 8.6, TINTA, "bold", font=FM,
             rata="center", muat=pw - 8)
        if i < len(pipa) - 1:
            panah(ax, px + pw + 3, y + 47, px + pw + 20, y + 47, UNGU, 1.4)
        px += pw + 23
    teks(ax, L + 46, y + 78, "SparseVector, 65,536 dimensions · 56,171 "
         "k-mers observed · 2.49% density · 38.7 GB on HDFS",
         8.5, TINTA_2, font=FM, muat=R - L - 60)

    # percabangan ke 6a dan 6b
    kiri, kanan = L + 185, R - 185
    panah(ax, TENGAH, y + h, TENGAH, y + h + 14)
    ax.plot([kiri, kanan], [y + h + 14] * 2, color=TINTA_3, linewidth=1.4,
            zorder=3)
    panah(ax, kiri, y + h + 14, kiri, y + h + 30)
    panah(ax, kanan, y + h + 14, kanan, y + h + 30)

    # ── 6a dan 6b ─────────────────────────────────────────────────────
    y, h = 522, 102
    for x0, no, rona, latar, judul, baris in [
        (L, "6a", HIJAU, HIJAU_BG, "Classification", [
            "Task A  segment, 8 classes",
            "Task B1 subtype from HA + NA, 21 classes",
            "Task B2 subtype from internal segments",
            "LogReg · RandomForest · NaiveBayes",
            "train-test split by isolate"]),
        (R - 370, "6b", AMBER, AMBER_BG, "Similarity graph", [
            "MinHash LSH · Jaccard threshold 0.12",
            "sample ≤ 2,500 nodes per segment",
            "label propagation → connected components",
            "PageRank → cluster centrality",
            "358,212 edges · eight segments"])]:
        kotak(ax, x0, y, 370, h, isi=latar, tepi=rona, tebal=1.2)
        kotak(ax, x0, y, 30, h, isi=rona, tepi=rona)
        teks(ax, x0 + 15, y + h / 2 + 4, no, 10.5, PUTIH, "bold",
             rata="center")
        teks(ax, x0 + 44, y + 21, judul, 11, TINTA, "bold")
        for i, b in enumerate(baris):
            teks(ax, x0 + 44, y + 39 + i * 13.5, b, 7.6, TINTA_2, font=FM,
                 muat=370 - 44 - 10)

    panah(ax, kiri, y + h, kiri, y + h + 16)
    panah(ax, kanan, y + h, kanan, y + h + 16)
    ax.plot([kiri, kanan], [y + h + 16] * 2, color=TINTA_3, linewidth=1.4,
            zorder=3)
    panah(ax, TENGAH, y + h + 16, TENGAH, y + h + 32)

    # ── 7. penapisan ──────────────────────────────────────────────────
    y = 656
    tahap(ax, "7", "Reassortment candidate screening", y, 60,
          ["predicted subtype ≠ recorded subtype, at high "
           "confidence",
           "→ 1,990 candidates across 1,238 strains, mean "
           "confidence 0.909"],
          rona=MERAH, isi=MERAH_BG, tebal=1.6)
    panah(ax, TENGAH, y + 60, TENGAH, y + 60 + 14)

    # ── 8. validasi ───────────────────────────────────────────────────
    y = 730
    tahap(ax, "8", "Independent validation", y, 60,
          ["host enrichment — a variable never used as a model "
           "feature",
           "Cochran–Mantel–Haenszel OR · 17 region × decade "
           "strata"],
          rona=TOSCA, isi=TOSCA_BG, tebal=1.6)

    return fig


if __name__ == "__main__":
    fig = gambar()
    jalan = KELUARAN / "gambar1-metodologi.png"
    fig.savefig(jalan, dpi=DPI, facecolor=PUTIH, bbox_inches="tight",
                pad_inches=0.14)
    plt.close(fig)
    print("  %-30s %7.1f KB" % (jalan.name, jalan.stat().st_size / 1024))
