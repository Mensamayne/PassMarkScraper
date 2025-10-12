# PassMark Scraper - Quick Start

Get started with PassMark Scraper in under 5 minutes! 🚀

---

## 🐳 Docker (Recommended)

The fastest way to get started:

```bash
# Start the service
docker-compose up -d

# Wait 5 seconds for startup
# Open http://localhost:9091
```

Done! The service is now running with 16,950 components in the database.

### Check Status

```bash
# View logs
docker-compose logs -f

# Check health
curl http://localhost:9091/health

# Stop service
docker-compose down
```

---

## 💻 Manual Setup (Windows)

If you prefer running without Docker:

```powershell
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start server
.\start_server.ps1

# Open http://localhost:9091
```

---

## 🎯 Try It Out

### Web Interface

1. Open http://localhost:9091
2. Enter "GTX 760A" in Component 1
3. Enter "RTX 3050" in Component 2
4. Click "Compare"
5. See the results! 🎉

### API Examples

```bash
# Compare CPU
curl "http://localhost:9091/compare?component1=i7-2630UM&component2=i9-8950HK&type=CPU"

# Search component
curl "http://localhost:9091/search?name=RTX+3080&type=GPU"

# List top GPUs
curl "http://localhost:9091/list?type=GPU&limit=10"
```

---

## 📚 Next Steps

- Read the [Tutorial](docs/TUTORIAL.md) for detailed usage
- Check [README.md](README.md) for full documentation
- Visit http://localhost:9091/docs for API documentation

---

## 🔄 Update Database

To scrape latest data from PassMark:

```bash
# Inside Docker container
docker exec passmark-scraper python scrape_all.py

# Or manually
python scrape_all.py
```

---

## ❓ Troubleshooting

### Port already in use
```bash
# Change port in config/config.json
{
  "api": {
    "port": 9092
  }
}

# Update docker-compose.yml ports section
```

### Database empty
```bash
# Populate database
python scrape_all.py
```

### Docker issues
```bash
# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

**That's it! You're ready to compare PC components.** 🎮

