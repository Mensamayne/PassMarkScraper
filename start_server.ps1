# Start PassMark Scraper API
Write-Host "🚀 Starting PassMark Scraper API..." -ForegroundColor Green
Write-Host ""

# Check if running in Docker
if (Test-Path "/.dockerenv") {
    Write-Host "Running in Docker container" -ForegroundColor Cyan
    uvicorn app.main:app --host 0.0.0.0 --port 9091
    exit
}

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Install Playwright browsers (only if not already installed)
if (!(Test-Path "$env:USERPROFILE\AppData\Local\ms-playwright")) {
    Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Yellow
    playwright install chromium
}

# Check database
if (Test-Path "benchmarks.db") {
    $dbSize = (Get-Item "benchmarks.db").Length / 1MB
    Write-Host "📊 Database found: $([math]::Round($dbSize, 2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Database not found. Run 'python scrape_all.py' to populate." -ForegroundColor Yellow
}

# Start server
Write-Host ""
Write-Host "✨ Starting FastAPI server..." -ForegroundColor Green
Write-Host "   🌐 API: http://localhost:9091" -ForegroundColor Cyan
Write-Host "   📖 Docs: http://localhost:9091/docs" -ForegroundColor Cyan
Write-Host "   🎨 Web UI: http://localhost:9091" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

uvicorn app.main:app --reload --port 9091
