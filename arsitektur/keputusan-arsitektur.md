# Keputusan Arsitektur

| # | Keputusan |
|---|---|
| KA-01 | Dua jalur ingestion, bukan satu |
| KA-02 | Partisi per tahun, pecah adaptif per bulan |
| KA-03 | Tiga zona data lake: bronze, silver, gold |
| KA-04 | Faktor replikasi HDFS 2 |
| KA-05 | Representasi vektor jarang |
| KA-06 | *k* = 8 untuk seluruh pemodelan |
| KA-07 | YARN sebagai satu-satunya manajer sumber daya |
| KA-08 | MapReduce dijalankan sungguhan |
| KA-09 | Tiga teknologi penyimpanan |
| KA-10 | Jupyter sebagai *gateway node* |
| KA-11 | MySQL di luar klaster |
| KA-12 | Graf kemiripan dibangun atas sampel |
| KA-13 | Algoritma iteratif memakai *checkpoint*, bukan *cache* |

## KA-09 — Pembagian peran penyimpanan

| | Peran | Alternatif yang ditolak |
|---|---|---|
| HDFS | data mentah dan turunan besar | berkas besar, akses berurutan, replikasi |
| MySQL | tabel mart untuk dashboard | kueri titik berlatensi milidetik |
| Neo4j | jaringan turunan | lintasan berkedalaman tak tetap |

## KA-12 — Sapuan ambang jarak Jaccard

| ambang | tepi | derajat | komponen | komponen terbesar |
|---|---|---|---|---|
| 0,05 | 2.032 | 1,6 | — | graf nyaris tidak terhubung |
| 0,08 | 7.995 | 6,1 | 155 | 8,6% |
| **0,12** | **19.233** | **14,8** | **154** | **19,1%** |
| 0,15 | 29.252 | 22,5 | — | berisiko satu komponen raksasa |
| 0,25 | 79.777 | 61,3 | — | — |
| 0,35 | 145.856 | 112,0 | — | — |

Diukur pada segmen 4, 2.604 simpul.
