param()

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "start-dev.ps1"
$repoRoot = Split-Path -Parent $PSScriptRoot
$alembicConfigPath = Join-Path $repoRoot "backend\alembic.ini"

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

Assert-True (Test-Path -LiteralPath $scriptPath) "scripts/start-dev.ps1 must exist"
Assert-True (Test-Path -LiteralPath $alembicConfigPath) "backend/alembic.ini must exist"

$scriptText = Get-Content -LiteralPath $scriptPath -Raw
$alembicText = Get-Content -LiteralPath $alembicConfigPath -Raw
$blockedPatterns = @(
    ".env",
    "API_KEY",
    "TOKEN",
    "PERSONAL_WIKI_NVIDIA_API_KEY",
    "PERSONAL_WIKI_OPENAI_API_KEY"
)

foreach ($pattern in $blockedPatterns) {
    Assert-True (-not $scriptText.Contains($pattern)) "start-dev.ps1 must not reference private credential pattern: $pattern"
}

$planOutput = & $scriptPath -PlanOnly -NoInstall -NoMigrations -NoOpen 2>&1 | Out-String

Assert-True ($LASTEXITCODE -eq 0) "PlanOnly mode should exit successfully"
Assert-True ($planOutput.Contains("Backend command:")) "PlanOnly output should include backend command"
Assert-True ($planOutput.Contains("Frontend command:")) "PlanOnly output should include frontend command"
Assert-True ($planOutput.Contains("Credential files and secrets are not read by this script.")) "PlanOnly output should state the privacy boundary"
Assert-True (-not $planOutput.Contains(".env")) "PlanOnly output must not mention dotenv files"
Assert-True (-not $planOutput.Contains("API_KEY")) "PlanOnly output must not mention API key names"
Assert-True (-not $planOutput.Contains("TOKEN")) "PlanOnly output must not mention token names"
Assert-True (-not $alembicText.Contains("sqlite:///./data/")) "Alembic database URL must not depend on the current working directory"
Assert-True ($alembicText.Contains("%(here)s/../data/")) "Alembic database URL should point at the repository data directory"

Write-Host "OK: start-dev.ps1 privacy-safe plan mode passed"
