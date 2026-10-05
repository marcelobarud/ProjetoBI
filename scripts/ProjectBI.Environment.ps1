$script:ProjectBIRoot = Split-Path -Parent $PSScriptRoot

function Import-ProjectBIEnvironment {
    $envFile = Join-Path $script:ProjectBIRoot '.env'
    if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) { return }

    $supportedNames = @(
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_PSQL_PATH'
    )

    foreach ($line in Get-Content -LiteralPath $envFile) {
        $text = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($text) -or $text.StartsWith('#')) { continue }

        $separator = $text.IndexOf('=')
        if ($separator -lt 0) { continue }

        $name = $text.Substring(0, $separator).Trim()
        if ($name -notin $supportedNames) { continue }
        if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, 'Process'))) { continue }

        $value = $text.Substring($separator + 1).Trim()
        if ($value.Length -ge 2) {
            $first = $value[0]
            $last = $value[$value.Length - 1]
            if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
                $value = $value.Substring(1, $value.Length - 2)
            }
        }
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

function Resolve-ProjectBIPsql {
    $candidates = [System.Collections.Generic.List[string]]::new()
    $configuredPath = [Environment]::GetEnvironmentVariable('POSTGRES_PSQL_PATH', 'Process')
    if (-not [string]::IsNullOrWhiteSpace($configuredPath)) { $candidates.Add($configuredPath.Trim('"')) }

    $pathCommand = Get-Command psql -ErrorAction SilentlyContinue
    if ($pathCommand -and $pathCommand.CommandType -eq 'Application') { $candidates.Add($pathCommand.Source) }

    $postgresRoot = 'C:\Program Files\PostgreSQL'
    $version18Root = Join-Path $postgresRoot '18'
    $standardPath = Join-Path $version18Root 'bin\psql.exe'
    $candidates.Add($standardPath)

    if (Test-Path -LiteralPath $postgresRoot -PathType Container) {
        $version18Prefix = $version18Root.TrimEnd('\') + '\'
        Get-ChildItem -LiteralPath $postgresRoot -Filter 'psql.exe' -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName.StartsWith($version18Prefix, [StringComparison]::OrdinalIgnoreCase) } |
            ForEach-Object { $candidates.Add($_.FullName) }
    }

    $seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate) -or -not $seen.Add($candidate)) { continue }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf) -or [IO.Path]::GetExtension($candidate) -ine '.exe') { continue }

        $versionText = (& $candidate --version 2>$null | Out-String).Trim()
        if ($LASTEXITCODE -eq 0 -and $versionText -match 'PostgreSQL\)?\s+(\d+)') {
            if ([int]$Matches[1] -eq 18) { return (Resolve-Path -LiteralPath $candidate).Path }
        }
    }

    throw 'Cliente psql PostgreSQL 18 não encontrado. Configure POSTGRES_PSQL_PATH, disponibilize-o no PATH ou instale o cliente PostgreSQL 18.'
}
