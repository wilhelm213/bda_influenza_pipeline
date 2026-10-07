# Pipeline Big Data Surveilans Genomik Influenza A

COMP8035041 Big Data Analytics, Magister Teknik Informatika, BINUS
Graduate Program.

Pipeline menyeluruh atas 1.586.912 sekuens genom Influenza A dari NCBI:
dari pengambilan data, penyimpanan di HDFS, pemrosesan dengan MapReduce
dan Spark di atas YARN, klasifikasi dengan Spark MLlib, sampai graph
analytics di Neo4j.

## Isi

| Folder | |
|---|---|
| `nb/` | Delapan notebook pipeline, berurutan 00 sampai 07 |
| `docker/` | Docker Compose, konfigurasi Hadoop, skrip pemeliharaan |
| `arsitektur/` | Diagram arsitektur beserta generator dan catatan keputusan |
| `laporan/` | Laporan dan generator gambarnya |
| `web/` | Dashboard lima halaman beserta skrip pembangunnya |
| `output/` | Gambar hasil notebook |
| `models/` | Metrik model dan skalabilitas |

## Notebook

| | |
|---|---|
| `00_setup.ipynb` | Pemeriksaan lingkungan dan klaster |
| `01_ingestion.ipynb` | Pengambilan dari NCBI, 42 partisi, idempoten |
| `02_storage_quality.ipynb` | Zona data lake dan gerbang mutu |
| `03_mapreduce_yarn.ipynb` | MapReduce dan Spark pada komputasi identik |
| `04_kmer_features.ipynb` | Fitur k-mer, CountVectorizer, IDF, Normalizer |
| `05_ml_segmen_subtipe.ipynb` | Tiga tugas klasifikasi, tiga algoritma |
| `06_graph.ipynb` | MinHash LSH, komponen terhubung, Neo4j |
| `07_mart_dashboard.ipynb` | Skema bintang MySQL dan dashboard |

## Menjalankan

Kredensial tidak ikut repositori. Siapkan dua berkas lebih dulu:

```bash
cp docker/.env.contoh docker/.env
```

Isi `NEO4J_PASSWORD` di dalamnya. Lalu jalankan notebook `00_setup.ipynb`
sekali; ia akan membuat `nb/bda_secret.json` dari contoh bila belum ada,
dan memberi tahu bidang mana yang perlu diisi.

Nyalakan klaster dengan profil yang sesuai:

```bash
cd docker
docker compose --profile yarn up -d
```

Profil `yarn` dan `standalone` saling eksklusif karena batas memori.

## Data

Zona `lake/`, `stage/`, `features/`, dan `graph/` tidak ikut repositori
karena berukuran ratusan megabita sampai puluhan gigabita dan seluruhnya
dapat dibangun ulang. Jalankan notebook 01 sampai 06 berurutan untuk
menghasilkannya kembali.

Sumber data: NCBI Influenza Virus Database.

## Temuan utama

| | |
|---|---|
| Klasifikasi segmen, F1 makro | 0,9998 |
| Klasifikasi subtipe dari HA+NA | 0,9654 |
| Klasifikasi subtipe dari segmen internal | 0,8678 |
| MapReduce vs Spark pada komputasi identik | 42,4 s vs 65,7 s, hasil identik |
| scikit-learn satu node | gagal dari 25% data ke atas |
| Pengayaan kandidat reassortment pada babi | OR Mantel-Haenszel 10,86 |
