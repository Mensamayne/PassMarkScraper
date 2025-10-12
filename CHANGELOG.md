# Changelog

All notable changes to PassMark Scraper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-10-12

### Added - Initial Release

#### Core Features
- REST API microservice for PC component benchmarks
- SQLite database with 28,333 components
- Beautiful web UI for component comparison
- Normalized scoring system (0-100)
- Tier classification (low/mid/high/ultra)

#### Component Coverage
- **CPU:** 4,251 processors (Pentium 4 to Ryzen 9)
- **GPU:** 2,563 graphics cards (GT 430 to RTX 4090, includes integrated)
- **RAM:** 8,648 modules (DDR2, DDR3, DDR4, DDR5)
- **Storage:** 12,871 drives (HDD to NVMe)

#### Scraping Features
- Full PassMark list support (`cpu_list.php`, `gpu_list.php`, etc.)
- Playwright-based scraper with JavaScript support
- Configurable filtering (server/workstation/consumer)
- All DDR types support (DDR5, DDR4, DDR3, DDR2)

#### API Endpoints
- `/search` - Component search
- `/compare` - Component comparison
- `/list` - List top components
- `/scrape-and-save` - Scrape and save to database
- `/health` - Health check

#### Management Features
- **Config Management**
  - `GET /config` - View configuration
  - `PUT /config` - Update configuration
  - `POST /config/reload` - Reload without restart

- **Backup System**
  - Automatic backup before scraping
  - Retention policy (7 backups)
  - `GET /backup/list` - List backups
  - `POST /backup/create` - Manual backup
  - `POST /backup/restore` - Restore from backup

- **Progress Tracking**
  - `GET /scrape-status` - Real-time progress
  - Current item tracking
  - Error logging

- **Scheduler**
  - APScheduler integration
  - Configurable cron schedule
  - `GET /scheduler/status` - Status and next run
  - `POST /scheduler/start` / `stop` - Manual control

- **Logging**
  - Structured logging to `logs/app.log`
  - Console output
  - Error tracking

#### Docker Support
- Docker Compose configuration
- Volume persistence for database and logs
- Health checks
- Resource limits
- Official Playwright base image

#### Documentation
- Comprehensive README.md
- QUICKSTART.md for fast start
- TUTORIAL.md with detailed guide
- API_REFERENCE.md with complete endpoint documentation
- EXAMPLES.md with usage examples

### Technical Details
- Python 3.11+
- FastAPI framework
- Playwright for web scraping
- SQLite with FTS5 for search
- BeautifulSoup4 for HTML parsing
- CORS enabled
- Production-ready error handling

---

## [Unreleased]

### Planned Features
- GraphQL API
- WebSocket for live progress
- Email/Slack notifications
- Component price tracking
- Historical performance trends
- Export to CSV/JSON
- More component types (Motherboards, PSUs)

---

**Note:** This is the initial production-ready release.

