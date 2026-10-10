param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'ProjectBI.Environment.ps1')
Import-ProjectBIEnvironment
& (Join-Path $PSScriptRoot 'Test-PostgresConnection.ps1')
$psql = Resolve-ProjectBIPsql
$oldPgPassword = $env:PGPASSWORD
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
try {
    $exists = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='projeto_bi';"
    if ($LASTEXITCODE -ne 0 -or -not $exists) { throw 'Database projeto_bi ausente; migration 003 não foi aplicada.' }

    $applied = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -Atc "SELECT CASE WHEN to_regclass('sales.sales_order_item_cancellations') IS NULL THEN 0 ELSE 1 END;"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível inspecionar o estado da migration 003.' }
    if ([int]($applied | Select-Object -Last 1) -eq 1) {
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        Write-Output 'Migration 003 já aplicada; estrutura validada e nenhuma alteração feita.'
        return
    }

    # The structural guard and read-only preflight must both pass before DDL.
    & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
    $preflightPath = Join-Path $root 'database/tests/004_partial_cancellation_preflight.sql'
    & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $preflightPath
    if ($LASTEXITCODE -ne 0) { throw 'Preflight da migration 003 falhou; nenhuma alteração foi aplicada.' }

    $migrationPath = Join-Path $root 'database/migrations/003_partial_item_cancellations.sql'
    & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $migrationPath
    if ($LASTEXITCODE -ne 0) { throw 'Migration 003 falhou; a transação DDL foi revertida pelo PostgreSQL.' }
    & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
    Write-Output 'Migration 003 aplicada e estrutura homologada.'
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
