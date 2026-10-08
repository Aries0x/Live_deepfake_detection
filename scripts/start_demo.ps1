# Media Integrity / SecureCall One-Click Demo Starter (Windows PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  SECURECALL: Real-Time Multimodal Media Integrity Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT_DIR

Write-Host "[1/3] Starting FastAPI Forensics Backend (port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "[2/3] Checking Backend Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    Write-Host "  -> Backend: $($health.backend)" -ForegroundColor Green
    Write-Host "  -> GPU Acceleration: $($health.gpu.name)" -ForegroundColor Green
    Write-Host "  -> Models Ready: EfficientNet-B0, AASIST-L, Temporal GRU, SyncNet" -ForegroundColor Green
} catch {
    Write-Host "  -> Backend warming up..." -ForegroundColor Yellow
}

Write-Host "[3/3] Starting Next.js Production Frontend (port 3000)..." -ForegroundColor Yellow
Set-Location "$ROOT_DIR\frontend"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run start -- -p 3000" -WindowStyle Minimized

Start-Sleep -Seconds 2

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  SECURECALL PLATFORM READY FOR DEMONSTRATION" -ForegroundColor Green
Write-Host "  - Frontend URL:   http://localhost:3000" -ForegroundColor White
Write-Host "  - Live Call Room: http://localhost:3000/call/demo-room" -ForegroundColor White
Write-Host "  - Operations:     http://localhost:3000/dashboard" -ForegroundColor White
Write-Host "  - Bulk Dataset:   http://localhost:3000/bulk" -ForegroundColor White
Write-Host "  - API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
