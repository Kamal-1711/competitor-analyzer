# Backend Startup Script
# This script starts the FastAPI backend server

Write-Host "Starting Competitor Analyzer Backend..." -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\backend"

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Install Playwright browsers if needed
Write-Host "Ensuring Playwright browsers are installed..." -ForegroundColor Yellow
python -m playwright install chromium

# Start the server
Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Green
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
