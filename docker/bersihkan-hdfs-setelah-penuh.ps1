$ErrorActionPreference = "Continue"

function Tulis($t, $w = "Gray") { Write-Host $t -ForegroundColor $w }

Tulis "Memeriksa Docker..." "Cyan"
$ok = $false
try { docker ps --format "{{.Names}}" | Out-Null; $ok = $? } catch {}
if (-not $ok) {
    Tulis "Docker belum siap. Nyalakan Docker Desktop, tunggu containernya naik, lalu ulangi." "Red"
    exit 1
}

$buang = @(
    "/bda/graph2/kasar_030",
    "/bda/graph2/_ckpt",
    "/bda/graph2/_ckpt_kasar",
    "/bda/graph2/_ckpt_klaster",
    "/bda/graph/_ckpt",
    "/bda/spark-events"
)

Tulis "`nPemakaian HDFS sebelum:" "Cyan"
docker exec bda-namenode hdfs dfs -du -h /bda

foreach ($p in $buang) {
    $ada = docker exec bda-namenode hdfs dfs -test -d $p 2>$null; $adaOk = $?
    if ($adaOk) {
        Tulis "  menghapus $p" "Yellow"
        docker exec bda-namenode hdfs dfs -rm -r -skipTrash $p | Out-Null
    } else {
        Tulis "  lewati $p (tidak ada)" "DarkGray"
    }
}

Tulis "`nMengosongkan tong sampah HDFS..." "Cyan"
docker exec bda-namenode hdfs dfs -expunge | Out-Null

Tulis "`nPemakaian HDFS sesudah:" "Cyan"
docker exec bda-namenode hdfs dfs -du -h /bda
docker exec bda-namenode hdfs dfs -df -h /

Tulis "`nSelesai. Langkah berikutnya:" "Green"
Tulis "  1. Tutup Docker Desktop sepenuhnya (tray -> Quit)."
Tulis "  2. Jalankan compact-docker-vhdx.ps1 SEBAGAI ADMINISTRATOR sekali lagi."
Tulis "     Pemadatan kedua inilah yang mengembalikan ruang dari data yang"
Tulis "     baru saja dihapus di atas."
