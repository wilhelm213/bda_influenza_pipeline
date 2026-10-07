$ErrorActionPreference = "Continue"

function Tulis($t, $w = "Gray") { Write-Host $t -ForegroundColor $w }
function BebasGB($drive) { [math]::Round((Get-PSDrive $drive).Free / 1GB, 2) }

Tulis "`n=== PEMBERSIHAN DISK ===`n" "Cyan"

$pr = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Tulis "GAGAL: jalankan dari PowerShell sebagai Administrator.`n" "Red"; exit 1
}

$cAwal = BebasGB C
$dAwal = BebasGB D
Tulis "Sebelum:  C: $cAwal GB   D: $dAwal GB`n" "White"

Tulis "[1/3] Membersihkan cache di C: ..." "Cyan"

function Hapus($jalan, $label) {
    if (-not (Test-Path $jalan)) { return }
    $sebelum = BebasGB C
    Get-ChildItem $jalan -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $naik = [math]::Round((BebasGB C) - $sebelum, 2)
    if ($naik -gt 0.01) { Tulis ("      {0,-42} +{1} GB" -f $label, $naik) "Green" }
}

Hapus "$env:LOCALAPPDATA\Temp\*"                    "Temp pengguna"
Hapus "C:\Windows\Temp\*"                           "Temp Windows"
Hapus "$env:LOCALAPPDATA\pip\cache\*"               "cache pip"
Hapus "$env:USERPROFILE\.cache\*"                   "cache ~/.cache"

foreach ($sub in @("Cache", "Code Cache", "GPUCache", "Service Worker\CacheStorage")) {
    Hapus "$env:LOCALAPPDATA\Google\Chrome\User Data\*\$sub\*" "Chrome $sub"
}

foreach ($sub in @("DXCache", "GLCache", "ComputeCache", "NV_Cache")) {
    Hapus "$env:LOCALAPPDATA\NVIDIA\$sub\*" "NVIDIA $sub"
}

$wu = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $wu) {
    Stop-Service wuauserv -Force -ErrorAction SilentlyContinue
    Hapus "$wu\*" "cache Windows Update"
    Start-Service wuauserv -ErrorAction SilentlyContinue
}

Tulis "`n[2/3] Mengosongkan Recycle Bin kedua drive ..." "Cyan"
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Tulis "      selesai" "Green"

Tulis "`nSetelah pembersihan:  C: $(BebasGB C) GB   (naik $([math]::Round((BebasGB C) - $cAwal, 2)) GB)" "White"

Tulis "`n[3/3] Memadatkan disk Docker di D: ..." "Cyan"
$skrip = Join-Path $PSScriptRoot "compact-docker-vhdx.ps1"
if (Test-Path $skrip) {
    & $skrip
} else {
    Tulis "      GAGAL: $skrip tidak ditemukan." "Red"
}

Tulis "`n=== RINGKASAN ===" "Cyan"
Tulis "  C:  $cAwal GB  ->  $(BebasGB C) GB" "Green"
Tulis "  D:  $dAwal GB  ->  $(BebasGB D) GB`n" "Green"
