# PassMark Scraper - Complete Tutorial

This tutorial will guide you through using the PassMark Scraper microservice, from basic setup to advanced usage.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Using the Web Interface](#using-the-web-interface)
3. [Using the API](#using-the-api)
4. [Scraping Data](#scraping-data)
5. [Database Management](#database-management)
6. [Docker Deployment](#docker-deployment)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation Methods

#### Method 1: Docker (Recommended)

```bash
# Clone or navigate to project directory
cd PassMarkScraper

# Build and start container
docker-compose up -d

# Check if running
docker-compose ps
```

The service will be available at http://localhost:9091

#### Method 2: Manual Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Start the server
uvicorn app.main:app --port 9091 --reload
```

### Initial Setup

1. **Check service health:**
```bash
curl http://localhost:9091/health
```

Expected response:
```json
{
  "status": "ok",
  "db_path": "benchmarks.db",
  "db_exists": true,
  "db_count": 16950
}
```

2. **If database is empty**, populate it:
```bash
python scrape_all.py
```

This will take 10-15 minutes to scrape ~20,000 components.

---

## Using the Web Interface

### Accessing the UI

Open your browser and navigate to:
```
http://localhost:9091
```

### Basic Comparison

1. **Enter Component Names**
   - Component 1: `GTX 760A`
   - Component 2: `RTX 3050`
   - Type: Leave as "Auto-detect" or select "GPU"

2. **Click "Compare"**

3. **View Results**
   - Winner highlighted in purple
   - Performance difference shown as percentage
   - Detailed stats for each component
   - Tier badges (low/mid/high/ultra)

### Example Comparisons

#### Old vs New CPU
- Component 1: `i7-2630UM`
- Component 2: `i9-8950HK`
- Result: i9 is **2498% faster**

#### Budget GPU vs Mid-Range
- Component 1: `GTX 1650`
- Component 2: `RTX 3060`
- Result: RTX 3060 is **~80% faster**

#### SSD vs HDD
- Component 1: `WD Blue 1TB HDD`
- Component 2: `Samsung 970 EVO`
- Result: SSD is **~500% faster**

### Tips for Better Results

1. **Use partial names** - "RTX 3050" will match "GeForce RTX 3050 8GB"
2. **Omit manufacturer** - "3080" works as well as "RTX 3080"
3. **Check spelling** - Minor typos might not find components
4. **Use type filter** - Helps when similar names exist across types

---

## Using the API

### Basic API Calls

#### 1. Search for a Component

```bash
curl "http://localhost:9091/search?name=RTX+3080&type=GPU"
```

Response:
```json
{
  "found": true,
  "component": {
    "name": "GeForce RTX 3080",
    "passmark_score": 25251,
    "normalized_score": 92,
    "tier": "ultra",
    "category": "consumer"
  }
}
```

#### 2. Compare Two Components

```bash
curl "http://localhost:9091/compare?component1=i5-10400&component2=i7-10700&type=CPU"
```

Response:
```json
{
  "found": true,
  "winner": "component2",
  "better_by_percent": 35.2,
  "component1": {
    "name": "Intel Core i5-10400 @ 2.90GHz",
    "passmark_score": 12249,
    "normalized_score": 55,
    "tier": "mid"
  },
  "component2": {
    "name": "Intel Core i7-10700 @ 2.90GHz",
    "passmark_score": 16564,
    "normalized_score": 70,
    "tier": "high"
  },
  "comparison": {
    "passmark_difference": 4315,
    "passmark_difference_percent": 35.2,
    "normalized_difference": 15
  }
}
```

#### 3. List Top Components

```bash
curl "http://localhost:9091/list?type=GPU&limit=10&category=consumer"
```

Response:
```json
{
  "type": "GPU",
  "category": "consumer",
  "count": 10,
  "components": [
    {
      "name": "GeForce RTX 4090",
      "passmark_score": 35888,
      "tier": "ultra"
    },
    ...
  ]
}
```

### API Integration Examples

#### Python

```python
import requests

def compare_components(comp1, comp2, comp_type=""):
    url = "http://localhost:9091/compare"
    params = {
        "component1": comp1,
        "component2": comp2
    }
    if comp_type:
        params["type"] = comp_type
    
    response = requests.get(url, params=params)
    return response.json()

# Usage
result = compare_components("GTX 1080", "RTX 3060")
print(f"Winner: {result['winner']}")
print(f"Performance gain: {result['better_by_percent']}%")
```

#### JavaScript/Node.js

```javascript
async function compareComponents(comp1, comp2, type = '') {
  const params = new URLSearchParams({
    component1: comp1,
    component2: comp2
  });
  if (type) params.append('type', type);
  
  const response = await fetch(`http://localhost:9091/compare?${params}`);
  return await response.json();
}

// Usage
const result = await compareComponents('i5-12400', 'i7-12700');
console.log(`Winner: ${result.winner}`);
console.log(`Performance gain: ${result.better_by_percent}%`);
```

#### cURL Scripts

```bash
#!/bin/bash
# compare.sh - Quick comparison script

COMP1=$1
COMP2=$2
TYPE=${3:-""}

if [ -z "$COMP1" ] || [ -z "$COMP2" ]; then
  echo "Usage: ./compare.sh <component1> <component2> [type]"
  exit 1
fi

curl -s "http://localhost:9091/compare?component1=$COMP1&component2=$COMP2&type=$TYPE" | jq
```

Usage:
```bash
./compare.sh "RTX 3070" "RTX 4070" "GPU"
```

---

## Scraping Data

### Understanding Scraping Modes

#### Full Lists Mode (`use_full_lists: true`)
- Scrapes **ALL** components from PassMark (~22,000)
- Includes: old CPUs, mobile GPUs, embedded processors, all storage devices
- Takes: 10-15 minutes
- Database size: ~5MB

#### High-End Mode (`use_full_lists: false`)
- Scrapes only **high-end** components (~1,000)
- Includes: recent CPUs, gaming GPUs, modern storage
- Takes: 2-3 minutes
- Database size: ~1MB

### Configuration

Edit `config/config.json`:

```json
{
  "scraping": {
    "use_full_lists": true,
    "limits": {
      "cpu": -1,
      "gpu": -1,
      "ram": -1,
      "storage": -1
    },
    "include_workstation": false
  }
}
```

**Options:**
- `use_full_lists`: `true` = all components, `false` = high-end only
- `limits`: `-1` = no limit, `100` = top 100 components
- `include_workstation`: `false` = exclude workstation components

### Running the Scraper

#### Full Scrape (All Component Types)

```bash
python scrape_all.py
```

Output:
```
============================================================
  SCRAPOWANIE WSZYSTKICH KOMPONENTÓW
============================================================

[*] Scrapuje GPU (WSZYSTKIE)...
    Pobrano: 2785 komponentów
   [OK] Zapisane: 2537 | Pominięte: 248

[*] Scrapuje CPU (WSZYSTKIE)...
    Pobrano: 5394 komponentów
   [OK] Zapisane: 1424 | Pominięte: 3970

...
```

#### Selective Scraping via API

```bash
# Scrape only GPUs
curl -X POST "http://localhost:9091/scrape-and-save?type=GPU&limit=100&include_workstation=false"
```

### What Gets Filtered?

The scraper automatically filters:
1. **Server components** - Xeon, EPYC, Quadro server editions
2. **Workstation components** (if `include_workstation: false`) - Threadripper, Quadro
3. **Invalid entries** - Components with unreasonable scores

---

## Database Management

### Inspecting the Database

```bash
# Connect to database
sqlite3 benchmarks.db

# Show component count
SELECT COUNT(*) FROM component_benchmarks;

# Show components by type
SELECT component_type, COUNT(*) 
FROM component_benchmarks 
GROUP BY component_type;

# Find specific component
SELECT * FROM component_benchmarks 
WHERE name LIKE '%RTX 3080%';

# Top 10 CPUs
SELECT name, passmark_score 
FROM component_benchmarks 
WHERE component_type='CPU' 
ORDER BY passmark_score DESC 
LIMIT 10;
```

### Database Schema

```sql
CREATE TABLE component_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    component_type TEXT NOT NULL,
    category TEXT,
    passmark_score INTEGER NOT NULL,
    normalized_score INTEGER NOT NULL,
    tier TEXT,
    tdp INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_name ON component_benchmarks(normalized_name);
CREATE INDEX idx_type ON component_benchmarks(component_type);
```

### Backup and Restore

#### Backup
```bash
# Copy database file
cp benchmarks.db benchmarks_backup_$(date +%Y%m%d).db

# Or export to SQL
sqlite3 benchmarks.db .dump > backup.sql
```

#### Restore
```bash
# From backup file
cp benchmarks_backup_20251012.db benchmarks.db

# From SQL dump
sqlite3 benchmarks.db < backup.sql
```

### Cleaning Database

```bash
# Remove old components (optional)
sqlite3 benchmarks.db "DELETE FROM component_benchmarks WHERE scraped_at < date('now', '-90 days');"

# Vacuum to reclaim space
sqlite3 benchmarks.db "VACUUM;"
```

---

## Docker Deployment

### Basic Deployment

```bash
# Build image
docker-compose build

# Start service
docker-compose up -d

# View logs
docker-compose logs -f passmark-api

# Stop service
docker-compose down
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  passmark-api:
    build: .
    container_name: passmark-scraper
    ports:
      - "9091:9091"
    volumes:
      - ./benchmarks.db:/app/benchmarks.db
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Volume Management

The database and logs are persisted using volumes:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect passmarkscraper_db_data

# Backup database from container
docker cp passmark-scraper:/app/benchmarks.db ./backup/

# Restore database to container
docker cp ./backup/benchmarks.db passmark-scraper:/app/
```

### Production Deployment

For production, consider:

1. **Use environment variables** for configuration
2. **Enable HTTPS** with reverse proxy (nginx, traefik)
3. **Set resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```
4. **Enable logging** to external service
5. **Regular backups** of database
6. **Monitoring** with health checks

---

## Advanced Usage

### Custom Filtering

Create custom filters in `app/filters.py`:

```python
def custom_filter(component_name: str) -> bool:
    """Custom filter logic."""
    # Only include RTX series
    if 'RTX' in component_name:
        return True
    # Exclude mobile
    if 'Mobile' in component_name:
        return False
    return True
```

### Batch Comparisons

Compare multiple components:

```python
import requests

components = ['RTX 3060', 'RTX 3070', 'RTX 3080', 'RTX 3090']
reference = 'GTX 1080 Ti'

for comp in components:
    result = requests.get(
        'http://localhost:9091/compare',
        params={'component1': reference, 'component2': comp}
    ).json()
    
    if result['found']:
        print(f"{comp}: {result['better_by_percent']}% faster than {reference}")
```

### Custom Normalization

Modify normalization in `app/normalizer.py`:

```python
def normalize_cpu_score(passmark_score: int) -> int:
    """Custom CPU normalization."""
    # Your custom logic here
    if passmark_score < 1000:
        return 0
    elif passmark_score > 40000:
        return 100
    else:
        return int((passmark_score - 1000) / 390)
```

### API Rate Limiting

Add rate limiting with FastAPI:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/compare")
@limiter.limit("10/minute")
async def compare_components(...):
    ...
```

---

## Troubleshooting

### Common Issues

#### 1. "Component not found"

**Problem:** API returns `"found": false`

**Solutions:**
- Check spelling
- Try partial name ("3080" instead of "RTX 3080")
- Verify component exists: `sqlite3 benchmarks.db "SELECT name FROM component_benchmarks WHERE name LIKE '%3080%';"`
- Rescrape if database is outdated

#### 2. Empty database

**Problem:** `db_count: 0` in health check

**Solution:**
```bash
# Populate database
python scrape_all.py

# Or via API
curl -X POST "http://localhost:9091/scrape-and-save?type=GPU&limit=100"
```

#### 3. Scraper timeout

**Problem:** Scraper fails with timeout errors

**Solutions:**
- Increase timeout in `config/config.json`:
  ```json
  {
    "scraping": {
      "timeout_seconds": 60
    }
  }
  ```
- Check internet connection
- Try scraping smaller batches

#### 4. Port already in use

**Problem:** Can't start server on port 9091

**Solution:**
```bash
# Find process using port
netstat -ano | findstr :9091

# Kill process (Windows)
taskkill /PID <PID> /F

# Or change port in config.json
```

#### 5. Docker container won't start

**Problem:** Container exits immediately

**Solutions:**
```bash
# Check logs
docker-compose logs passmark-api

# Check if port is free
netstat -ano | findstr :9091

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Debug Mode

Enable debug logging:

```python
# In app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --port 9091
```

### Performance Issues

If API is slow:

1. **Check database size:**
   ```bash
   ls -lh benchmarks.db
   ```

2. **Rebuild indexes:**
   ```bash
   sqlite3 benchmarks.db "REINDEX;"
   ```

3. **Optimize database:**
   ```bash
   sqlite3 benchmarks.db "VACUUM; ANALYZE;"
   ```

4. **Check resource usage:**
   ```bash
   docker stats passmark-scraper
   ```

---

## Best Practices

### 1. Regular Updates

Schedule weekly scraping to keep data fresh:

```bash
# Linux/Mac cron
0 3 * * 0 cd /path/to/PassMarkScraper && python scrape_all.py

# Windows Task Scheduler
schtasks /create /tn "PassMark Scrape" /tr "python C:\...\scrape_all.py" /sc weekly /d SUN /st 03:00
```

### 2. Monitoring

Monitor service health:

```bash
#!/bin/bash
# health_check.sh

response=$(curl -s http://localhost:9091/health)
status=$(echo $response | jq -r '.status')

if [ "$status" != "ok" ]; then
  echo "Service unhealthy!"
  # Send alert
fi
```

### 3. Backup Strategy

- **Daily:** Backup database file
- **Weekly:** Full database dump
- **Monthly:** Archive old backups

### 4. Security

- Use reverse proxy (nginx) for HTTPS
- Implement API key authentication
- Rate limit endpoints
- Validate all user inputs
- Keep dependencies updated

---

## Next Steps

1. ✅ Get service running
2. ✅ Populate database
3. ✅ Test web interface
4. ✅ Try API calls
5. ✅ Deploy to Docker
6. 📚 Read [Technical Specification](SPEC.md)
7. 🔧 Customize for your needs

---

## Resources

- **API Documentation:** http://localhost:9091/docs
- **PassMark Website:** https://www.cpubenchmark.net
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Docker Docs:** https://docs.docker.com

---

**Need Help?** Check the troubleshooting section or review the API documentation at `/docs`.

