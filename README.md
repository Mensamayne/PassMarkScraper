# PassMark Scraper Microservice

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-supported-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Database](https://img.shields.io/badge/database-28k+_components-success.svg)](http://localhost:9091/health)

REST API microservice that provides performance benchmark scores for PC components. Data is scraped from PassMark and served via HTTP endpoints with a beautiful web interface for component comparison.

## 🎯 Features

- 🔍 **28,000+ Components** in database (CPU, GPU, RAM, Storage)
- ⚡ **Fast REST API** with component search and comparison
- 🎨 **Beautiful Web UI** for easy component comparison
- 📊 **Normalized Scores** (0-100) for fair comparisons
- 🏆 **Tier System** (low/mid/high/ultra)
- 🔄 **Automatic Scraping** from PassMark with full list support
- 💾 **All DDR Types** (DDR5, DDR4, DDR3, DDR2)
- 🕰️ **Legacy Support** (Pentium 4, Athlon, VIA processors)
- 🐳 **Docker Support** with volume persistence
- 🔧 **Config Management** - Update config via API
- 💾 **Auto-Backup** - Automatic backups before scraping
- 📊 **Progress Tracking** - Real-time scraping progress
- ⏰ **Scheduler** - Automatic weekly scraping
- 📝 **Structured Logging** - Logs to files + console

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# API available at http://localhost:9091
# Web UI at http://localhost:9091
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Start server
uvicorn app.main:app --port 9091 --reload

# Or use the PowerShell script
.\start_server.ps1
```

---

## 📊 Web Interface

Open http://localhost:9091 in your browser for a beautiful comparison interface.

**Features:**
- Visual component comparison
- Real-time performance difference calculation
- Tier and category display
- Mobile-responsive design

**Example:**
1. Enter "GTX 760A" in Component 1
2. Enter "RTX 3050" in Component 2
3. Click "Compare"
4. See the RTX 3050 is 776% faster! 🚀

---

## 🔌 API Endpoints

### Main Endpoints

#### `GET /`
Web interface for component comparison

#### `GET /compare`
Compare two components

**Parameters:**
- `component1` (string) - First component name
- `component2` (string) - Second component name
- `type` (string, optional) - Component type (CPU, GPU, RAM, STORAGE)

**Example:**
```bash
curl "http://localhost:9091/compare?component1=i7-2630UM&component2=i9-8950HK&type=CPU"
```

**Response:**
```json
{
  "found": true,
  "winner": "component2",
  "better_by_percent": 2498.0,
  "component1": {
    "name": "Intel Core i7-2630UM @ 1.60GHz",
    "passmark_score": 400,
    "normalized_score": 10,
    "tier": "low"
  },
  "component2": {
    "name": "Intel Core i9-8950HK @ 2.90GHz",
    "passmark_score": 10392,
    "normalized_score": 50,
    "tier": "mid"
  }
}
```

#### `GET /search`
Search for a component in database

**Parameters:**
- `name` (string) - Component name to search
- `type` (string, optional) - Component type

**Example:**
```bash
curl "http://localhost:9091/search?name=RTX+3080&type=GPU"
```

#### `GET /list`
List top components from database

**Parameters:**
- `type` (string) - Component type (CPU, GPU, RAM, STORAGE)
- `limit` (int) - Number of components to return
- `category` (string, optional) - Filter by category (consumer, workstation)

**Example:**
```bash
curl "http://localhost:9091/list?type=GPU&limit=10&category=consumer"
```

#### `GET /health`
Health check endpoint

---

## 🔧 Management Endpoints

### Configuration

#### `GET /config`
View current configuration

#### `PUT /config`
Update configuration (with backup)

#### `POST /config/reload`
Reload config without restart

### Backup

#### `GET /backup/list`
List all database backups

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

#### `POST /backup/create`
Create manual backup

#### `POST /backup/restore?filename=<name>`
Restore from backup

### Monitoring

#### `GET /scrape-status`
Real-time scraping progress

```json
{
  "is_running": true,
  "component_type": "GPU",
  "progress": { "current": 150, "total": 2785, "percentage": 5.4 },
  "stats": { "saved": 140, "skipped": 10, "errors": 0 }
}
```

#### `GET /scheduler/status`
Scheduler status and next run time

```json
{
  "enabled": true,
  "running": true,
  "next_run": "2025-10-19T03:00:00+00:00"
}
```

#### `POST /scheduler/start` / `POST /scheduler/stop`
Control scheduler

---

## 📦 Database

The microservice uses SQLite database (`benchmarks.db`) with the following structure:

### Current Database Stats:
- **CPU:** 4,255 components (includes Pentium, Celeron, Athlon, FX, mobile, legacy)
- **GPU:** 2,537 components
- **RAM:** 8,648 components (DDR5, DDR4, DDR3, DDR2)
- **STORAGE:** 12,871 components
- **TOTAL:** 28,311 components

### Schema:
```sql
CREATE TABLE component_benchmarks (
    id INTEGER PRIMARY KEY,
    component_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    component_type TEXT NOT NULL,
    category TEXT,
    passmark_score INTEGER NOT NULL,
    normalized_score INTEGER NOT NULL,
    tier TEXT,
    scraped_at TIMESTAMP
);
```

---

## 🔄 Scraping

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

- `use_full_lists: true` - Scrapes ALL components from PassMark (~22k)
- `use_full_lists: false` - Scrapes only high-end lists (~1k)
- `limits: -1` - No limit (scrape all)
- `include_workstation: false` - Excludes workstation components

### Manual Scraping

```bash
# Scrape all component types
python scrape_all.py

# Or use API endpoint
curl -X POST "http://localhost:9091/scrape-and-save?type=CPU&limit=100"
```

---

## 🐳 Docker

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  passmark-api:
    build: .
    ports:
      - "9091:9091"
    volumes:
      - ./benchmarks.db:/app/benchmarks.db
      - ./logs:/app/logs
    restart: unless-stopped
```

### Build and Run

```bash
# Build image
docker-compose build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Database Persistence

The database is persisted using Docker volumes:
- `./benchmarks.db` - SQLite database file
- `./logs` - Application logs

---

## 📁 Project Structure

```
PassMarkScraper/
├── app/
│   ├── main.py              # FastAPI application
│   ├── list_scraper.py      # Scraper for full lists
│   ├── scraper.py           # Single component scraper
│   ├── database.py          # SQLite operations
│   ├── normalizer.py        # Score normalization
│   ├── filters.py           # Component filtering
│   ├── models.py            # Pydantic models
│   └── config_loader.py     # Configuration loader
├── static/
│   └── index.html           # Web UI
├── config/
│   └── config.json          # Configuration
├── docs/
│   ├── TUTORIAL.md          # Detailed tutorial
│   └── SPEC.md              # Technical specification
├── benchmarks.db            # SQLite database
├── docker-compose.yml       # Docker Compose config
├── Dockerfile               # Docker image config
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🎯 Use Cases

### 1. PC Building Assistant
Compare components to help users choose the best option for their budget.

### 2. Performance Benchmarking
Get real-world performance data for any PC component.

### 3. Upgrade Advisor
Compare old components with new ones to show upgrade value.

### 4. Market Analysis
Analyze component performance across different price ranges.

---

## 🔧 Configuration

### Port Configuration

Default port is `9091`. To change:

1. Edit `config/config.json`:
```json
{
  "api": {
    "port": 9091
  }
}
```

2. Update `docker-compose.yml`:
```yaml
ports:
  - "9091:9091"
```

---

## 📈 Performance

- **Search:** ~1-2ms per query (SQLite indexed)
- **Compare:** ~2-5ms per comparison
- **Full scrape:** ~10-15 minutes for all components
- **Database size:** ~5MB for 16k components

---

## 🛠️ Troubleshooting

### Database is empty
Run the scraper to populate the database:
```bash
python scrape_all.py
```

### Port already in use
Change the port in `config/config.json` and restart.

### Docker container won't start
Check logs:
```bash
docker-compose logs
```

### Scraping fails
- Check internet connection
- PassMark might be down
- Increase timeout in `config/config.json`

---

## 📚 Documentation

- **Tutorial:** See [docs/TUTORIAL.md](docs/TUTORIAL.md) for detailed usage guide
- **API Docs:** Visit http://localhost:9091/docs for interactive API documentation
- **Technical Spec:** See [docs/SPEC.md](docs/SPEC.md) for technical details

---

## ⚖️ Legal Notice

This scraper is for **personal and educational use only**. Respect PassMark's Terms of Service. Data is publicly available on PassMark's website. Use responsibly.

---

## 📊 Status

- **Version:** 1.0.0
- **Status:** Production Ready ✅
- **Database:** 28,311 components (all DDR types, legacy CPUs included)
- **API:** 20 endpoints, fully documented
- **Docker:** Supported ✅
- **CI/CD:** GitHub Actions ready
- **License:** MIT

---

## 🎨 Screenshots

### Web Interface
Clean, modern interface for comparing components with real-time results.

### API Response
```json
{
  "winner": "component2",
  "better_by_percent": 776.3,
  "component1": { "name": "GeForce GTX 760A", "tier": "low" },
  "component2": { "name": "GeForce RTX 3050", "tier": "high" }
}
```

---

## 🚀 Future Enhancements

- [ ] GraphQL API
- [ ] Component price tracking
- [ ] Historical performance trends
- [ ] More component types (Motherboards, PSUs)
- [ ] Export to CSV/JSON
- [ ] Batch comparison API

---

## 📧 Support

For issues or questions:
1. Check the [Tutorial](docs/TUTORIAL.md)
2. Review [API Reference](docs/API_REFERENCE.md)
3. See [Examples](docs/EXAMPLES.md)
4. Check API docs at http://localhost:9091/docs
5. Open an [Issue](https://github.com/yourusername/PassMarkScraper/issues)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report a Bug](.github/ISSUE_TEMPLATE/bug_report.md)
- ✨ [Request a Feature](.github/ISSUE_TEMPLATE/feature_request.md)
- 💻 [Submit a Pull Request](.github/pull_request_template.md)

---

## 🔒 Security

For security issues, please see our [Security Policy](SECURITY.md).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Data Attribution:** All benchmark data is copyrighted by PassMark Software Pty Ltd.
This software is for personal and educational use only.

---

## 🌟 Acknowledgments

- [PassMark Software](https://www.passmark.com) for benchmark data
- [FastAPI](https://fastapi.tiangolo.com) for the amazing framework
- [Playwright](https://playwright.dev) for web scraping capabilities

---

**Last Updated:** 2025-10-12  
**Version:** 1.0.0  
**License:** MIT  
**Status:** Production Ready ✅
