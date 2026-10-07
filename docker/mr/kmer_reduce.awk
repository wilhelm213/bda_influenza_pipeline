# ═══════════════════════════════════════════════════════════════════
# REDUCER — menjumlahkan cacah tiap k-mer
# ═══════════════════════════════════════════════════════════════════
#
# Sisi *reduce* dari pencacahan. Berkas yang sama dipakai juga sebagai
# *combiner*: penjumlahan bersifat asosiatif dan komutatif, sehingga
# menjumlahkan sebagian di sisi mapper lalu menjumlahkan sisanya di
# reducer memberi hasil yang persis sama. Combiner inilah yang menahan
# ledakan lalu lintas jaringan -- tanpanya setiap satu dari ratusan juta
# k-mer harus diseberangkan satu per satu ke reducer.
#
# Penjumlahan dilakukan sambil membaca, tanpa menyimpan kamus apa pun di
# memori. Itu bisa dilakukan karena Hadoop menjamin seluruh baris dengan
# kunci yang sama tiba berurutan pada reducer yang sama. Jaminan itu
# persis guna tahap *shuffle and sort* di tengah MapReduce -- dan tahap
# itu pula yang biasanya paling mahal dari keseluruhan job.
#
# Dipanggil oleh hadoop-streaming.jar, bukan dijalankan langsung:
#   -combiner "awk -f kmer_reduce.awk"
#   -reducer  "awk -f kmer_reduce.awk"
# ═══════════════════════════════════════════════════════════════════

BEGIN {
    FS = "\t"
    kunci = ""
    total = 0
}

{
    if ($1 == kunci) {
        total += $2
    } else {
        if (kunci != "") print kunci "\t" total
        kunci = $1
        total = $2
    }
}

END {
    if (kunci != "") print kunci "\t" total
}
