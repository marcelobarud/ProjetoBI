param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dataPath = Join-Path $root '.local-postgres/data'
$logPath = Join-Path $root '.local-postgres/postgres.log'
$pgCtl = Get-Command pg_ctl.exe -ErrorAction SilentlyContinue
$pgCtlPath = if ($pgCtl -and $pgCtl.CommandType -eq 'Application') { $pgCtl.Source } else { 'D:\PostGre\bin\pg_ctl.exe' }

if (-not (Test-Path -LiteralPath (Join-Path $dataPath 'PG_VERSION') -PathType Leaf)) {
    throw 'Cluster local do ProjetoBI não foi inicializado.'
}
if (-not (Test-Path -LiteralPath $pgCtlPath -PathType Leaf)) {
    throw 'pg_ctl.exe não foi encontrado no PATH nem em D:\PostGre\bin.'
}

$pgCtlVersion = (& $pgCtlPath --version 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $pgCtlVersion -notmatch 'PostgreSQL\)?\s+18\.') { throw 'pg_ctl.exe PostgreSQL 18 não está disponível.' }
& $pgCtlPath -D $dataPath status *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Output 'A instância local do ProjetoBI já está ativa na porta 5433.'
    return
}

& $pgCtlPath -D $dataPath -l $logPath -o '-h 127.0.0.1 -p 5433' -w start
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar a instância local do ProjetoBI.' }
Write-Output 'Instância local do ProjetoBI iniciada na porta 5433.'
