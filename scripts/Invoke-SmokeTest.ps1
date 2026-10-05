param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'Test-PostgresConnection.ps1')
& (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
$psql = (Get-Command psql).Source
$oldPgPassword = $env:PGPASSWORD
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
try {
    $smokePath = Join-Path $root 'database/tests/002_smoke_rollback.sql'
    & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $smokePath
    if ($LASTEXITCODE -ne 0) { throw 'Smoke test falhou; a sessão PostgreSQL encerrou e reverteu a transação aberta.' }
    Write-Output 'Smoke test executado; a transação terminou em ROLLBACK e não deixou linhas permanentes.'
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
