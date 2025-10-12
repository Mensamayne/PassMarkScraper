"""FastAPI application for PassMark benchmark microservice."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models import BenchmarkResponse, ScrapeResult, HealthResponse
from app.scraper import scrape_single_component
from app.list_scraper import scrape_top_components
from app.page_analyzer import analyze_component_page
from app.database import Database
from app.filters import categorize_component, should_include_component
from app.normalizer import (
    normalize_name,
    normalize_component_score,
    get_tier
)
from app.backup import create_backup, list_backups, restore_backup
from app.scrape_status import get_status, update_status
from app.scheduler import (
    init_scheduler, 
    get_scheduler_status, 
    start_scheduler as start_sched,
    stop_scheduler as stop_sched
)
from app.config_loader import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Thread pool for running sync scraper
executor = ThreadPoolExecutor(max_workers=3)

# Initialize database
db = Database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting PassMark Scraper API...")
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("backups").mkdir(exist_ok=True)
    
    # Initialize scheduler if enabled in config
    try:
        init_scheduler(config.get_config())
        scheduler_status = get_scheduler_status()
        if scheduler_status['enabled']:
            logger.info(f"Scheduler initialized. Next run: {scheduler_status.get('next_run', 'N/A')}")
        else:
            logger.info("Scheduler disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PassMark Scraper API...")
    try:
        stop_sched()
    except Exception as e:
        logger.warning(f"Failed to stop scheduler during shutdown: {e}")
    
    # Cleanup thread pool
    try:
        executor.shutdown(wait=False)
    except Exception as e:
        logger.warning(f"Failed to shutdown executor: {e}")


app = FastAPI(
    title="PassMark Scraper API",
    description="Microservice for PC component benchmark scores",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_path = "benchmarks.db"
    db_exists = Path(db_path).exists()
    
    return {
        "status": "ok",
        "db_path": db_path,
        "db_exists": db_exists,
        "db_count": db.get_count()
    }


@app.get("/debug/scrape-one", response_model=ScrapeResult)
async def debug_scrape_one(
    url: str = Query(..., description="PassMark component URL")
):
    """
    Debug endpoint - scrape a single component without saving to database.
    
    Example:
        /debug/scrape-one?url=https://www.cpubenchmark.net/cpu.php?cpu=AMD+Ryzen+5+7600X
    """
    try:
        # Run sync scraper in thread pool to avoid asyncio conflict
        loop = asyncio.get_event_loop()
        raw_data = await loop.run_in_executor(executor, scrape_single_component, url)
        
        # Normalize the data
        component_type = raw_data["component_type"]
        passmark_score = raw_data["passmark_score"]
        normalized_score = normalize_component_score(component_type, passmark_score)
        tier = get_tier(normalized_score)
        normalized_name = normalize_name(raw_data["name"])
        
        normalized = {
            "component_name": raw_data["name"],
            "normalized_name": normalized_name,
            "component_type": component_type,
            "passmark_score": passmark_score,
            "normalized_score": normalized_score,
            "tier": tier
        }
        
        return ScrapeResult(
            raw_data=raw_data,
            normalized=normalized,
            would_insert_sql="Debug SQL removed for security"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scrape error: {str(e)}"
        )


@app.get("/search")
async def search_benchmark(
    name: str = Query(..., description="Component name to search"),
    type: str = Query(None, description="Component type (CPU, GPU, RAM, STORAGE) - optional")
):
    """
    Search for component benchmark score in database.
    
    Example:
        /search?name=RTX+5090&type=GPU
        /search?name=Ryzen+9+9950X
    """
    try:
        result = db.search_component(name, type)
        
        if result:
            return {
                "found": True,
                "component": result
            }
        else:
            return {
                "found": False,
                "error": "not_found"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@app.get("/debug/top-list")
async def debug_top_list(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of top components to return")
):
    """
    Debug endpoint - scrape top components from PassMark ranking lists.
    
    Example:
        /debug/top-list?type=CPU&limit=5
    """
    try:
        # Run in thread pool
        loop = asyncio.get_event_loop()
        components = await loop.run_in_executor(
            executor, 
            scrape_top_components, 
            type.upper(), 
            limit
        )
        
        # Add normalized scores
        for comp in components:
            normalized_score = normalize_component_score(type, comp["passmark_score"])
            comp["normalized_score"] = normalized_score
            comp["tier"] = get_tier(normalized_score)
        
        return {
            "component_type": type.upper(),
            "count": len(components),
            "components": components
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scrape error: {str(e)}"
        )


@app.get("/debug/analyze-page")
async def debug_analyze_page(
    url: str = Query(..., description="PassMark component URL to analyze")
):
    """
    Debug endpoint - analyze what data is available on a PassMark page.
    
    Example:
        /debug/analyze-page?url=https://www.cpubenchmark.net/cpu.php?cpu=AMD+Ryzen+9+9950X
    """
    try:
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(executor, analyze_component_page, url)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
        )


@app.post("/scrape-and-save")
async def scrape_and_save_top(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of top components to scrape"),
    include_workstation: bool = Query(True, description="Include workstation components"),
    skip_backup: bool = Query(False, description="Skip automatic backup before scraping")
):
    """
    Scrape top N components from PassMark and save to database.
    Server components are automatically excluded.
    Automatically creates backup before scraping.
    
    Example:
        /scrape-and-save?type=GPU&limit=100
    """
    try:
        # Create backup before scraping (unless skipped)
        backup_path = None
        if not skip_backup:
            try:
                backup_path = create_backup()
                logger.info(f"Pre-scrape backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Backup failed, continuing anyway: {e}")
        
        logger.info(f"Starting scrape: type={type}, limit={limit}")
        
        # Initialize status tracking
        status = get_status()
        status.start(type.upper(), limit * 2)
        
        # Get list from PassMark
        loop = asyncio.get_event_loop()
        components = await loop.run_in_executor(
            executor,
            scrape_top_components,
            type.upper(),
            limit * 2  # Get more to account for filtering
        )
        
        status.total_items = len(components)
        saved_count = 0
        skipped_count = 0
        results = []
        
        for idx, comp in enumerate(components):
            if saved_count >= limit:
                break
            
            # Update progress
            status.update(idx + 1, comp['name'])
            
            # Check if should include
            category = categorize_component(comp['name'], type.upper())
            
            if category == 'server':
                skipped_count += 1
                status.increment_skipped()
                continue
            
            if not include_workstation and category == 'workstation':
                skipped_count += 1
                status.increment_skipped()
                continue
            
            # Normalize scores
            normalized_score = normalize_component_score(type, comp["passmark_score"])
            
            # Prepare data for database
            db_data = {
                'name': comp['name'],
                'normalized_name': normalize_name(comp['name']),
                'component_type': type.upper(),
                'category': category,
                'passmark_score': comp['passmark_score'],
                'normalized_score': normalized_score,
                'tier': get_tier(normalized_score)
            }
            
            # Save to database
            try:
                db.insert_component(db_data)
                saved_count += 1
                status.increment_saved()
                
                results.append({
                    'name': comp['name'],
                    'category': category,
                    'score': comp['passmark_score']
                })
            except Exception as e:
                status.add_error(f"Failed to save {comp['name']}: {str(e)}")
                logger.error(f"Failed to save component: {e}")
        
        # Finish status tracking
        status.finish()
        
        return {
            "success": True,
            "type": type.upper(),
            "saved": saved_count,
            "skipped": skipped_count,
            "backup_created": backup_path,
            "components": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scrape and save error: {str(e)}"
        )


@app.get("/list")
async def list_components(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of components to return"),
    category: str = Query(None, description="Filter by category (consumer, workstation)")
):
    """
    List top components from database.
    
    Example:
        /list?type=GPU&limit=10&category=consumer
    """
    try:
        components = db.get_top_components(type.upper(), limit, category)
        
        return {
            "type": type.upper(),
            "category": category or "all",
            "count": len(components),
            "components": components
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"List error: {str(e)}"
        )


@app.get("/compare")
async def compare_components(
    component1: str = Query(..., description="First component name (e.g., 'gtx 1080ti')"),
    component2: str = Query(..., description="Second component name (e.g., 'rtx 3080')"),
    type: str = Query(None, description="Component type (CPU, GPU, RAM, STORAGE) - optional")
):
    """
    Compare two components and show which is better.
    
    Example:
        /compare?component1=gtx+1080ti&component2=rtx+3080
        /compare?component1=ryzen+5+7600x&component2=i9+13900k&type=CPU
    """
    try:
        # Search for both components
        result1 = db.search_component(component1, type)
        result2 = db.search_component(component2, type)
        
        # Check if both found
        if not result1 and not result2:
            return {
                "found": False,
                "error": "both_not_found"
            }
        
        if not result1:
            return {
                "found": False,
                "error": "component1_not_found",
                "component2": {
                    "name": result2['name'],
                    "passmark_score": result2['passmark_score'],
                    "normalized_score": result2['normalized_score'],
                    "tier": result2['tier']
                }
            }
        
        if not result2:
            return {
                "found": False,
                "error": "component2_not_found",
                "component1": {
                    "name": result1['name'],
                    "passmark_score": result1['passmark_score'],
                    "normalized_score": result1['normalized_score'],
                    "tier": result1['tier']
                }
            }
        
        # Both found - compare them
        score1 = result1['passmark_score']
        score2 = result2['passmark_score']
        norm1 = result1['normalized_score']
        norm2 = result2['normalized_score']
        
        # Calculate differences
        score_diff = abs(score1 - score2)
        score_diff_percent = round((score_diff / min(score1, score2)) * 100, 1)
        
        norm_diff = abs(norm1 - norm2)
        
        # Determine winner
        if score1 > score2:
            winner = "component1"
            better_by_percent = round(((score1 - score2) / score2) * 100, 1)
        elif score2 > score1:
            winner = "component2"
            better_by_percent = round(((score2 - score1) / score1) * 100, 1)
        else:
            winner = "tie"
            better_by_percent = 0
        
        return {
            "found": True,
            "winner": winner,
            "better_by_percent": better_by_percent,
            "component1": {
                "name": result1['name'],
                "passmark_score": score1,
                "normalized_score": norm1,
                "tier": result1['tier'],
                "category": result1.get('category'),
                "tdp": result1.get('tdp')
            },
            "component2": {
                "name": result2['name'],
                "passmark_score": score2,
                "normalized_score": norm2,
                "tier": result2['tier'],
                "category": result2.get('category'),
                "tdp": result2.get('tdp')
            },
            "comparison": {
                "passmark_difference": score_diff,
                "passmark_difference_percent": score_diff_percent,
                "normalized_difference": norm_diff,
                "component1_faster": score1 > score2,
                "component2_faster": score2 > score1
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison error: {str(e)}"
        )


@app.get("/config")
async def get_config():
    """Get current configuration."""
    from app.config_loader import config
    cfg = config.get_config()
    return {
        "database": cfg.get("database", {}),
        "api": cfg.get("api", {}),
        "scraping": cfg.get("scraping", {}),
        "sources": cfg.get("sources", {})
    }


@app.put("/config")
async def update_config(new_config: dict):
    """Update configuration (requires restart to take full effect)."""
    import json
    from app.config_loader import config
    
    try:
        # Backup current config
        config_path = Path("config/config.json")
        backup_path = Path("config/config.json.backup")
        
        if config_path.exists():
            import shutil
            shutil.copy(config_path, backup_path)
        
        # Write new config
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)
        
        return {
            "success": True,
            "message": "Configuration updated. Restart service for full effect.",
            "backup_created": str(backup_path)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update config: {str(e)}"
        )


@app.post("/config/reload")
async def reload_config():
    """Reload configuration without restart."""
    from app.config_loader import config
    
    try:
        config.load_config()
        cfg = config.get_config()
        return {
            "success": True,
            "message": "Configuration reloaded",
            "config": {
                "scraping": cfg.get("scraping", {}),
                "api": cfg.get("api", {})
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload config: {str(e)}"
        )


@app.get("/backup/list")
async def list_database_backups():
    """List all available database backups."""
    try:
        backups = list_backups()
        return {
            "count": len(backups),
            "backups": backups
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )


@app.post("/backup/create")
async def create_database_backup():
    """Create a manual backup of the database."""
    try:
        backup_path = create_backup()
        return {
            "success": True,
            "message": "Backup created",
            "backup_path": backup_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup: {str(e)}"
        )


@app.post("/backup/restore")
async def restore_database_backup(filename: str = Query(..., description="Backup filename to restore")):
    """Restore database from backup."""
    try:
        restore_backup(filename)
        return {
            "success": True,
            "message": f"Database restored from {filename}",
            "db_count": db.get_count()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore backup: {str(e)}"
        )


@app.get("/scrape-status")
async def scrape_status():
    """Get current scraping status and progress."""
    status = get_status()
    return status.to_dict()


@app.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status."""
    return get_scheduler_status()


@app.post("/scheduler/start")
async def scheduler_start():
    """Start the scheduler."""
    try:
        if start_sched():
            return {
                "success": True,
                "message": "Scheduler started",
                "status": get_scheduler_status()
            }
        else:
            return {
                "success": False,
                "message": "Scheduler already running or not configured"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scheduler: {str(e)}"
        )


@app.post("/scheduler/stop")
async def scheduler_stop():
    """Stop the scheduler."""
    try:
        if stop_sched():
            return {
                "success": True,
                "message": "Scheduler stopped"
            }
        else:
            return {
                "success": False,
                "message": "Scheduler not running"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop scheduler: {str(e)}"
        )


@app.get("/")
async def root():
    """Serve the main HTML page."""
    html_file = Path("static/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return {
            "name": "PassMark Scraper API",
            "version": "1.0.0",
            "status": "Production Ready",
            "db_count": db.get_count(),
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "config": "GET /config - View configuration",
                "config_update": "PUT /config - Update configuration",
                "config_reload": "POST /config/reload - Reload configuration",
                "search": "/search?name=<component>&type=<CPU|GPU> - Search in database",
                "compare": "/compare?component1=gtx+1080ti&component2=rtx+3080 - Compare two components",
                "list": "/list?type=<CPU|GPU>&limit=10&category=consumer - List components",
                "scrape_and_save": "POST /scrape-and-save?type=<type>&limit=100 - Scrape and save to DB",
                "debug_scrape_one": "/debug/scrape-one?url=<passmark_url>",
                "debug_top_list": "/debug/top-list?type=<CPU|GPU>&limit=10",
                "debug_analyze_page": "/debug/analyze-page?url=<passmark_url>"
            }
        }

