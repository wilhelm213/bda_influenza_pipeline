$ErrorActionPreference = "Stop"
$vhdx    = "D:\docker\wsl\disk\docker_data.vhdx"
$akar    = "D:\docker"
$butuhGB = 30

function Tulis($teks, $warna = "Gray") { Write-Host $teks -ForegroundColor $warna }
function BebasGB { [math]::Round((Get-PSDrive D).Free / 1GB, 2) }
function UkuranGB($p) { [math]::Round((Get-Item $p -Force).Length / 1GB, 2) }

Tulis "`n=== PEMADATAN docker_data.vhdx ===`n" "Cyan"

$pr = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Tulis "GAGAL: jalankan dari PowerShell sebagai Administrator.`n" "Red"; exit 1
}
if (-not (Test-Path $vhdx)) { Tulis "GAGAL: $vhdx tidak ditemukan.`n" "Red"; exit 1 }
if (-not (Get-Command Optimize-VHD -ErrorAction SilentlyContinue)) {
    Tulis "GAGAL: cmdlet Optimize-VHD tidak tersedia." "Red"
    Tulis "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-Management-PowerShell`n" "Yellow"
    exit 1
}
$terkompresi = (Get-Item $vhdx -Force).Attributes -band [IO.FileAttributes]::Compressed
if ($terkompresi -and (BebasGB) -lt $butuhGB) {
    Tulis "GAGAL: berkas masih terkompresi dan D: hanya punya $(BebasGB) GB bebas." "Red"
    Tulis "       Dekompresi sementara MENAMBAH pemakaian sekitar 19 GB." "Red"
    Tulis "       Kosongkan Recycle Bin D: dulu:  rd /s /q D:\`$Recycle.Bin`n" "Red"
    exit 1
}

$proses = Get-Process -Name "Docker Desktop", "com.docker.backend",
                            "com.docker.build", "com.docker.dev-envs" `
                            -ErrorAction SilentlyContinue
if ($proses) {
    Tulis "Menghentikan $($proses.Count) sisa proses Docker ..." "Gray"
    $proses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 4
}

Tulis "Mematikan seluruh distro WSL ..." "Gray"
wsl --shutdown
Start-Sleep -Seconds 6

$terkunci = $true
foreach ($n in 1..10) {
    try { $fs = [IO.File]::Open($vhdx,'Open','ReadWrite','None'); $fs.Close(); $terkunci = $false; break }
    catch { Tulis "  menunggu berkas dilepas ... ($n/10)" "DarkGray"; Start-Sleep -Seconds 3 }
}
if ($terkunci) {
    Tulis "`nGAGAL: berkas masih terkunci. Nyalakan ulang Windows lalu jalankan" "Red"
    Tulis "       skrip ini SEBELUM membuka Docker Desktop.`n" "Red"; exit 1
}

$sebelumGB  = UkuranGB $vhdx
$dSebelum   = BebasGB
Tulis "`nSebelum:" "White"
Tulis "  docker_data.vhdx : $sebelumGB GB"
Tulis "  D: bebas         : $dSebelum GB"
Tulis "  atribut          : $((Get-Item $vhdx -Force).Attributes)"

if ((Get-Item $vhdx -Force).Attributes -band [IO.FileAttributes]::Compressed) {
    Tulis "`n[1/2] Melepas kompresi NTFS." "Cyan"
    Tulis "      Seluruh berkas 641 GB harus ditulis ulang, jadi ini bagian" "Yellow"
    Tulis "      paling lama -- 30 sampai 90 menit. Jangan tutup jendela ini.`n" "Yellow"

    $jam1 = [Diagnostics.Stopwatch]::StartNew()
    & cmd /c "compact /u /s:`"$akar`" /i" | Select-Object -Last 6
    $jam1.Stop()

    $atr = (Get-Item $vhdx -Force).Attributes
    if ($atr -band [IO.FileAttributes]::Compressed) {
        Tulis "`nGAGAL: atribut Compressed masih menempel ($atr)." "Red"
        Tulis "       Coba manual:  compact /u `"$vhdx`"" "Yellow"
        Tulis "       Beri tahu Claude hasilnya.`n" "Yellow"; exit 1
    }
    Tulis "      Selesai dalam $([math]::Round($jam1.Elapsed.TotalMinutes,1)) menit. Atribut sekarang: $atr" "Green"
    Tulis "      D: bebas         : $(BebasGB) GB  (turun sementara, ini normal)"
} else {
    Tulis "`n[1/2] Berkas sudah tidak terkompresi -- dilewati." "Green"
}

Tulis "`n[2/2] Memadatkan disk virtual. 10-40 menit.`n" "Cyan"
$jam2 = [Diagnostics.Stopwatch]::StartNew()
try {
    Optimize-VHD -Path $vhdx -Mode Full
} catch {
    Tulis "Mode Full gagal: $($_.Exception.Message)" "Yellow"
    Tulis "Mencoba Mode Quick sebagai cadangan ...`n" "Yellow"
    Optimize-VHD -Path $vhdx -Mode Quick
}
$jam2.Stop()

$sesudahGB = UkuranGB $vhdx
$dSesudah  = BebasGB
Tulis "`n=== HASIL ===" "Cyan"
Tulis "  docker_data.vhdx : $sebelumGB GB  ->  $sesudahGB GB"
Tulis "  D: bebas         : $dSebelum GB  ->  $dSesudah GB"
Tulis "`n  Dikembalikan     : $([math]::Round($dSesudah - $dSebelum, 2)) GB" "Green"
Tulis "  Total waktu      : $([math]::Round(($jam2.Elapsed.TotalMinutes + $(if($jam1){$jam1.Elapsed.TotalMinutes}else{0})),1)) menit`n" "Green"

if (($sebelumGB - $sesudahGB) -lt 50) {
    Tulis "Catatan: yang kembali jauh lebih sedikit dari perkiraan (~500 GB)." "Yellow"
    Tulis "Beri tahu Claude angka di atas.`n" "Yellow"
}

Tulis "Docker Desktop sudah aman dibuka kembali." "Cyan"
Tulis "Biarkan D:\docker TIDAK terkompresi seterusnya: kompresi NTFS di sana" "Gray"
Tulis "hanya hemat ~3%, memperlambat I/O, dan memblokir pemadatan berikutnya.`n" "Gray"
