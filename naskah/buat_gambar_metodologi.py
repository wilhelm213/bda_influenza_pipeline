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


def tahap(ax, ax_no, judul, y, h, baris, isi=PUTIH, tepi=GARIS, tebal=1.0,
          catatan=None):
    dalam = R - L - 46 - 14
    kotak(ax, L, y, R - L, h, isi=isi, tepi=tepi, tebal=tebal)
    kotak(ax, L, y, 30, h, isi=AKSEN, tepi=AKSEN)
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
        ("HDFS", ["3 datanode", "replikasi 2", "blok 128 MB"]),
        ("YARN", ["1 RM + 3 NM", "12 vCore", "18.432 MB"]),
        ("Spark 3.5.9", ["DataFrame API", "Spark ML", "MinHash LSH"]),
        ("MapReduce", ["Hadoop Streaming", "mapper awk"]),
        ("Neo4j 5.26", ["property graph", "Cypher + GDS"]),
    ]
    bx, bw = PITA_X + 8, PITA_W - 16
    tinggi = [22 + len(b) * 11 for _, b in rel]
    total = sum(tinggi) + 14 * (len(rel) - 1) + 34
    ty = 20 + (770 - total) / 2
    teks(ax, bx + bw / 2, ty, "INFRASTRUKTUR", 7.4, AKSEN, "bold",
         rata="center", muat=bw)
    ty += 16
    for (nama, baris), t in zip(rel, tinggi):
        kotak(ax, bx, ty, bw, t, isi=PUTIH, tepi=GARIS_2)
        teks(ax, bx + bw / 2, ty + 14, nama, 7.8, TINTA, "bold",
             rata="center", muat=bw - 6)
        for i, s in enumerate(baris):
            teks(ax, bx + bw / 2, ty + 25 + i * 11, s, 6.4, TINTA_3, font=FM,
                 rata="center", muat=bw - 6)
        ty += t + 14

    def aliran(y1, y2, label=None):
        panah(ax, TENGAH, y1, TENGAH, y2)
        if label:
            teks(ax, TENGAH + 10, (y1 + y2) / 2 + 3.5, label, 8.5, AKSEN,
                 "bold", font=FM)

    # ── 1. penarikan data ─────────────────────────────────────────────
    y, h = 20, 92
    kotak(ax, L, y, R - L, h)
    kotak(ax, L, y, 30, h, isi=AKSEN, tepi=AKSEN)
    teks(ax, L + 15, y + h / 2 + 5, "1", 13, PUTIH, "bold", rata="center")
    teks(ax, L + 46, y + 22, "Penarikan data", 12, TINTA, "bold")
    teks(ax, R - 14, y + 22, "42 partisi · idempoten · gabung "
         "menurut nomor aksesi", 8.5, TINTA_3, font=FM, rata="right")
    for dx, judul, ket in [
            (0, "Jalur A — NCBI E-utilities",
             "esearch + efetch · FASTA"),
            (376, "Jalur B — NCBI Virus vvsearch2",
             "metadata CSV · 12 kolom")]:
        kotak(ax, L + 46 + dx, y + 32, 352, 46, isi=TANAH, tepi=GARIS_2)
        teks(ax, L + 60 + dx, y + 51, judul, 9, TINTA, "bold", muat=324)
        teks(ax, L + 60 + dx, y + 68, ket, 8, TINTA_3, font=FM, muat=324)
    aliran(y + h, y + h + 34, "1.627.536 sekuens")

    # ── 2. zona bronze ────────────────────────────────────────────────
    y = 146
    tahap(ax, "2", "Zona bronze — HDFS", y, 48,
          ["hasil unduh apa adanya, tidak pernah diubah · sumber "
           "kebenaran untuk pengulangan"])
    aliran(y + 48, y + 48 + 26)

    # ── 3. gerbang mutu ───────────────────────────────────────────────
    y = 220
    tahap(ax, "3", "Gerbang mutu dan deduplikasi", y, 76,
          ["panjang ≥ 500 bp (gugur 36.388) · panjang ≤ "
           "2.600 bp (gugur 49)",
           "basa ambigu ≤ 5% (gugur 4.187) · deduplikasi cetakan "
           "SHA-1"])
    aliran(y + 76, y + 76 + 34,
           "1.586.912 lolos · 893.599 wakil unik")

    # ── 4. zona silver ────────────────────────────────────────────────
    y = 330
    tahap(ax, "4", "Zona silver — Parquet berpartisi segmen", y, 48,
          ["kolom asal + kolom turunan: hash, cacah duplikat, asal label, "
           "presisi tanggal"])
    aliran(y + 48, y + 48 + 26)

    # ── 5. rekayasa fitur ─────────────────────────────────────────────
    y, h = 404, 88
    kotak(ax, L, y, R - L, h, isi=AKSEN_BG, tepi=AKSEN, tebal=1.4)
    kotak(ax, L, y, 30, h, isi=AKSEN, tepi=AKSEN)
    teks(ax, L + 15, y + h / 2 + 5, "5", 13, PUTIH, "bold", rata="center")
    teks(ax, L + 46, y + 22, "Rekayasa fitur alignment-free", 12, TINTA,
         "bold")
    pipa = ["k-mer, k = 8", "CountVectorizer", "IDF", "Normalizer L2"]
    px, pw = L + 46, 160
    for i, s in enumerate(pipa):
        kotak(ax, px, y + 32, pw, 30, isi=PUTIH, tepi=AKSEN)
        teks(ax, px + pw / 2, y + 51, s, 8.6, TINTA, "bold", font=FM,
             rata="center", muat=pw - 8)
        if i < len(pipa) - 1:
            panah(ax, px + pw + 3, y + 47, px + pw + 20, y + 47, AKSEN, 1.2)
        px += pw + 23
    teks(ax, L + 46, y + 78, "SparseVector 65.536 dimensi · 56.171 "
         "k-mer teramati · kepadatan 2,49% · 38,7 GB pada HDFS",
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
    for x0, no, judul, baris in [
        (L, "6a", "Klasifikasi", [
            "Tugas A  segmen, 8 kelas",
            "Tugas B1 subtipe dari HA + NA, 21 kelas",
            "Tugas B2 subtipe dari segmen internal",
            "LogReg · RandomForest · NaiveBayes",
            "pembagian latih-uji menurut isolat"]),
        (R - 370, "6b", "Graf kemiripan", [
            "MinHash LSH · ambang Jaccard 0,12",
            "sampel ≤ 2.500 simpul per segmen",
            "label propagation → komponen terhubung",
            "PageRank → sentralitas klaster",
            "358.212 tepi · delapan segmen"])]:
        kotak(ax, x0, y, 370, h)
        kotak(ax, x0, y, 30, h, isi=AKSEN, tepi=AKSEN)
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
    tahap(ax, "7", "Penapisan kandidat reassortment", y, 60,
          ["subtipe terprediksi ≠ subtipe tercatat, pada keyakinan "
           "tinggi",
           "→ 1.990 kandidat dari 1.238 galur, keyakinan rata-rata "
           "0,909"],
          isi=AKSEN_BG, tepi=AKSEN, tebal=1.4)
    panah(ax, TENGAH, y + 60, TENGAH, y + 60 + 14)

    # ── 8. validasi ───────────────────────────────────────────────────
    y = 730
    tahap(ax, "8", "Validasi independen", y, 60,
          ["pengayaan inang — peubah yang tidak pernah menjadi fitur "
           "model",
           "OR Cochran-Mantel-Haenszel · 17 strata wilayah × "
           "dekade"],
          tepi=AKSEN, tebal=1.4)

    return fig


if __name__ == "__main__":
    fig = gambar()
    jalan = KELUARAN / "gambar1-metodologi.png"
    fig.savefig(jalan, dpi=DPI, facecolor=PUTIH, bbox_inches="tight",
                pad_inches=0.14)
    plt.close(fig)
    print("  %-30s %7.1f KB" % (jalan.name, jalan.stat().st_size / 1024))
