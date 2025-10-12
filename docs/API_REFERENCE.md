# PassMark Scraper - API Reference

Complete API documentation for all endpoints.

---

## Configuration Management

### GET `/config`
Get current microservice configuration.

**Response:**
```json
{
  "database": { "path": "benchmarks.db" },
  "api": { "host": "0.0.0.0", "port": 9091 },
  "scraping": {
    "use_full_lists": true,
    "limits": { "cpu": -1, "gpu": -1 },
    "include_workstation": false
  },
  "scheduler": {
    "enabled": true,
    "scrape_time": "03:00",
    "scrape_days": "sunday"
  }
}
```

---

### PUT `/config`
Update configuration (creates backup of old config).

**Request Body:**
```json
{
  "scraping": {
    "use_full_lists": false,
    "limits": { "cpu": 100 }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated",
  "backup_created": "config/config.json.backup"
}
```

---

### POST `/config/reload`
Reload configuration without restarting service.

**Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded"
}
```

---

## Backup Management

### GET `/backup/list`
List all available database backups.

**Response:**
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

---

### POST `/backup/create`
Create manual backup of database.

**Response:**
```json
{
  "success": true,
  "message": "Backup created",
  "backup_path": "backups/benchmarks_20251012_180046.db"
}
```

---

### POST `/backup/restore?filename=<backup_file>`
Restore database from backup.

**Parameters:**
- `filename` - Backup filename to restore

**Response:**
```json
{
  "success": true,
  "message": "Database restored",
  "db_count": 28333
}
```

---

## Progress Tracking

### GET `/scrape-status`
Get current scraping progress (real-time).

**Response (idle):**
```json
{
  "is_running": false,
  "component_type": null,
  "progress": { "current": 0, "total": 0, "percentage": 0 }
}
```

**Response (active):**
```json
{
  "is_running": true,
  "component_type": "GPU",
  "started_at": "2025-10-12T18:00:47",
  "progress": {
    "current": 150,
    "total": 2785,
    "percentage": 5.4
  },
  "stats": {
    "saved": 140,
    "skipped": 10,
    "errors": 0
  },
  "current_item": "GeForce RTX 3080 Ti",
  "recent_errors": []
}
```

---

## Scheduler Management

### GET `/scheduler/status`
Get scheduler status and next run time.

**Response:**
```json
{
  "enabled": true,
  "running": true,
  "jobs": 1,
  "next_run": "2025-10-19T03:00:00+00:00"
}
```

---

### POST `/scheduler/start`
Start the scheduler (if configured).

**Response:**
```json
{
  "success": true,
  "message": "Scheduler started"
}
```

---

### POST `/scheduler/stop`
Stop the scheduler.

**Response:**
```json
{
  "success": true,
  "message": "Scheduler stopped"
}
```

---

## Enhanced Scraping

### POST `/scrape-and-save`
Scrape components with auto-backup and progress tracking.

**Parameters:**
- `type` - Component type (CPU, GPU, RAM, STORAGE)
- `limit` - Number of components to save
- `include_workstation` - Include workstation components (default: true)
- `skip_backup` - Skip automatic backup (default: false)

**Features:**
- ✅ Automatic backup before scraping
- ✅ Real-time progress tracking via `/scrape-status`
- ✅ Error logging
- ✅ Retention policy (keeps last 7 backups)

**Example:**
```bash
curl -X POST "http://localhost:9091/scrape-and-save?type=GPU&limit=100"
```

**Response:**
```json
{
  "success": true,
  "type": "GPU",
  "saved": 95,
  "skipped": 5,
  "backup_created": "backups/benchmarks_20251012_180046.db",
  "components": [...]
}
```

---

## Configuration Options

### Scheduler Configuration

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

**Options:**
- `enabled`: `true` = automatic scraping, `false` = manual only
- `scrape_time`: Time in HH:MM format (24h)
- `scrape_days`: Day name (monday, tuesday, ..., sunday)
- `timezone`: Timezone (UTC, Europe/Warsaw, America/New_York, etc.)

**Examples:**

Daily at midnight UTC:
```json
{
  "scrape_days": "monday,tuesday,wednesday,thursday,friday,saturday,sunday",
  "scrape_time": "00:00"
}
```

Every Friday at 2 PM:
```json
{
  "scrape_days": "friday",
  "scrape_time": "14:00"
}
```

---

## Error Handling

All endpoints include error handling:

**Success Response:**
```json
{ "success": true, "message": "..." }
```

**Error Response:**
```json
{
  "detail": "Error description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `404` - Not found
- `500` - Server error
- `timeout` - Scraping timeout (600s)

---

## Complete Endpoint List

### Core Endpoints
- `GET /` - Web UI
- `GET /health` - Health check
- `GET /docs` - API documentation

### Search & Compare
- `GET /search` - Search component
- `GET /compare` - Compare two components
- `GET /list` - List components

### Configuration
- `GET /config` - View config
- `PUT /config` - Update config
- `POST /config/reload` - Reload config

### Backup
- `GET /backup/list` - List backups
- `POST /backup/create` - Create backup
- `POST /backup/restore` - Restore backup

### Monitoring
- `GET /scrape-status` - Scraping progress
- `GET /scheduler/status` - Scheduler info
- `POST /scheduler/start` - Start scheduler
- `POST /scheduler/stop` - Stop scheduler

### Scraping
- `POST /scrape-and-save` - Scrape with auto-backup
- `GET /debug/scrape-one` - Debug single component
- `GET /debug/top-list` - Debug list scraping

---

**Total Endpoints:** 17  
**Auto-backup:** ✅  
**Progress Tracking:** ✅  
**Scheduler:** ✅  
**Logging:** ✅

