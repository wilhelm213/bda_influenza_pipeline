# ═══════════════════════════════════════════════════════════════════
# MAPPER — memecah sekuens FASTA menjadi k-mer
# ═══════════════════════════════════════════════════════════════════
#
# Sisi *map* dari pencacahan k-mer. Satu rekaman sekuens masuk, sejumlah
# pasangan `k-mer <TAB> 1` keluar. Reducer yang menjumlahkannya.
#
# Kenapa awk dan bukan Python. Image apache/hadoop:3.3.6 berbasis
# CentOS 7 yang sudah habis masa dukungannya: cermin repositorinya sudah
# dimatikan, sehingga `yum install python3` gagal dengan "No package
# python3 available". Memasang Python berarti membangun image sendiri
# atau menarik Miniforge ratusan megabita ke tiap NodeManager. awk sudah
# ada di setiap node Hadoop tanpa dipasang, dan untuk pekerjaan
# geser-jendela seperti ini kemampuannya lebih dari cukup.
#
# Jebakan yang khas FASTA. Satu rekaman terdiri dari baris deskripsi
# berawalan ">" lalu sejumlah baris basa yang dipecah rata pada lebar
# tertentu. Pemecahan itu murni kosmetik dan tidak punya arti biologis.
# Kalau tiap baris diproses sendiri, setiap k-mer yang melintasi batas
# baris ikut hilang -- pada lebar 70 dan k=8 sekitar 10% k-mer menguap
# diam-diam tanpa satu pun pesan galat. Karena itu potongan basa ditahan
# sampai rekaman berikutnya datang, baru dipancarkan sebagai satu untai.
#
# Dipanggil oleh hadoop-streaming.jar, bukan dijalankan langsung:
#   -mapper "awk -v K=8 -f kmer_map.awk"
# ═══════════════════════════════════════════════════════════════════

BEGIN {
    if (K == "") K = 8
    seq = ""
}

# Baris deskripsi menutup rekaman sebelumnya.
/^>/ {
    if (seq != "") { pancarkan(seq); seq = "" }
    next
}

# Baris basa cuma ditumpuk; belum diproses sampai rekamannya utuh.
{
    gsub(/[ \t\r]/, "", $0)
    seq = seq toupper($0)
}

END {
    if (seq != "") pancarkan(seq)
}

function pancarkan(s,    n, i, kmer) {
    n = length(s)
    if (n < K) return
    for (i = 1; i <= n - K + 1; i++) {
        kmer = substr(s, i, K)
        # Huruf ambigu (N, R, Y, ...) dibuang di tingkat k-mer, bukan di
        # tingkat sekuens. Satu N hanya merusak K k-mer di sekitarnya,
        # jadi membuang seluruh sekuens karenanya terlalu mahal.
        if (kmer ~ /^[ACGT]+$/) print kmer "\t1"
    }
}
