Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory)]
        [string]$Label,

        [Parameter(Mandatory)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Label"
    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Write-Host "Super Mario Bros. Randomizer - developer check"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "PowerShell 7 or newer is required for this developer helper."
}

Invoke-Checked "Python version" { python --version }
Invoke-Checked "Git version" { git --version }

$pythonInfo = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
if ($LASTEXITCODE -ne 0) {
    throw "Could not query Python."
}

$parts = $pythonInfo.Trim().Split(".")
$pythonMajor = [int]$parts[0]
$pythonMinor = [int]$parts[1]

if (($pythonMajor -lt 3) -or ($pythonMajor -eq 3 -and $pythonMinor -lt 13)) {
    Write-Warning "CI targets Python 3.13 and 3.14. You are running Python $pythonInfo."
}
else {
    Write-Host "Python $pythonInfo is in the repository's CI target range."
}

Invoke-Checked "Compile sources" {
    python -m compileall -q smb1_chaos_randomizer.py tests
}

Invoke-Checked "Run unit tests" {
    python -m unittest discover -s tests -v
}

Invoke-Checked "Check CLI help" {
    python smb1_chaos_randomizer.py --help *> $null
}

Write-Host ""
Write-Host "==> Git working tree"
git status --short

Write-Host ""
Write-Host "All developer checks passed."
