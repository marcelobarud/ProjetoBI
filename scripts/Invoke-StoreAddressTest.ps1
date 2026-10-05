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
    $before = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -AtF '|' -c "SELECT current_database(), count(*) FROM core.stores;"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível verificar core.stores antes do teste.' }
    $parts = ($before | Select-Object -Last 1) -split '\|'
    if ($parts[0] -ne 'projeto_bi' -or [int64]$parts[1] -ne 0) { throw 'O teste de ROLLBACK requer core.stores vazia; nenhuma linha de teste foi inserida.' }

    $testPath = Join-Path $root 'database/tests/003_store_address_rollback.sql'
    & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -f $testPath
    if ($LASTEXITCODE -ne 0) { throw 'Teste de endereço falhou; a sessão PostgreSQL reverteu a transação aberta.' }

    $after = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d projeto_bi -AtF '|' -c "SELECT current_database(), count(*) FROM core.stores;"
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível verificar core.stores após o teste.' }
    $parts = ($after | Select-Object -Last 1) -split '\|'
    if ($parts[0] -ne 'projeto_bi' -or [int64]$parts[1] -ne 0) { throw 'O teste deixou uma ou mais linhas persistidas em core.stores.' }
    Write-Output 'Teste de endereço aprovado: INSERT válido, CEP/UF/país inválidos e 7 campos obrigatórios nulos rejeitados; ROLLBACK confirmado; core.stores = 0.'
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
