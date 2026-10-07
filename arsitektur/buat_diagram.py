from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

KELUARAN = Path(__file__).parent
DPI = 200

TEAL      = "#0d6e63"
TEAL_BG   = "#e2efec"
TANAH     = "#f6f8f6"
PUTIH     = "#ffffff"
TINTA     = "#101713"
TINTA_3   = "#7c8781"
KET       = "#101713"
GARIS     = "#cfd8d2"
HOST      = "#8a4b16"
HOST_BG   = "#f6eee4"

F = "DejaVu Sans"
FM = "DejaVu Sans Mono"

def kanvas(lebar, tinggi):
    fig, ax = plt.subplots(figsize=(lebar / 100, tinggi / 100))
    ax.set_xlim(0, lebar)
    ax.set_ylim(tinggi, 0)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax

def kotak(ax, x, y, w, h, isi=PUTIH, tepi=GARIS, tebal=1.0, putus=None, r=3):
    p = FancyBboxPatch(
        (x, y + h), w, -h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        linewidth=tebal, edgecolor=tepi, facecolor=isi,
        linestyle=(0, putus) if putus else "solid", zorder=2)
    ax.add_patch(p)

def teks(ax, x, y, s, uk=11.5, warna=TINTA, tebal="normal", font=F, rata="left"):
    ax.text(x, y, s, fontsize=uk, color=warna, fontweight=tebal,
            fontfamily=font, ha=rata, va="baseline", zorder=3)

def panah(ax, x1, y1, x2, y2, warna=TINTA_3, tebal=1.3):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
        linewidth=tebal, color=warna, shrinkA=0, shrinkB=0, zorder=3))

def simpan(fig, nama):
    jalan = KELUARAN / nama
    fig.savefig(jalan, dpi=DPI, facecolor=PUTIH, bbox_inches="tight",
                pad_inches=0.12)
    plt.close(fig)
    kb = jalan.stat().st_size / 1024
    print(f"  {nama:<32} {kb:>7,.0f} KB")

def gambar1():
    fig, ax = kanvas(900, 600)

    lapisan = [
        ("SUMBER", "Data", 20, 58, False, [
            (210, 312, "NCBI E-utilities — FASTA", None),
            (536, 312, "NCBI Virus vvsearch2 — CSV", None)]),
        ("INGESTION", "Notebook 01", 92, 58, False, [
            (210, 312, "42 partisi · pecah bulanan > 60.000", None),
            (536, 312, "idempoten · batas laju 3 req/detik", None)]),
        ("STORAGE", "HDFS", 164, 88, True, [
            (210, 203, "Zona bronze", "apa adanya · 530 MB"),
            (427, 203, "Zona silver", "Parquet · 888 MB"),
            (644, 204, "Zona gold", "teragregasi")]),
        ("RESOURCE", "YARN", 266, 52, True, [
            (210, 638, "ResourceManager + 3 NodeManager · 12 vCore · 18.432 MB", None)]),
        ("PROCESSING", "Notebook 03", 332, 66, False, [
            (210, 312, "MapReduce — Hadoop Streaming", "mapper & reducer awk"),
            (536, 312, "Apache Spark 3.5.9", "DataFrame · Spark SQL · MLlib")]),
        ("ANALYTICS", "Notebook 04–06", 412, 66, False, [
            (210, 203, "Fitur k-mer", "alignment-free"),
            (427, 203, "Machine learning", "segmen · subtipe"),
            (644, 204, "Graph analytics", "MinHash LSH")]),
        ("SERVING", "Notebook 07", 492, 66, False, [
            (210, 203, "MySQL", "skema bintang"),
            (427, 203, "Neo4j", "property graph"),
            (644, 204, "Dashboard", "Plotly mandiri")]),
    ]

    for i, (l1, l2, y, h, inti, chips) in enumerate(lapisan):
        kotak(ax, 40, y, 820, h,
              isi=TEAL_BG if inti else TANAH,
              tepi=TEAL if inti else GARIS,
              tebal=1.6 if inti else 1.0)
        teks(ax, 54, y + 23, l1, 9.5, TEAL, "bold", FM)
        teks(ax, 54, y + 40, l2, 11.5, TINTA, "bold")
        if l2 == "HDFS":
            teks(ax, 54, y + 57, "replikasi 2", 8.5, KET, font=FM)
            teks(ax, 54, y + 71, "blok 128 MB", 8.5, KET, font=FM)

        for cx, cw, judul, ket in chips:
            ch = 56 if h == 88 else (38 if ket else (28 if h == 52 else 30))
            cy = y + (h - ch) / 2
            kotak(ax, cx, cy, cw, ch, PUTIH, TEAL if inti else GARIS,
                  1.3 if inti else 1.0)
            if ket:

                teks(ax, cx + 14, cy + ch * 0.40, judul, 10.5)
                teks(ax, cx + 14, cy + ch * 0.75, ket, 8.5, KET, font=FM)
            else:
                teks(ax, cx + 14, cy + ch / 2 + 4, judul, 10.5)

        if i < len(lapisan) - 1:
            panah(ax, 450, y + h, 450, lapisan[i + 1][2])

    teks(ax, 40, 582,
         "Lapisan bergaris tebal = komponen inti Hadoop yang menjadi fondasi "
         "seluruh lapisan di atasnya.", 8.5, KET, font=FM)
    simpan(fig, "1-arsitektur-berlapis.png")

def gambar2():
    fig, ax = kanvas(900, 440)

    kotak(ax, 30, 46, 700, 330, "none", TINTA_3, 1.3, putus=(6, 4), r=4)
    teks(ax, 42, 38, "KLASTER DOCKER — jaringan bda", 9.5, KET, font=FM)

    kotak(ax, 52, 76, 322, 148, TANAH, TEAL, 1.3)
    teks(ax, 64, 96, "HDFS", 9.5, TEAL, "bold", FM)
    kotak(ax, 70, 106, 150, 38, PUTIH, TEAL, 1.4)
    teks(ax, 80, 123, "bda-namenode", 10.5)
    teks(ax, 80, 137, "9870 · 8020", 8.5, KET, font=FM)
    for i, x in enumerate((70, 166, 262), start=1):
        kotak(ax, x, 160, 88, 44)
        teks(ax, x + 8, 180, f"datanode{i}", 10)
        teks(ax, x + 8, 195, "2 GB", 8.5, KET, font=FM)

    kotak(ax, 394, 76, 312, 148, TANAH, TEAL, 1.3)
    teks(ax, 406, 96, "YARN", 9.5, TEAL, "bold", FM)
    kotak(ax, 412, 106, 180, 38, PUTIH, TEAL, 1.4)
    teks(ax, 422, 123, "bda-resourcemanager", 10.5)
    teks(ax, 422, 137, "8088", 8.5, KET, font=FM)
    for i, x in enumerate((412, 508, 604), start=1):
        kotak(ax, x, 160, 88, 44)
        teks(ax, x + 8, 180, f"nodemgr{i}", 10)

        teks(ax, x + 8, 195, "7 GB · 4 vCore", 6.5, KET, font=FM)

    kotak(ax, 52, 256, 322, 56, PUTIH, TEAL, 1.4)
    teks(ax, 64, 277, "bda-jupyter — gateway node", 10.5, TINTA, "bold")
    teks(ax, 64, 292, "driver Spark · klien Hadoop", 8.5, KET, font=FM)
    teks(ax, 64, 305, "tempat job disubmit, bukan dieksekusi", 8.5, KET, font=FM)

    kotak(ax, 394, 256, 312, 56, PUTIH, TEAL, 1.4)
    teks(ax, 406, 277, "bda-neo4j", 10.5, TINTA, "bold")
    teks(ax, 406, 292, "graph database · Cypher + GDS", 8.5, KET, font=FM)
    teks(ax, 406, 305, "7474 browser · 7687 bolt", 8.5, KET, font=FM)

    kotak(ax, 760, 106, 120, 70, HOST_BG, HOST, 1.3, putus=(4, 3))
    teks(ax, 770, 128, "MySQL", 10.5, TINTA, "bold")
    teks(ax, 770, 143, "Windows host", 8.5, KET, font=FM)
    teks(ax, 770, 157, "di luar klaster", 8.5, KET, font=FM)

    panah(ax, 213, 256, 213, 226, TEAL, 1.5)
    panah(ax, 550, 256, 550, 226, TEAL, 1.5)
    panah(ax, 374, 284, 392, 284)
    panah(ax, 706, 141, 758, 141)
    teks(ax, 712, 134, "JDBC", 8.5, KET, font=FM)

    teks(ax, 734, 196, "host.docker.internal", 8, KET, font=FM)

    teks(ax, 30, 404,
         "Jupyter menyubmit ke YARN; YARN mengalokasikan container di NodeManager; "
         "NodeManager membaca dan menulis ke HDFS.", 8.5, KET, font=FM)
    teks(ax, 30, 420,
         "Penulisan JDBC terjadi di executor, bukan di driver — karena itu "
         "NodeManager harus menjangkau host Windows.", 8.5, KET, font=FM)
    simpan(fig, "2-topologi-klaster.png")

def gambar3():
    fig, ax = kanvas(900, 340)

    zona = [
        (30, "NCBI", "dua layanan", "1.627.536", "sekuens"),
        (222, "Bronze", "HDFS, apa adanya", "530 MB", "201 berkas"),
        (414, "Silver", "Parquet, 26 kolom", "1.586.912", "lolos 97,5%"),
        (606, "Fitur", "vektor jarang", "892.344", "× 65.536 dimensi"),
    ]
    for x, judul, sub, nilai, ket in zona:
        kotak(ax, x, 60, 150, 86, PUTIH, TEAL, 1.4)
        teks(ax, x + 14, 84, judul, 11.5, TINTA, "bold")
        teks(ax, x + 14, 100, sub, 8.5, KET, font=FM)
        teks(ax, x + 14, 122, nilai, 10.5, TEAL, "bold", FM)
        teks(ax, x + 14, 136, ket, 8.5, KET, font=FM)

    for x1, label in ((180, "unduh"), (372, "saring"), (564, "k-mer")):
        panah(ax, x1, 103, x1 + 38, 103, TEAL, 1.5)
        teks(ax, x1 + 19, 50, label, 8, KET, font=FM, rata="center")

    panah(ax, 489, 146, 489, 196, TEAL, 1.5)
    panah(ax, 681, 146, 681, 196, TEAL, 1.5)

    kotak(ax, 414, 200, 150, 76, PUTIH, TEAL, 1.4)
    teks(ax, 428, 224, "Gold → MySQL", 11, TINTA, "bold")
    teks(ax, 428, 241, "skema bintang", 8.5, KET, font=FM)
    teks(ax, 428, 256, "teragregasi", 8.5, KET, font=FM)

    kotak(ax, 606, 200, 150, 76, PUTIH, TEAL, 1.4)
    teks(ax, 620, 224, "Graf → Neo4j", 11, TINTA, "bold")
    teks(ax, 620, 241, "property graph", 8.5, KET, font=FM)
    teks(ax, 620, 256, "sentralitas", 8.5, KET, font=FM)

    panah(ax, 564, 238, 602, 238, TEAL, 1.5)

    kotak(ax, 30, 200, 330, 76, PUTIH, TINTA_3, 1.2, putus=(4, 3))
    teks(ax, 44, 224, "Keluaran untuk pengambil keputusan", 11, TINTA, "bold")

    teks(ax, 44, 242, "dashboard · tabel mart · kandidat", 8.5, KET, font=FM)
    teks(ax, 44, 258, "tiga insight yang disyaratkan", 8.5, KET, font=FM)
    panah(ax, 412, 238, 364, 238, TEAL, 1.5)

    teks(ax, 30, 312,
         "Zona bronze tidak pernah diubah. Bila terjadi kesalahan pada tahap mana "
         "pun di hilir, seluruh proses", 8.5, KET, font=FM)
    teks(ax, 30, 326,
         "dapat diulang dari sana tanpa mengunduh ulang dari NCBI — itulah gunanya "
         "memisahkan zona.", 8.5, KET, font=FM)
    simpan(fig, "3-aliran-data.png")

def gambar4():
    fig, ax = kanvas(1020, 700)

    BIRU_BG = "#eef3f6"
    BIRU_TP = "#9fb6c4"
    KUNING  = "#f5c344"
    KUNING_T = "#c99a1e"
    ABU_BG  = "#eceee9"

    def band(x, y, w, h, judul, isi=BIRU_BG, tepi=BIRU_TP):
        kotak(ax, x, y, w, h, isi, tepi, 1.2)
        if judul:
            teks(ax, x + 12, y + 20, judul, 10.5, TINTA, "bold")

    def modul(x, y, w, h, judul, ket=None, isi=KUNING, tepi=KUNING_T,
              uk=9.5, putus=None):
        kotak(ax, x, y, w, h, isi, tepi, 1.1, putus=putus)
        if ket:
            teks(ax, x + 10, y + h * 0.42, judul, uk, TINTA, "bold")
            teks(ax, x + 10, y + h * 0.78, ket, 7, KET, font=FM)
        else:
            teks(ax, x + 10, y + h / 2 + 3.5, judul, uk, TINTA, "bold")

    def vlabel(x, y, s, uk=10.5):
        ax.text(x, y, s, fontsize=uk, color=TINTA, fontweight="bold",
                fontfamily=F, ha="center", va="center", rotation=90, zorder=3)

    band(18, 40, 66, 526, None)
    vlabel(32, 300, "Data Sources")
    for i, (lbl, ket) in enumerate([
            ("CSV metadata", "terstruktur"),
            ("baris defline", "semi-terstruktur"),
            ("untai basa FASTA", "tidak terstruktur")]):
        y = 70 + i * 165
        kotak(ax, 46, y, 32, 150, PUTIH, BIRU_TP, 1.0)
        ax.text(56, y + 75, lbl, fontsize=8, color=TINTA, fontweight="bold",
                fontfamily=F, ha="center", va="center", rotation=90, zorder=3)
        ax.text(70, y + 75, ket, fontsize=6.5, color=KET,
                fontfamily=FM, ha="center", va="center", rotation=90, zorder=3)

    band(92, 40, 58, 526, None)
    vlabel(107, 300, "Ingestion Layer")
    for i, (lbl,) in enumerate([("E-utilities",), ("vvsearch2",),
                                ("42 partisi",), ("idempoten",)]):
        y = 74 + i * 124
        kotak(ax, 122, y, 22, 112, KUNING, KUNING_T, 1.0)
        ax.text(133, y + 56, lbl, fontsize=7.5, color=TINTA, fontweight="bold",
                fontfamily=F, ha="center", va="center", rotation=90, zorder=3)

    band(160, 40, 840, 84, "Visualization Layer")
    modul(176, 66, 262, 46, "Administrasi Hadoop",
          "NameNode 9870 · YARN 8088 · Neo4j 7474")
    modul(452, 66, 262, 46, "JupyterLab — IDE analis",
          "notebook 00 sampai 07")
    modul(728, 66, 256, 46, "Dashboard Plotly",
          "HTML mandiri · tiga insight")

    band(160, 136, 596, 196, "Hadoop Platform Management Layer")
    modul(176, 164, 564, 40, "YARN — ResourceManager + 3 NodeManager",
          "12 vCore · 18.432 MB · penjadwal tunggal untuk MapReduce dan Spark",
          uk=10)
    modul(176, 214, 274, 44, "MapReduce",
          "Hadoop Streaming · mapper & reducer awk")
    modul(466, 214, 274, 44, "Apache Spark 3.5.9",
          "DataFrame API · pengganti Pig dan Hive")
    modul(176, 268, 176, 44, "Spark SQL", "transformasi asli")
    modul(368, 268, 176, 44, "Spark MLlib", "klasifikasi")
    modul(560, 268, 180, 44, "MinHash LSH", "graf kemiripan")

    band(768, 136, 232, 196, "Analytics Engines")
    for i, (j, k, aktif) in enumerate([
            ("Statistical Analytics", "gerbang mutu · ablasi k", True),
            ("Text Analytics", "k-mer · TF-IDF", True),
            ("Machine Learning", "LogReg · RF · NB", True),
            ("Graph Analytics", "PageRank · Louvain", True),
            ("Real-Time Engine", "tidak dipakai — batch", False)]):

        y = 164 + i * 33
        kotak(ax, 784, y, 200, 30, PUTIH if aktif else ABU_BG,
              KUNING_T if aktif else TINTA_3, 1.1,
              putus=None if aktif else (3, 2))
        teks(ax, 794, y + 13, j, 8.5, TINTA, "bold")
        teks(ax, 794, y + 25, k, 6.3, KET, font=FM)

    band(160, 344, 432, 116, "Hadoop Storage Layer")
    modul(176, 372, 400, 36, "HDFS — data lake",
          "zona bronze · silver · gold  |  replikasi 2 · blok 128 MB")
    modul(176, 416, 400, 36, "Neo4j — NoSQL graph database",
          "property graph · Cypher · Graph Data Science")

    band(604, 344, 396, 116, "Data Warehouses")
    kotak(ax, 620, 376, 54, 66, PUTIH, BIRU_TP, 1.2, r=10)
    teks(ax, 628, 404, "mart", 8.5, KET, font=FM)
    modul(686, 380, 298, 58, "MySQL 8.0",
          "fact_sekuens + tiga tabel dimensi")
    teks(ax, 686, 452, "di luar klaster, pada host Windows", 7, KET, font=FM)

    band(160, 472, 432, 108, "Hadoop Infrastructure Layer")
    modul(176, 500, 400, 34, "Virtualized Services — Docker Compose",
          "sembilan container pada jaringan bda")
    modul(176, 540, 400, 30, "WSL2 pada Windows 11 — satu mesin fisik",
          None, ABU_BG, TINTA_3, uk=8.5, putus=(3, 2))

    band(604, 472, 396, 108, None, ABU_BG, TINTA_3)
    teks(ax, 616, 492, "Sumber daya fisik", 9.5, TINTA, "bold")
    for i, (a, b) in enumerate([("CPU", "12 vCore"), ("RAM", "18.432 MB"),
                                ("Disk", "HDFS 2,95 TB")]):
        x = 620 + i * 126
        kotak(ax, x, 502, 112, 62, PUTIH, TINTA_3, 1.0)
        teks(ax, x + 12, 524, a, 9, TINTA, "bold")
        teks(ax, x + 12, 544, b, 7.5, KET, font=FM)

    band(18, 592, 982, 34, None)
    teks(ax, 32, 613, "Security Layer", 10, TINTA, "bold")
    teks(ax, 206, 613,
         "hak akses minimum MySQL  ·  kredensial terpisah dari kode  ·  "
         "jaringan Docker terisolasi", 8, KET, font=FM)

    band(18, 634, 982, 34, None)
    teks(ax, 32, 655, "Monitoring Layer", 10, TINTA, "bold")
    teks(ax, 206, 655,
         "jejak audit JSONL per tahap  ·  Spark UI 4040  ·  YARN REST API  ·  "
         "laporan kualitas data", 8, KET, font=FM)

    teks(ax, 18, 690,
         "Kerangka lapisan mengikuti arsitektur referensi Hadoop; isi tiap kotak "
         "adalah komponen yang benar-benar dipakai proyek ini.",
         7.5, KET, font=FM)
    simpan(fig, "4-arsitektur-referensi.png")

if __name__ == "__main__":
    print(f"Menulis diagram ke {KELUARAN}\n")
    gambar1()
    gambar2()
    gambar3()
    gambar4()
    print("\nSelesai. Sisipkan berkas PNG di atas ke laporan Anda.")
