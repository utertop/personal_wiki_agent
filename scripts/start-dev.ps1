param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [string]$ConfigPath = "config\sources.example.yaml",
    [Alias("SkipInstall")]
    [switch]$NoInstall,
    [Alias("SkipMigrations")]
    [switch]$NoMigrations,
    [switch]$Open,
    [switch]$NoOpen,
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $RepoRoot "backend"
$FrontendRoot = Join-Path $RepoRoot "frontend"
$StateRoot = Join-Path $RepoRoot ".codex_tmp\start-dev"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
$BackendLog = Join-Path $StateRoot "backend.log"
$BackendErr = Join-Path $StateRoot "backend.err.log"
$FrontendLog = Join-Path $StateRoot "frontend.log"
$FrontendErr = Join-Path $StateRoot "frontend.err.log"
$AlembicConfig = Join-Path $BackendRoot "alembic.ini"
$StartedProcesses = New-Object System.Collections.Generic.List[System.Diagnostics.Process]

function Write-Step {
    param([string]$Message)
    Write-Output "[start-dev] $Message"
}

function Resolve-ProjectPath {
    param([string]$Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $Path))
}

function Read-JsonFile {
    param([string]$Path)

    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-DependencyHash {
    param([string[]]$Paths)

    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($path in $Paths) {
        if (Test-Path -LiteralPath $path) {
            $hash = Get-FileHash -LiteralPath $path -Algorithm SHA256
            $parts.Add("$path=$($hash.Hash)")
        }
    }

    $text = [string]::Join("`n", $parts)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Test-HashMarker {
    param(
        [string]$MarkerPath,
        [string]$ExpectedHash
    )

    if (-not (Test-Path -LiteralPath $MarkerPath)) {
        return $false
    }

    $stored = (Get-Content -LiteralPath $MarkerPath -Raw).Trim()
    return $stored -eq $ExpectedHash
}

function Save-HashMarker {
    param(
        [string]$MarkerPath,
        [string]$Hash
    )

    $parent = Split-Path -Parent $MarkerPath
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Set-Content -LiteralPath $MarkerPath -Value $Hash -Encoding ASCII
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Write-Step "$FilePath $($Arguments -join ' ')"
    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Ensure-BackendDependencies {
    if ($NoInstall) {
        Write-Step "Backend install skipped"
        return
    }

    $pyproject = Join-Path $BackendRoot "pyproject.toml"
    $marker = Join-Path $StateRoot "backend-deps.sha256"
    $hash = Get-DependencyHash @($pyproject)

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Step "Creating Python virtual environment"
        Invoke-Checked "python" @("-m", "venv", ".venv") $RepoRoot
    }

    if (Test-HashMarker $marker $hash) {
        Write-Step "Backend dependencies are current"
        return
    }

    Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip") $RepoRoot
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-e", ".\backend[dev]") $RepoRoot
    Save-HashMarker $marker $hash
}

function Ensure-FrontendDependencies {
    if ($NoInstall) {
        Write-Step "Frontend install skipped"
        return
    }

    $packageJson = Join-Path $FrontendRoot "package.json"
    $packageLock = Join-Path $FrontendRoot "package-lock.json"
    $nodeModules = Join-Path $FrontendRoot "node_modules"
    $marker = Join-Path $StateRoot "frontend-deps.sha256"
    $hash = Get-DependencyHash @($packageJson, $packageLock)

    if ((Test-Path -LiteralPath $nodeModules) -and (Test-HashMarker $marker $hash)) {
        Write-Step "Frontend dependencies are current"
        return
    }

    $installCommand = if (Test-Path -LiteralPath $packageLock) { "install" } else { "install" }
    Invoke-Checked "npm.cmd" @($installCommand) $FrontendRoot
    Save-HashMarker $marker $hash
}

function Invoke-Migrations {
    if ($NoMigrations) {
        Write-Step "Database migrations skipped"
        return
    }

    Invoke-Checked $VenvPython @("-m", "alembic", "-c", $AlembicConfig, "upgrade", "head") $RepoRoot
}

function Get-FrontendDevCommand {
    $packageJsonPath = Join-Path $FrontendRoot "package.json"
    $packageJson = Read-JsonFile $packageJsonPath
    if (-not $packageJson.scripts.dev) {
        throw "frontend/package.json must define scripts.dev"
    }

    return @("run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort")
}

function Wait-HttpReady {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Step "$Name is ready: $Url"
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "$Name did not become ready within $TimeoutSeconds seconds: $Url"
}

function Start-ManagedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$OutputLog,
        [string]$ErrorLog
    )

    Write-Step "Starting $Name"
    Write-Step "$Name logs: $OutputLog"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $OutputLog `
        -RedirectStandardError $ErrorLog `
        -WindowStyle Hidden `
        -PassThru
    $StartedProcesses.Add($process)
    return $process
}

function Stop-ManagedProcesses {
    foreach ($process in $StartedProcesses) {
        if ($null -ne $process -and -not $process.HasExited) {
            Write-Step "Stopping process $($process.Id)"
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

$ResolvedConfigPath = Resolve-ProjectPath $ConfigPath
$BackendArguments = @(
    "-m", "uvicorn",
    "app.main:app",
    "--app-dir", "backend",
    "--host", "127.0.0.1",
    "--port", "$BackendPort",
    "--reload"
)
$FrontendArguments = Get-FrontendDevCommand

if ($PlanOnly) {
    Write-Step "Repository: $RepoRoot"
    Write-Step "Config: $ResolvedConfigPath"
    Write-Step "Backend URL: $BackendUrl"
    Write-Step "Frontend URL: $FrontendUrl"
    Write-Step "Backend command: $VenvPython $($BackendArguments -join ' ')"
    Write-Step "Frontend command: npm.cmd $($FrontendArguments -join ' ')"
    Write-Step "Credential files and secrets are not read by this script."
    exit 0
}

New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $ResolvedConfigPath)) {
    throw "Config file not found: $ResolvedConfigPath"
}

$PreviousConfigPath = [Environment]::GetEnvironmentVariable("PERSONAL_WIKI_CONFIG_PATH", "Process")
$PreviousApiBase = [Environment]::GetEnvironmentVariable("VITE_API_BASE_URL", "Process")

try {
    [Environment]::SetEnvironmentVariable("PERSONAL_WIKI_CONFIG_PATH", $ResolvedConfigPath, "Process")
    [Environment]::SetEnvironmentVariable("VITE_API_BASE_URL", $BackendUrl, "Process")

    Ensure-BackendDependencies
    Ensure-FrontendDependencies
    Invoke-Migrations

    Start-ManagedProcess "backend" $VenvPython $BackendArguments $RepoRoot $BackendLog $BackendErr | Out-Null
    Wait-HttpReady "Backend" "$BackendUrl/health"

    Start-ManagedProcess "frontend" "npm.cmd" $FrontendArguments $FrontendRoot $FrontendLog $FrontendErr | Out-Null
    Wait-HttpReady "Frontend" $FrontendUrl

    Write-Step "Ready for practical use"
    Write-Step "Backend: $BackendUrl"
    Write-Step "Frontend: $FrontendUrl"
    Write-Step "If real model calls fail, check your local model credential configuration."

    if ($Open -and -not $NoOpen) {
        Start-Process $FrontendUrl | Out-Null
    }

    Write-Step "Press Ctrl+C to stop backend and frontend"
    while ($true) {
        foreach ($process in $StartedProcesses) {
            if ($process.HasExited) {
                throw "Managed process exited unexpectedly with code $($process.ExitCode). Check logs in $StateRoot"
            }
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    [Environment]::SetEnvironmentVariable("PERSONAL_WIKI_CONFIG_PATH", $PreviousConfigPath, "Process")
    [Environment]::SetEnvironmentVariable("VITE_API_BASE_URL", $PreviousApiBase, "Process")
    Stop-ManagedProcesses
}
