param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dictionaryPath = Join-Path $root 'docs/database/data-dictionary.md'
$migrationPath = Join-Path $root 'database/migrations/001_initial_schema.sql'
$dictionaryText = Get-Content -Raw $dictionaryPath
$migrationText = Get-Content -Raw $migrationPath
$expected = @([regex]::Matches($dictionaryText, '(?m)^### ([a-z_]+\.[a-z_]+)$') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
$actual = @([regex]::Matches($migrationText, '(?m)^CREATE TABLE ([a-z_]+\.[a-z_]+)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
$expectedSchemas = @('after_sales', 'catalog', 'core', 'crm', 'inventory', 'logistics', 'payments', 'procurement', 'sales') | Sort-Object
$actualSchemas = @([regex]::Matches($migrationText, '(?m)^CREATE SCHEMA ([a-z_]+);\r?$') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
$missing = @($expected | Where-Object { $_ -notin $actual })
$unexpected = @($actual | Where-Object { $_ -notin $expected })
$missingSchemas = @($expectedSchemas | Where-Object { $_ -notin $actualSchemas })
$unexpectedSchemas = @($actualSchemas | Where-Object { $_ -notin $expectedSchemas })
if ($expected.Count -ne 40 -or $actual.Count -ne 40 -or $missing.Count -gt 0 -or $unexpected.Count -gt 0) {
    throw "Tabelas divergentes: dicionário=$($expected.Count), migration=$($actual.Count), ausentes=[$($missing -join ', ')], inesperadas=[$($unexpected -join ', ')]"
}
if ($missingSchemas.Count -gt 0 -or $unexpectedSchemas.Count -gt 0) { throw "Schemas divergentes. Ausentes=[$($missingSchemas -join ', ')], inesperados=[$($unexpectedSchemas -join ', ')]" }

$columnMismatches = [System.Collections.Generic.List[string]]::new()
$sections = [regex]::Matches($dictionaryText, '(?ms)^### ([a-z_]+\.[a-z_]+)\r?\n(.*?)(?=^### |^## |\z)')
$dictionaryColumns = @{}
foreach ($section in $sections) {
    $tableName = $section.Groups[1].Value
    $dictionaryColumns[$tableName] = @([regex]::Matches($section.Groups[2].Value, '(?m)^\| ([a-z_]+) \|') | ForEach-Object { $_.Groups[1].Value })
    $tableMatch = [regex]::Match($migrationText, "(?ms)^CREATE TABLE $([regex]::Escape($tableName)) \(\r?\n(.*?)^\);")
    if (-not $tableMatch.Success) { continue }
    foreach ($column in [regex]::Matches($section.Groups[2].Value, '(?m)^\| ([a-z_]+) \| ([^|]+) \| (Não|Sim) \|')) {
        $columnName = $column.Groups[1].Value
        $expectedType = $column.Groups[2].Value.Trim()
        $expectedNotNull = $column.Groups[3].Value -eq 'Não'
        $line = @($tableMatch.Groups[1].Value -split '\r?\n' | Where-Object { $_ -match "^\s+$([regex]::Escape($columnName))\s+" }) | Select-Object -First 1
        if (-not $line) { $columnMismatches.Add("$tableName.$columnName ausente"); continue }
        $definition = $line.Trim().TrimEnd(',')
        $definition = $definition.Substring($columnName.Length).Trim()
        $actualNotNull = $definition.EndsWith(' NOT NULL')
        if ($actualNotNull) { $definition = $definition.Substring(0, $definition.Length - ' NOT NULL'.Length).TrimEnd() }
        if ($definition -cne $expectedType -or $actualNotNull -ne $expectedNotNull) {
            $columnMismatches.Add("$tableName.$columnName esperado=[$expectedType; not_null=$expectedNotNull], migration=[$definition; not_null=$actualNotNull]")
        }
    }
}
if ($columnMismatches.Count -gt 0) { throw "Colunas divergentes entre dicionário e migration: $($columnMismatches -join '; ')" }
if ($migrationText -match 'unit_cost_snapshot|\b(FLOAT|REAL|DOUBLE PRECISION)\b|USING GIN|CREATE EXTENSION|DEFAULT\s+now\s*\(') { throw 'A migration contém referência proibida (custo legado, ponto flutuante, GIN, extensão ou default temporal).' }
$keySignatures = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($tableMatch in [regex]::Matches($migrationText, '(?ms)^CREATE TABLE ([a-z_]+\.[a-z_]+) \(\r?\n(.*?)^\);')) {
    $tableName = $tableMatch.Groups[1].Value
    $pkMatch = [regex]::Match($tableMatch.Groups[2].Value, 'CONSTRAINT pk_[a-z_]+ PRIMARY KEY \(([^)]+)\)')
    if ($pkMatch.Success) { [void]$keySignatures.Add("$tableName|$($pkMatch.Groups[1].Value -replace '\s','')") }
}
foreach ($uniqueMatch in [regex]::Matches($migrationText, '(?m)^ALTER TABLE ([a-z_]+\.[a-z_]+) ADD CONSTRAINT uq_[a-z_]+ UNIQUE \(([^)]+)\);')) {
    [void]$keySignatures.Add("$($uniqueMatch.Groups[1].Value)|$($uniqueMatch.Groups[2].Value -replace '\s','')")
}
$foreignKeyProblems = [System.Collections.Generic.List[string]]::new()
$foreignKeys = [regex]::Matches($migrationText, '(?m)^ALTER TABLE ([a-z_]+\.[a-z_]+) ADD CONSTRAINT fk_[a-z_]+ FOREIGN KEY \(([^)]+)\) REFERENCES ([a-z_]+\.[a-z_]+) \(([^)]+)\);')
foreach ($foreignKey in $foreignKeys) {
    $sourceTable = $foreignKey.Groups[1].Value
    $sourceColumns = @($foreignKey.Groups[2].Value -split ',' | ForEach-Object { $_.Trim() })
    $targetTable = $foreignKey.Groups[3].Value
    $targetColumns = @($foreignKey.Groups[4].Value -split ',' | ForEach-Object { $_.Trim() })
    foreach ($columnName in $sourceColumns) { if ($columnName -notin $dictionaryColumns[$sourceTable]) { $foreignKeyProblems.Add("FK fonte inexistente: $sourceTable.$columnName") } }
    foreach ($columnName in $targetColumns) { if ($columnName -notin $dictionaryColumns[$targetTable]) { $foreignKeyProblems.Add("FK destino inexistente: $targetTable.$columnName") } }
    $signature = "$targetTable|$(($targetColumns -join ','))"
    if (-not $keySignatures.Contains($signature)) { $foreignKeyProblems.Add("FK sem PK/UNIQUE alvo compatível: $targetTable($($targetColumns -join ', '))") }
    if ($sourceColumns.Count -ne $targetColumns.Count) { $foreignKeyProblems.Add("FK com cardinalidade de colunas incompatível: $sourceTable -> $targetTable") }
}
if ($foreignKeys.Count -ne 70 -or $foreignKeyProblems.Count -gt 0) { throw "FKs divergentes: encontradas=$($foreignKeys.Count); $($foreignKeyProblems -join '; ')" }
$expectedDdlCounts = @{
    '(?m)^\s+CONSTRAINT pk_' = 40
    '(?m)^ALTER TABLE .* ADD CONSTRAINT fk_' = 70
    '(?m)^ALTER TABLE .* ADD CONSTRAINT ck_' = 75
    '(?m)^ALTER TABLE .* ADD CONSTRAINT uq_' = 37
    '(?m)^CREATE INDEX ' = 64
    '(?m)^CREATE UNIQUE INDEX ' = 7
}
foreach ($pattern in $expectedDdlCounts.Keys) {
    $count = [regex]::Matches($migrationText, $pattern).Count
    if ($count -ne $expectedDdlCounts[$pattern]) { throw "Contagem DDL inesperada para '$pattern': esperado $($expectedDdlCounts[$pattern]), encontrado $count." }
}
if (-not $migrationText.TrimEnd().EndsWith('COMMIT;') -or -not $migrationText.StartsWith('-- ProjetoBI') -or $migrationText -notmatch '(?m)^BEGIN;\r?$') { throw 'Migration deve estar envolvida por BEGIN/COMMIT e ser identificada como migration do projeto.' }
Write-Output "Definição estática conferida: $($actualSchemas.Count) schemas, $($actual.Count) tabelas, colunas/tipos/nulabilidades e 70 FKs com destinos únicos compatíveis."
