# PassMark Scraper - Usage Examples

Practical examples for all features.

---

## 📊 Basic Operations

### Check Service Health
```bash
curl http://localhost:9091/health
```

Response:
```json
{
  "status": "ok",
  "db_count": 28333
}
```

---

## 🔍 Component Search & Compare

### Search for Component
```bash
curl "http://localhost:9091/search?name=RTX+3080&type=GPU"
```

### Compare Two Components
```bash
curl "http://localhost:9091/compare?component1=Pentium+4&component2=Ryzen+9&type=CPU"
```

Result: Ryzen 9 is **81,535% faster** than Pentium 4!

---

## 🔧 Configuration Management

### View Current Config
```bash
curl http://localhost:9091/config
```

### Update Scraping Limits
```bash
curl -X PUT http://localhost:9091/config \
  -H "Content-Type: application/json" \
  -d '{
    "scraping": {
      "use_full_lists": false,
      "limits": {
        "cpu": 100,
        "gpu": 100
      }
    }
  }'
```

### Reload Config
```bash
curl -X POST http://localhost:9091/config/reload
```

---

## 💾 Backup Management

### Create Manual Backup
```bash
curl -X POST http://localhost:9091/backup/create
```

Response:
```json
{
  "success": true,
  "backup_path": "backups/benchmarks_20251012_180046.db"
}
```

### List All Backups
```bash
curl http://localhost:9091/backup/list
```

Response:
```json
{
  "count": 2,
  "backups": [
    {
      "filename": "benchmarks_20251012_180046.db",
      "size_mb": 7.07,
      "created_at": "2025-10-12T18:00:46"
    }
  ]
}
```

### Restore from Backup
```bash
curl -X POST "http://localhost:9091/backup/restore?filename=benchmarks_20251012_180046.db"
```

---

## 📊 Progress Monitoring

### Check Scraping Progress
```bash
# Start scraping in background
curl -X POST "http://localhost:9091/scrape-and-save?type=GPU&limit=100" &

# Monitor progress in real-time
watch -n 1 'curl -s http://localhost:9091/scrape-status | jq'
```

Response (while scraping):
```json
{
  "is_running": true,
  "component_type": "GPU",
  "progress": {
    "current": 45,
    "total": 100,
    "percentage": 45.0
  },
  "stats": {
    "saved": 42,
    "skipped": 3,
    "errors": 0
  },
  "current_item": "GeForce RTX 3070"
}
```

---

## ⏰ Scheduler Management

### Check Scheduler Status
```bash
curl http://localhost:9091/scheduler/status
```

Response:
```json
{
  "enabled": true,
  "running": true,
  "jobs": 1,
  "next_run": "2025-10-19T03:00:00+00:00"
}
```

### Enable Scheduler (via config)

Edit `config/config.json`:
```json
{
  "scheduler": {
    "enabled": true,
    "scrape_time": "03:00",
    "scrape_days": "sunday",
    "timezone": "UTC"
  }
}
```

Then reload:
```bash
curl -X POST http://localhost:9091/config/reload
docker-compose restart
```

### Start/Stop Scheduler Manually
```bash
# Start
curl -X POST http://localhost:9091/scheduler/start

# Stop
curl -X POST http://localhost:9091/scheduler/stop
```

---

## 🔄 Complete Scraping Workflow

### Scenario: Update Database Weekly

**Step 1: Configure Scheduler**
```json
{
  "scheduler": {
    "enabled": true,
    "scrape_time": "03:00",
    "scrape_days": "sunday"
  }
}
```

**Step 2: Restart Service**
```bash
docker-compose restart
```

**Step 3: Verify**
```bash
curl http://localhost:9091/scheduler/status
```

Expected:
```json
{
  "enabled": true,
  "next_run": "2025-10-19T03:00:00+00:00"
}
```

**What happens:**
- Every Sunday at 3:00 AM
- Automatic backup created
- Scrapes all components (CPU, GPU, RAM, Storage)
- Logs to `logs/app.log`
- Keeps last 7 backups

---

## 🚨 Disaster Recovery

### Scenario: Scraping Failed, Database Corrupted

**Step 1: List Backups**
```bash
curl http://localhost:9091/backup/list
```

**Step 2: Restore from Latest Backup**
```bash
curl -X POST "http://localhost:9091/backup/restore?filename=benchmarks_20251012_180046.db"
```

**Step 3: Verify**
```bash
curl http://localhost:9091/health
```

Expected:
```json
{
  "status": "ok",
  "db_count": 28333
}
```

---

## 🎯 Real-World Use Cases

### Use Case 1: PC Building Assistant

```python
import requests

def get_upgrade_recommendation(old_gpu, budget_options):
    """Compare old GPU with budget options."""
    results = []
    
    for new_gpu in budget_options:
        response = requests.get(
            'http://localhost:9091/compare',
            params={'component1': old_gpu, 'component2': new_gpu, 'type': 'GPU'}
        )
        
        data = response.json()
        if data['found']:
            results.append({
                'gpu': new_gpu,
                'improvement': data['better_by_percent'],
                'new_score': data['component2']['passmark_score']
            })
    
    # Sort by improvement
    results.sort(key=lambda x: x['improvement'], reverse=True)
    return results

# Usage
old = "GTX 1060"
options = ["RTX 3060", "RTX 3050", "RX 6600"]
recommendations = get_upgrade_recommendation(old, options)

for rec in recommendations:
    print(f"{rec['gpu']}: +{rec['improvement']}% improvement")
```

### Use Case 2: Batch Component Analysis

```python
import requests
import pandas as pd

def analyze_gpu_generation(generation):
    """Analyze all GPUs from a generation."""
    response = requests.get(
        'http://localhost:9091/list',
        params={'type': 'GPU', 'limit': 100, 'category': 'consumer'}
    )
    
    gpus = response.json()['components']
    
    # Filter by generation (e.g., "RTX 30")
    gen_gpus = [g for g in gpus if generation in g['name']]
    
    # Create DataFrame
    df = pd.DataFrame(gen_gpus)
    
    print(f"\n{generation} Series Analysis:")
    print(f"Count: {len(df)}")
    print(f"Avg Score: {df['passmark_score'].mean():.0f}")
    print(f"Min: {df['passmark_score'].min()} ({df.loc[df['passmark_score'].idxmin(), 'name']})")
    print(f"Max: {df['passmark_score'].max()} ({df.loc[df['passmark_score'].idxmax(), 'name']})")

# Usage
analyze_gpu_generation("RTX 30")
analyze_gpu_generation("RTX 40")
```

### Use Case 3: Monitoring Dashboard

```javascript
// Real-time monitoring
async function monitorScraping() {
  const statusElement = document.getElementById('status');
  
  const interval = setInterval(async () => {
    const response = await fetch('http://localhost:9091/scrape-status');
    const status = await response.json();
    
    if (status.is_running) {
      statusElement.innerHTML = `
        <h3>Scraping ${status.component_type}</h3>
        <progress value="${status.progress.current}" max="${status.progress.total}"></progress>
        <p>${status.progress.percentage}% - ${status.current_item}</p>
        <p>Saved: ${status.stats.saved} | Skipped: ${status.stats.skipped}</p>
      `;
    } else {
      clearInterval(interval);
      statusElement.innerHTML = '<p>Scraping complete!</p>';
    }
  }, 1000);
}
```

---

## 🛠️ Advanced Configuration

### Custom Scraping Schedule

**Every day at midnight:**
```json
{
  "scheduler": {
    "enabled": true,
    "scrape_time": "00:00",
    "scrape_days": "monday,tuesday,wednesday,thursday,friday,saturday,sunday"
  }
}
```

**Twice a week (Monday & Friday at 2 AM):**
```json
{
  "scheduler": {
    "enabled": true,
    "scrape_time": "02:00",
    "scrape_days": "monday,friday"
  }
}
```

**With different timezone:**
```json
{
  "scheduler": {
    "enabled": true,
    "scrape_time": "03:00",
    "scrape_days": "sunday",
    "timezone": "Europe/Warsaw"
  }
}
```

---

## 📝 Logging Examples

### View Logs
```bash
# Docker logs
docker-compose logs -f passmark-api

# File logs
tail -f logs/app.log

# Windows
Get-Content logs/app.log -Wait -Tail 50
```

### Log Format
```
2025-10-12 18:00:46 - app.main - INFO - Starting scrape: type=GPU, limit=5
2025-10-12 18:00:46 - app.backup - INFO - Backup created: backups/benchmarks_20251012_180046.db
2025-10-12 18:00:47 - app.main - INFO - Saved 5, Skipped 0
```

---

## 🔄 Complete Update Workflow

### Weekly Update Process

```bash
#!/bin/bash
# weekly_update.sh

echo "Starting weekly PassMark update..."

# 1. Create manual backup
echo "Creating backup..."
curl -X POST http://localhost:9091/backup/create

# 2. Check current database stats
echo "Current database:"
curl http://localhost:9091/health

# 3. Start scraping (with auto-backup)
echo "Starting scrape..."
curl -X POST "http://localhost:9091/scrape-and-save?type=CPU&limit=10000"
curl -X POST "http://localhost:9091/scrape-and-save?type=GPU&limit=10000"
curl -X POST "http://localhost:9091/scrape-and-save?type=RAM&limit=10000"
curl -X POST "http://localhost:9091/scrape-and-save?type=STORAGE&limit=10000"

# 4. Verify new stats
echo "Updated database:"
curl http://localhost:9091/health

echo "Update complete!"
```

Make executable:
```bash
chmod +x weekly_update.sh
```

Run:
```bash
./weekly_update.sh
```

---

**For more examples, see [TUTORIAL.md](TUTORIAL.md)**

