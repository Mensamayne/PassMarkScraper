# PassMark Scraper - Technical Specification

## 🎯 Goal
Build a REST API microservice that provides performance benchmarks from PassMark. Scrape data periodically and serve via HTTP endpoints to replace price-based component scoring with real performance data.

---

## 📊 Data Sources

### PassMark Databases
1. **CPU Benchmark** - https://www.cpubenchmark.net/
   - ~4,500+ processors
   - Score: "CPU Mark" (single-thread & multi-thread)
   - Data: Model name, CPU Mark, Thread Rating, TDP, Price

2. **GPU Benchmark** - https://www.videocardbenchmark.net/
   - ~3,000+ graphics cards  
   - Score: "G3D Mark" (3D Graphics Mark)
   - Data: Model name, G3D Mark, TDP, Price

3. **RAM/HDD/SSD** (optional for phase 2)
   - Significantly less data available
   - Lower priority

### Initial Scope
- **CPU**: Top 2,000 processors (covers all modern + relevant legacy)
- **GPU**: Top 1,500 graphics cards (covers all gaming/workstation GPUs)
- **Total**: ~3,500 components to scrape

---

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.11+** - Main language
- **FastAPI** - REST API framework (async, auto-docs)
- **Playwright** - Browser automation (handles JavaScript rendering)
- **BeautifulSoup4** - HTML parsing (fallback if simple HTML)
- **SQLite + FTS5** - Lightweight database (faster than MongoDB for this use case)
- **Uvicorn** - ASGI server
- **python-dotenv** - Configuration management

### Why SQLite over MongoDB?
- **Simple model**: Only lookup `(name, type) → score`
- **Read-heavy**: 99% SELECT, scraper writes once a week
- **Fast**: Index on (name, type) = ~1-2ms lookup
- **Zero maintenance**: No server daemon required
- **Container-friendly**: Single `.db` file
- **Lightweight**: ~1MB library vs MongoDB daemon

---

## 📁 Project Structure

```
PassMarkScraper/
├── app/
│   ├── main.py                   # FastAPI application (endpoints)
│   ├── scraper.py                # Playwright scraper (single + batch)
│   ├── database.py               # SQLite connection & queries
│   ├── normalizer.py             # Score normalization (0-100)
│   └── models.py                 # Pydantic models
├── config/
│   └── config.json               # Configuration (URLs, limits, delays)
├── logs/
│   └── app.log                   # Application logs
├── benchmarks.db                 # SQLite database (volume-mounted in Docker)
├── Dockerfile                    # Container configuration
├── docker-compose.yml            # Docker Compose setup
├── SPEC.md                       # This file
├── README.md                     # Usage instructions
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variables template
```

---

## 🗄️ SQLite Schema

### Table: `component_benchmarks`

```sql
CREATE TABLE component_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,           -- "AMD Ryzen 5 7600X"
    normalized_name TEXT NOT NULL,          -- "ryzen 5 7600x" (lowercase, no special chars)
    component_type TEXT NOT NULL,           -- "CPU" | "GPU"
    
    -- Benchmark scores
    passmark_score INTEGER NOT NULL,        -- Raw PassMark score (e.g. 31845)
    normalized_score INTEGER NOT NULL,      -- Normalized 0-100 score
    tier TEXT,                              -- "low" | "mid" | "high" | "ultra"
    
    -- Additional data
    tdp INTEGER,                            -- Thermal Design Power (watts)
    price_usd REAL,                         -- Price from PassMark (USD)
    
    -- Metadata
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookup
CREATE INDEX idx_lookup ON component_benchmarks(normalized_name, component_type);
CREATE INDEX idx_type_score ON component_benchmarks(component_type, normalized_score DESC);
CREATE INDEX idx_scraped_at ON component_benchmarks(scraped_at DESC);
```

---

## 🔄 Data Flow

```
1. SCRAPE (Background Job)
   PassMark Website → Playwright → Raw HTML/Data
   
2. PARSE
   Raw Data → BeautifulSoup → Structured Data
   
3. NORMALIZE
   Structured Data → normalizer.py → Scores (0-100)
   
4. STORE
   Normalized Data → SQLite INSERT/UPDATE
   
5. API REQUEST (Real-time)
   Java Backend → HTTP GET /search?name=RTX4070&type=GPU
   
6. QUERY
   FastAPI → SQLite SELECT → Return Score
   
7. INTEGRATE
   RigRollService.java → Use returned score in build power calculation
```

---

## 📐 Score Normalization Algorithm

### CPU Normalization (0-100 scale)
```python
# PassMark CPU scores range: ~500 (low-end) to ~60,000 (HEDT)
# Gaming CPUs typically: 2,000 - 45,000

def normalize_cpu_score(passmark_score):
    # Define percentile ranges based on PassMark data
    if passmark_score < 2000:   return 10   # Very low (office/basic)
    if passmark_score < 5000:   return 20   # Entry-level
    if passmark_score < 10000:  return 35   # Budget gaming
    if passmark_score < 15000:  return 50   # Mid-range
    if passmark_score < 20000:  return 65   # Good gaming
    if passmark_score < 28000:  return 80   # High-end
    if passmark_score < 40000:  return 92   # Enthusiast
    return 100                              # HEDT/Workstation
```

### GPU Normalization (0-100 scale)
```python
# PassMark G3D scores range: ~200 (GT 1030) to ~35,000 (RTX 4090)

def normalize_gpu_score(g3d_score):
    if g3d_score < 1000:    return 5    # Office/basic (GT 1030, etc.)
    if g3d_score < 3000:    return 15   # Entry gaming (GTX 1050 Ti)
    if g3d_score < 6000:    return 30   # Budget (GTX 1660, RX 580)
    if g3d_score < 10000:   return 50   # Mid-range (RTX 3060, RX 6600)
    if g3d_score < 15000:   return 65   # Good gaming (RTX 3070, RX 6800)
    if g3d_score < 20000:   return 80   # High-end (RTX 4070 Ti)
    if g3d_score < 28000:   return 92   # Enthusiast (RTX 4080)
    return 100                          # Ultra (RTX 4090, RTX 5090)
```

---

## 🔧 Configuration

### `config/scraper_config.json`
```json
{
  "scraping": {
    "delay_between_requests_ms": 2000,
    "max_retries": 3,
    "timeout_seconds": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  },
  "limits": {
    "cpu_count": 2000,
    "gpu_count": 1500,
    "ram_count": 0,
    "storage_count": 0
  },
  "sources": {
    "cpu_url": "https://www.cpubenchmark.net/CPU_mega_page.html",
    "gpu_url": "https://www.videocardbenchmark.net/GPU_mega_page.html"
  },
  "normalization": {
    "cpu_min_score": 500,
    "cpu_max_score": 60000,
    "gpu_min_score": 200,
    "gpu_max_score": 35000
  }
}
```

### `config/config.json`
```json
{
  "database": {
    "path": "benchmarks.db"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

---

## 🚀 Execution Plan

### Phase 1: Core Scraping (Week 1)
- [x] Setup project structure
- [ ] Implement CPU scraper
- [ ] Implement GPU scraper
- [ ] Data normalization
- [ ] MongoDB integration

### Phase 2: Matching & Integration (Week 2)
- [ ] Fuzzy name matching algorithm
- [ ] Map scraped data to existing components
- [ ] Java service integration (`RigRollService.java`)
- [ ] Fallback logic (price-based if no benchmark found)

### Phase 3: Automation (Week 3)
- [ ] Scheduled task (weekly updates)
- [ ] Error handling & retry logic
- [ ] Monitoring & alerting
- [ ] Documentation

---

## 📝 Best Practices

### Code Quality
1. **Type Hints** - Use Python type annotations everywhere
2. **Docstrings** - Google-style docstrings for all functions
3. **Logging** - Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
4. **Error Handling** - Try/except with specific exceptions, retry logic
5. **Testing** - Unit tests for critical functions (matching, normalization)

### Scraping Ethics
1. **Respect robots.txt** - Check PassMark's robots.txt before scraping
2. **Rate Limiting** - 2-3 second delay between requests
3. **User-Agent** - Identify as bot, include contact email
4. **Caching** - Don't re-scrape data that hasn't changed
5. **Off-peak hours** - Run scraper at night (low traffic)

### Data Quality
1. **Validation** - Verify scores are reasonable (e.g. no negative values)
2. **Deduplication** - Handle multiple entries for same component
3. **Versioning** - Keep history of score changes
4. **Manual Review** - Log suspicious entries for manual check

### Performance
1. **Async Scraping** - Use `asyncio` + Playwright async API
2. **Batch Inserts** - Insert to MongoDB in batches of 100
3. **Parallel Processing** - CPU & GPU scraping in parallel
4. **Incremental Updates** - Only update changed components

---

## 🔐 Security & Reliability

### Error Recovery
- Store failed scrapes in `data/failed/`
- Retry mechanism with exponential backoff
- Email/log alerts on critical failures

### Data Validation
- Cross-check with multiple sources (sanity check)
- Flag anomalies (e.g., GT 1030 with score > 10000)
- Manual approval for outliers

### Backup
- Daily backup of `component_benchmarks` collection
- Keep raw scraped data for 30 days

---

## 📈 Expected Data Volume

### Components Count
- **CPU**: ~2,000 entries × ~200 bytes = **400 KB**
- **GPU**: ~1,500 entries × ~200 bytes = **300 KB**
- **Total**: ~700 KB in MongoDB (negligible)

### Scraping Time Estimate
- **Per component**: ~0.5s (with 2s delay = 2.5s total)
- **CPU scraping**: 2,000 × 2.5s = **~1.4 hours**
- **GPU scraping**: 1,500 × 2.5s = **~1 hour**
- **Total runtime**: **~2.5 hours** (run weekly at night)

---

## 🔗 Integration with Java Backend

### Update `RigRollService.java`

**Old method** (price-based):
```java
private int calculateComponentPowerScore(double price) {
    if (price < 500) return 20;
    else if (price < 1000) return 40;
    else if (price < 2000) return 60;
    else if (price < 3000) return 80;
    else return 100;
}
```

**New method** (HTTP API-based with fallback):
```java
private int calculateComponentPowerScore(Component component, String type) {
    try {
        // HTTP request to PassMark microservice
        String url = String.format("http://localhost:8080/search?name=%s&type=%s",
                                   URLEncoder.encode(component.getName(), "UTF-8"),
                                   type);
        
        RestTemplate restTemplate = new RestTemplate();
        BenchmarkResponse response = restTemplate.getForObject(url, BenchmarkResponse.class);
        
        if (response != null && response.getNormalizedScore() != null) {
            return response.getNormalizedScore();
        }
    } catch (Exception e) {
        log.warn("Failed to fetch benchmark for {}: {}", component.getName(), e.getMessage());
    }
    
    // Fallback to price-based scoring
    return calculateComponentPowerScoreByPrice(component.getPrice());
}
```

### Response Model
```java
@Data
public class BenchmarkResponse {
    private String name;
    private Integer passmarkScore;
    private Integer normalizedScore;
    private String tier;
}
```

---

## 🕐 Maintenance Schedule

### Weekly (Automated)
- Run scraper every **Sunday at 3:00 AM**
- Update benchmark scores in MongoDB
- Generate report of new/changed components

### Monthly (Manual)
- Review scraping logs
- Check for failed scrapes
- Update scraping logic if PassMark changes site structure
- Verify data quality

### Quarterly (Manual)
- Review normalization thresholds
- Adjust tier boundaries based on new hardware
- Clean up obsolete components (>3 years old with no market presence)

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| PassMark changes site structure | HIGH | Monitor errors, manual review weekly, version HTML snapshots |
| IP ban from aggressive scraping | MEDIUM | Rate limiting (2s delay), rotate user agents, respect robots.txt |
| Incorrect name matching | MEDIUM | Fuzzy matching with threshold >80%, manual review flagged matches |
| Data staleness | LOW | Weekly updates, cache invalidation after 30 days |
| Legal issues (ToS violation) | HIGH | Use data for internal purposes only, add disclaimer |

---

## 📦 Deliverables

### Phase 1 (Scraper Core)
1. `scripts/scraper_cpu.py` - CPU scraper with Playwright
2. `scripts/scraper_gpu.py` - GPU scraper with Playwright  
3. `scripts/data_processor.py` - Data cleaning & normalization
4. `scripts/mongodb_updater.py` - Batch upsert to MongoDB
5. `requirements.txt` - Python dependencies
6. `README.md` - Setup & usage instructions

### Phase 2 (Integration)
1. `models/ComponentBenchmark.java` - Java model for benchmarks
2. Updated `RigRollService.java` - Use benchmark scores
3. `scripts/fuzzy_matcher.py` - Match scraped → existing components
4. `config/scraper_config.json` - Configuration file

### Phase 3 (Automation)
1. `scripts/scheduler.py` - Weekly auto-run script
2. Windows Task Scheduler config (`.xml`)
3. Email notification on errors
4. Dashboard/report generator

---

## 🧪 Testing Strategy

### Unit Tests
- Name normalization (e.g., "GeForce RTX 4070" → "rtx 4070")
- Score normalization (raw → 0-100)
- Fuzzy matching accuracy

### Integration Tests
- Full scrape → process → MongoDB pipeline
- MongoDB query performance
- Java service benchmark lookup

### Data Quality Tests
- Verify no duplicate entries
- Check score distribution (should follow normal curve)
- Validate TDP values (reasonable ranges)

---

## 📊 Success Metrics

1. **Coverage**: >90% of components in `components` collection matched to benchmarks
2. **Accuracy**: Build Power Score correlates with actual performance (validation needed)
3. **Reliability**: <5% scraping failure rate
4. **Performance**: Full scrape completes in <3 hours
5. **Freshness**: Data updated weekly without manual intervention

---

## 🔄 Example: GT 1030 Problem SOLVED

### Current (Price-Based)
```
GT 1030: 309 PLN → score: 20/100 ✅
Ryzen 5 7600X: 1,872 PLN → score: 60/100 ✅
TOTAL BUILD: 3,909 PLN → RARITY: RARE 💎
BUILD POWER: 18% (bottleneck) 🍾 ← CORRECT!
```

**Problem**: Rarity (RARE) doesn't match Build Power (18% = trash)

### New (Benchmark-Based)
```
GT 1030: PassMark G3D = 1,689 → normalized: 8/100 ❌ (worse!)
Ryzen 5 7600X: PassMark CPU = 31,845 → normalized: 88/100 ✅
TOTAL BUILD: Still 3,909 PLN → RARITY: RARE 💎
BUILD POWER: 7% (worse bottleneck) 💀 ← MORE ACCURATE!
```

**Solution**: 
- Option A: Rarity based on Build Power (not price)
- Option B: Keep both - show "Rare but trash" badge 😄

---

## 🚦 Go/No-Go Decision Points

### Prerequisites (Must Have)
- ✅ MongoDB accessible at port 27018
- ✅ Python 3.11+ installed
- ✅ Network access to PassMark (not blocked by firewall)

### Legal Check (Should Have)
- Check PassMark `robots.txt`
- Review Terms of Service
- Consider reaching out to PassMark for permission

### Alternative if Scraping Blocked
- Manual CSV import from PassMark (they offer downloads)
- Use TechPowerUp GPU database (more scraping-friendly)
- Build static JSON from community sources (e.g., Reddit hardware wiki)

---

## 📞 Contact & Support

**Maintainer**: Development Team  
**Issues**: Log to `logs/errors.log` + create GitHub issue  
**Updates**: Check PassMark quarterly for site structure changes

---

## 🎓 Learning Resources

- Playwright Python: https://playwright.dev/python/
- PassMark Forums: https://www.passmark.com/forum/
- Web Scraping Best Practices: https://scrapinghub.com/guides/web-scraping-best-practices

---

**Last Updated**: 2025-10-12  
**Version**: 1.0  
**Status**: SPEC READY - AWAITING IMPLEMENTATION



