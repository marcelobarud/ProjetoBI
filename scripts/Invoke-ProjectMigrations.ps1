param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'Test-SchemaDefinition.ps1')
& (Join-Path $PSScriptRoot 'Test-PostgresConnection.ps1')
$psql = (Get-Command psql).Source
$migrationFiles = @(Get-ChildItem (Join-Path $root 'database/migrations') -Filter '*.sql' -File | Sort-Object Name)
if ($migrationFiles.Count -eq 0) { throw 'Nenhuma migration encontrada.' }
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
    }
    else {
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        Write-Output 'Estrutura já está aplicada e foi validada; nenhuma migration repetida.'
    }
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
