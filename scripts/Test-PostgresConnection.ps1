param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ProjectBI.Environment.ps1')
Import-ProjectBIEnvironment

$required = @('POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD')
$missing = @($required | Where-Object { [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_)) })
if ($missing.Count -gt 0) { throw "Variáveis ausentes: $($missing -join ', '). Configure-as no ambiente local." }
if ($env:POSTGRES_DB -ne 'projeto_bi') { throw 'POSTGRES_DB deve ser projeto_bi.' }
if ($env:POSTGRES_PORT -notmatch '^\d{1,5}$' -or [int]$env:POSTGRES_PORT -lt 1 -or [int]$env:POSTGRES_PORT -gt 65535) { throw 'POSTGRES_PORT deve ser uma porta TCP válida.' }

$psql = Resolve-ProjectBIPsql

$oldPgPassword = $env:PGPASSWORD
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
try {
    $versionNumber = & $psql -X -w -v ON_ERROR_STOP=1 -h $env:POSTGRES_HOST -p $env:POSTGRES_PORT -U $env:POSTGRES_USER -d postgres -Atc 'SHOW server_version_num;'
    if ($LASTEXITCODE -ne 0) { throw 'Falha de conexão à database administrativa postgres.' }
    $versionNumber = [int]($versionNumber | Select-Object -Last 1)
    if ($versionNumber -lt 180000 -or $versionNumber -ge 190000) { throw "PostgreSQL incompatível (server_version_num=$versionNumber). A implementação exige PostgreSQL 18; nenhum objeto foi alterado." }
    Write-Output "Conexão confirmada. PostgreSQL 18; database administrativa postgres."
}
finally {
    $env:PGPASSWORD = $oldPgPassword
}
