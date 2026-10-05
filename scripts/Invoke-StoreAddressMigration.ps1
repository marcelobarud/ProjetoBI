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
    $databaseExists = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = 'projeto_bi';"
    if ($LASTEXITCODE -ne 0 -or -not $databaseExists) { throw 'projeto_bi não existe; nenhuma migration foi aplicada.' }

    $state = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -AtF '|' -c "SELECT current_database(), current_setting('server_version'), (SELECT count(*) FROM information_schema.columns WHERE table_schema='core' AND table_name='stores' AND column_name IN ('postal_code','street','street_number','complement','district','city','state_code','country_code')), (SELECT count(*) FROM core.stores);"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível inspecionar projeto_bi e core.stores.' }
    $parts = ($state | Select-Object -Last 1) -split '\|'
    if ($parts.Count -ne 4 -or $parts[0] -ne 'projeto_bi') { throw 'Database alvo inesperada; nenhuma migration foi aplicada.' }
    if ($parts[1] -notmatch '^18\.') { throw 'A migration exige PostgreSQL 18.x; nenhuma migration foi aplicada.' }
    $columnCount = [int]$parts[2]
    $storeCount = [int64]$parts[3]
    if ($columnCount -notin @(0, 8)) { throw 'Migration de endereço está parcial; pare para inspeção manual.' }

    if ($columnCount -eq 8) {
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        Write-Output 'Migration 002 já estava aplicada; estrutura vigente validada e nenhuma alteração foi feita.'
        return
    }

    & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
    if ($storeCount -ne 0) { throw "core.stores contém $storeCount linhas; a migration NOT NULL exige revisão. Nenhuma migration foi aplicada." }

    $migrationPath = Join-Path $root 'database/migrations/002_add_store_address.sql'
    if (-not (Test-Path -LiteralPath $migrationPath -PathType Leaf)) { throw 'Migration 002 não encontrada.' }
    & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $migrationPath
    if ($LASTEXITCODE -ne 0) { throw 'Migration 002 falhou; a transação foi revertida pelo PostgreSQL.' }

    & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
    & (Join-Path $PSScriptRoot 'Invoke-StoreAddressTest.ps1')
    Write-Output 'Migration 002 aplicada e validada; teste transacional terminou em ROLLBACK.'
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
