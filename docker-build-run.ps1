# Build and run PassMark Scraper in Docker
Write-Host "🐳 Building Docker image..." -ForegroundColor Green

# Build image
docker build -t passmark-scraper .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image built successfully" -ForegroundColor Green
Write-Host ""

# Stop and remove existing container
Write-Host "🛑 Stopping existing container..." -ForegroundColor Yellow
docker stop passmark-scraper 2>$null
docker rm passmark-scraper 2>$null

# Run container
Write-Host "🚀 Starting container..." -ForegroundColor Green
docker run -d `
    --name passmark-scraper `
    -p 9091:9091 `
    -v ${PWD}/benchmarks.db:/app/benchmarks.db `
    -v ${PWD}/logs:/app/logs `
    -v ${PWD}/config:/app/config:ro `
    -e PYTHONUNBUFFERED=1 `
    passmark-scraper

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✨ Container started successfully!" -ForegroundColor Green
Write-Host "   🌐 API: http://localhost:9091" -ForegroundColor Cyan
Write-Host "   📖 Docs: http://localhost:9091/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 View logs: docker logs -f passmark-scraper" -ForegroundColor Gray
Write-Host "🛑 Stop: docker stop passmark-scraper" -ForegroundColor Gray

