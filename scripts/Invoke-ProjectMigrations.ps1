param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'ProjectBI.Environment.ps1')
Import-ProjectBIEnvironment
& (Join-Path $PSScriptRoot 'Test-SchemaDefinition.ps1')
& (Join-Path $PSScriptRoot 'Test-PostgresConnection.ps1')
$psql = Resolve-ProjectBIPsql
$migrationFiles = @(Get-ChildItem (Join-Path $root 'database/migrations') -Filter '*.sql' -File | Sort-Object Name)
if ($migrationFiles.Count -eq 0) { throw 'Nenhuma migration encontrada.' }
$expectedMigrationNames = @('001_initial_schema.sql', '002_add_store_address.sql', '003_partial_item_cancellations.sql')
if (($migrationFiles.Name -join '|') -ne ($expectedMigrationNames -join '|')) {
    throw 'O runner atual suporta explicitamente as migrations 001, 002 e 003. Revise o fluxo antes de adicionar outra migration.'
}
$oldPgPassword = $env:PGPASSWORD
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
try {
    $databaseExists = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = 'projeto_bi';"
    if ($LASTEXITCODE -ne 0 -or -not $databaseExists) { throw 'projeto_bi não existe. Execute Initialize-ProjectDatabase.ps1 primeiro.' }
    $counts = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -AtF ',' -c "SELECT (SELECT count(*) FROM pg_namespace WHERE nspname NOT LIKE 'pg\_%' ESCAPE '\' AND nspname NOT IN ('information_schema','public')), (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname NOT LIKE 'pg\_%' ESCAPE '\' AND n.nspname <> 'information_schema');"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível inspecionar a database alvo.' }
    $parts = ($counts | Select-Object -Last 1) -split ','
    if ([int]$parts[0] -eq 0 -and [int]$parts[1] -eq 0) {
        foreach ($file in $migrationFiles) {
            Write-Output "Aplicando $($file.Name)..."
            & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $file.FullName
            if ($LASTEXITCODE -ne 0) { throw "Migration $($file.Name) falhou; a transação deve ter sido revertida." }
        }
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        Write-Output 'Bootstrap concluído: migrations 001, 002 e 003 aplicadas e validadas.'
    }
    else {
        $storeAddressColumnCount = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -Atc "SELECT count(*) FROM information_schema.columns WHERE table_schema='core' AND table_name='stores' AND column_name IN ('postal_code','street','street_number','complement','district','city','state_code','country_code');"
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível determinar a versão do schema de core.stores.' }
        $storeAddressColumnCount = [int]($storeAddressColumnCount | Select-Object -Last 1)
        if ($storeAddressColumnCount -notin @(0, 8)) { throw 'Schema de endereço de core.stores está parcial; nenhuma migration foi executada.' }
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        if ($storeAddressColumnCount -eq 0) {
            & (Join-Path $PSScriptRoot 'Invoke-StoreAddressMigration.ps1')
            & (Join-Path $PSScriptRoot 'Invoke-PartialCancellationMigration.ps1')
        }
        else {
            & (Join-Path $PSScriptRoot 'Invoke-PartialCancellationMigration.ps1')
        }
    }
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
