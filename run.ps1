# Install dependencies and run the server (Windows)
# Usage: .\run.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& py -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    & pip install -q -r requirements.txt
}

Write-Host "Starting server at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
& py -m uvicorn main:app --host 127.0.0.1 --port 8000
