$ErrorActionPreference = "Stop"

$Bin     = "C:\Program Files\MySQL\MySQL Server 8.0\bin"
$Ini     = "C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"
$InitSql = "D:\BDA\docker\mysql-init.sql"
$Secret  = "D:\BDA\nb\bda_secret.json"
$Service = "MySQL80"

function Info($m) { Write-Host "  $m" }

$pr = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "GAGAL: skrip ini harus dijalankan sebagai Administrator." -ForegroundColor Red
    Write-Host "  Klik kanan Start -> Terminal (Admin), lalu jalankan ulang."
    exit 1
}

foreach ($f in @("$Bin\mysqld.exe", "$Bin\mysql.exe", $Ini, $InitSql, $Secret)) {
    if (-not (Test-Path $f)) { Write-Host "GAGAL: tidak ada $f" -ForegroundColor Red; exit 1 }
}

$pw = (Get-Content $Secret -Raw | ConvertFrom-Json).mysql.password
$user = (Get-Content $Secret -Raw | ConvertFrom-Json).mysql.user
Info "User target   : $user"
Info "Password      : $($pw.Length) karakter (dibaca dari bda_secret.json)"
Info "Skrip SQL     : $InitSql"
Write-Host ""

Info "Menghentikan service $Service ..."
if ((Get-Service $Service).Status -eq "Running") {
    Stop-Service $Service -Force
    (Get-Service $Service).WaitForStatus("Stopped", "00:01:00")
}
Info "  service berhenti"

Info "Menjalankan mysqld dengan --init-file (proses sementara) ..."
$p = Start-Process -FilePath "$Bin\mysqld.exe" `
        -ArgumentList "--defaults-file=`"$Ini`"", "--init-file=`"$InitSql`"", "--console" `
        -PassThru -WindowStyle Hidden

$ok = $false
for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Seconds 3
    $null = & "$Bin\mysql.exe" -u root -p"$pw" -e "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    if ($p.HasExited) { break }
}

if ($ok) { Info "  perintah SQL berhasil dijalankan ($($i*3) detik)" }
else     { Info "  peringatan: belum bisa memverifikasi, tetap dilanjutkan" }

Info "Mematikan proses sementara ..."
if (-not $p.HasExited) {
    & "$Bin\mysqladmin.exe" -u root -p"$pw" shutdown 2>&1 | Out-Null
    Start-Sleep -Seconds 5
    if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
}
Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Info "  proses sementara berhenti"

Info "Menyalakan kembali service $Service ..."
Start-Service $Service
(Get-Service $Service).WaitForStatus("Running", "00:01:00")
Start-Sleep -Seconds 5
Info "  service berjalan"
Write-Host ""

Write-Host "VERIFIKASI" -ForegroundColor Cyan
$r1 = & "$Bin\mysql.exe" -u root -p"$pw" -e "SELECT VERSION();" 2>&1
Info "root                : $(if($LASTEXITCODE -eq 0){'BISA'}else{'gagal'})"

$r2 = & "$Bin\mysql.exe" -u $user -p"$pw" -h 127.0.0.1 -e "SELECT DATABASE();" bda_influenza 2>&1
Info "$user lewat TCP        : $(if($LASTEXITCODE -eq 0){'BISA'}else{'gagal'})"

$r3 = & "$Bin\mysql.exe" -u root -p"$pw" -N -B -e `
      "SELECT CONCAT(user,'@',host) FROM mysql.user WHERE user IN ('root','$user');" 2>&1
Info "akun yang ada       : $($r3 -join ', ')"

$r4 = & "$Bin\mysql.exe" -u root -p"$pw" -N -B -e `
      "SHOW DATABASES LIKE 'bda_influenza';" 2>&1
Info "database            : $(if($r4){'bda_influenza ADA'}else{'BELUM ADA'})"

Write-Host ""
Write-Host "Selesai. Jalankan ulang sel MySQL di notebook 00 untuk memastikan." -ForegroundColor Green
