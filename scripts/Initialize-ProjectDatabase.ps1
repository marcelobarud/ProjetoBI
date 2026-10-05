param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'Test-PostgresConnection.ps1')
$psql = (Get-Command psql).Source
$oldPgPassword = $env:PGPASSWORD
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
try {
    $exists = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = 'projeto_bi';"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível verificar a database alvo.' }
    if (-not $exists) {
        $createdb = Get-Command createdb -ErrorAction SilentlyContinue
        if (-not $createdb) { throw 'createdb não foi encontrado no PATH. Nenhuma database foi criada.' }
        & $createdb.Source -w -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER projeto_bi
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar projeto_bi. Verifique as permissões do usuário.' }
        Write-Output 'Database projeto_bi criada vazia.'
        return
    }

    $counts = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -AtF ',' -c "SELECT (SELECT count(*) FROM pg_namespace WHERE nspname NOT LIKE 'pg\_%' ESCAPE '\' AND nspname NOT IN ('information_schema','public')), (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname NOT LIKE 'pg\_%' ESCAPE '\' AND n.nspname <> 'information_schema');"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível inspecionar os objetos da database existente.' }
    $parts = ($counts | Select-Object -Last 1) -split ','
    if ([int]$parts[0] -eq 0 -and [int]$parts[1] -eq 0) { Write-Output 'Database projeto_bi já existe e está vazia; preservada.'; return }

    try {
        & (Join-Path $PSScriptRoot 'Invoke-DatabaseValidation.ps1')
        Write-Output 'Database projeto_bi já contém o esquema esperado; preservada.'
    }
    catch {
        throw 'projeto_bi já existe e contém objetos que não foram reconhecidos como a estrutura completa esperada. Nenhum objeto foi alterado. Inspecione a database antes de continuar.'
    }
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
