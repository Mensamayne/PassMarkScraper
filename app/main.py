"""FastAPI application for PassMark benchmark microservice."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models import (
    ScrapeResult,
    PairingAnalysisRequest,
    PairingAnalysisResponse,
    CategoryAnalysis,
    RecommendPairingRequest,
    RecommendPairingResponse,
    ComponentRecommendation,
    GamingProfileRequest,
    GamingProfileResponse,
    GameCategoryPerformance,
    PerformanceEstimateResponse,
    BenchmarkResponse,
)
from app.scraper import scrape_single_component
from app.list_scraper import scrape_top_components
from app.page_analyzer import analyze_component_page
from app.database import Database
from app.filters import categorize_component, is_desktop_component
from app.normalizer import normalize_name, normalize_component_score, get_tier
from app.backup import create_backup, list_backups, restore_backup
from app.scrape_status import get_status
from app.recommendation import analyze_pairing, recommend_components
from app.gaming_profiles import (
    GAME_CATEGORIES,
    get_performance_tier_for_resolution,
    estimate_fps,
)
from app.power_analysis import estimate_system_power, calculate_monthly_cost
from app.scheduler import (
    init_scheduler,
    get_scheduler_status,
    start_scheduler as start_sched,
    stop_scheduler as stop_sched,
)
from app.config_loader import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
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
        if scheduler_status["enabled"]:
            logger.info(
                f"Scheduler initialized. Next run: {scheduler_status.get('next_run', 'N/A')}"
            )
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
    lifespan=lifespan,
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

    return {"status": "ok", "db_path": db_path, "db_exists": db_exists, "db_count": db.get_count()}


@app.get("/debug/scrape-one", response_model=ScrapeResult)
async def debug_scrape_one(url: str = Query(..., description="PassMark component URL")):
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
            "tier": tier,
        }

        return ScrapeResult(
            raw_data=raw_data,
            normalized=normalized,
            would_insert_sql="Debug SQL removed for security",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape error: {str(e)}")


@app.get("/search")
async def search_benchmark(
    name: str = Query(..., description="Component name to search"),
    type: str = Query(None, description="Component type (CPU, GPU, RAM, STORAGE) - optional"),
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
            return {"found": True, "component": result}
        else:
            return {"found": False, "error": "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/api/search-enhanced")
async def search_enhanced(request: dict):
    """
    Enhanced search with fuzzy matching and chipset extraction.
    
    Request body:
    {
        "query": "INNO3D RTX5080 ICHILL FROSTBITE PRO 16GB",
        "component_type": "gpu"
    }
    
    Response:
    {
        "matches": [
            {
                "name": "GeForce RTX 5080",
                "passmark_score": 36156,
                "normalized_score": 100,
                "confidence": 0.95,
                "match_type": "chipset_extracted"
            }
        ],
        "fallback_used": false
    }
    """
    try:
        query = request.get("query", "")
        component_type = request.get("component_type", "").upper()
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        # Use enhanced search from database
        matches = db.search_enhanced(query, component_type)
        
        return {
            "matches": matches,
            "fallback_used": len(matches) == 0,
            "query": query,
            "component_type": component_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced search error: {str(e)}")


@app.get("/debug/top-list")
async def debug_top_list(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of top components to return"),
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
            executor, scrape_top_components, type.upper(), limit
        )

        # Add normalized scores
        for comp in components:
            normalized_score = normalize_component_score(type, comp["passmark_score"])
            comp["normalized_score"] = normalized_score
            comp["tier"] = get_tier(normalized_score)

        return {"component_type": type.upper(), "count": len(components), "components": components}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape error: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/scrape-and-save")
async def scrape_and_save_top(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of top components to scrape"),
    include_workstation: bool = Query(True, description="Include workstation components"),
    skip_backup: bool = Query(False, description="Skip automatic backup before scraping"),
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
            limit * 2,  # Get more to account for filtering
        )

        status.total_items = len(components)
        saved_count = 0
        skipped_count = 0
        results = []

        for idx, comp in enumerate(components):
            if saved_count >= limit:
                break

            # Update progress
            status.update(idx + 1, comp["name"])

            # Check if should include
            category = categorize_component(comp["name"], type.upper())

            if category == "server":
                skipped_count += 1
                status.increment_skipped()
                continue

            if not include_workstation and category == "workstation":
                skipped_count += 1
                status.increment_skipped()
                continue

            # Normalize scores
            normalized_score = normalize_component_score(type, comp["passmark_score"])

            # Prepare data for database
            db_data = {
                "name": comp["name"],
                "normalized_name": normalize_name(comp["name"]),
                "component_type": type.upper(),
                "category": category,
                "passmark_score": comp["passmark_score"],
                "normalized_score": normalized_score,
                "tier": get_tier(normalized_score),
            }

            # Save to database
            try:
                db.insert_component(db_data)
                saved_count += 1
                status.increment_saved()

                results.append(
                    {"name": comp["name"], "category": category, "score": comp["passmark_score"]}
                )
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
            "components": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape and save error: {str(e)}")


@app.get("/list")
async def list_components(
    type: str = Query(..., description="Component type (CPU, GPU, RAM, STORAGE)"),
    limit: int = Query(10, description="Number of components to return"),
    category: str = Query(None, description="Filter by category (consumer, workstation)"),
):
    """
    List top components from database.

    Example:
        /list?type=GPU&limit=10&category=consumer
    """
    try:
        components = db.get_top_components(type.upper(), limit * 2, category)  # Get 2x to account for filtering
        
        # Runtime filter to exclude mobile/laptop components
        if category == "consumer":
            components = [
                c for c in components
                if is_desktop_component(c.get("name", ""), type.upper())
            ][:limit]  # Apply limit after filtering

        return {
            "type": type.upper(),
            "category": category or "all",
            "count": len(components),
            "components": components,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List error: {str(e)}")


@app.get("/compare")
async def compare_components(
    component1: str = Query(..., description="First component name (e.g., 'gtx 1080ti')"),
    component2: str = Query(..., description="Second component name (e.g., 'rtx 3080')"),
    type: str = Query(None, description="Component type (CPU, GPU, RAM, STORAGE) - optional"),
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
            return {"found": False, "error": "both_not_found"}

        if not result1:
            return {
                "found": False,
                "error": "component1_not_found",
                "component2": {
                    "name": result2["name"],
                    "passmark_score": result2["passmark_score"],
                    "normalized_score": result2["normalized_score"],
                    "tier": result2["tier"],
                },
            }

        if not result2:
            return {
                "found": False,
                "error": "component2_not_found",
                "component1": {
                    "name": result1["name"],
                    "passmark_score": result1["passmark_score"],
                    "normalized_score": result1["normalized_score"],
                    "tier": result1["tier"],
                },
            }

        # Both found - compare them
        score1 = result1["passmark_score"]
        score2 = result2["passmark_score"]
        norm1 = result1["normalized_score"]
        norm2 = result2["normalized_score"]

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
                "name": result1["name"],
                "passmark_score": score1,
                "normalized_score": norm1,
                "tier": result1["tier"],
                "category": result1.get("category"),
                "tdp": result1.get("tdp"),
            },
            "component2": {
                "name": result2["name"],
                "passmark_score": score2,
                "normalized_score": norm2,
                "tier": result2["tier"],
                "category": result2.get("category"),
                "tdp": result2.get("tdp"),
            },
            "comparison": {
                "passmark_difference": score_diff,
                "passmark_difference_percent": score_diff_percent,
                "normalized_difference": norm_diff,
                "component1_faster": score1 > score2,
                "component2_faster": score2 > score1,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@app.get("/config")
async def get_config():
    """Get current configuration."""
    from app.config_loader import config

    cfg = config.get_config()
    return {
        "database": cfg.get("database", {}),
        "api": cfg.get("api", {}),
        "scraping": cfg.get("scraping", {}),
        "sources": cfg.get("sources", {}),
        "scheduler": cfg.get("scheduler", {}),
        "recommendation": cfg.get("recommendation", {}),
    }


@app.put("/config")
async def update_config(new_config: dict):
    """Update configuration (requires restart to take full effect)."""
    import json

    try:
        # Backup current config
        config_path = Path("config/config.json")
        backup_path = Path("config/config.json.backup")

        if config_path.exists():
            import shutil

            shutil.copy(config_path, backup_path)

        # Write new config
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=2)

        return {
            "success": True,
            "message": "Configuration updated. Restart service for full effect.",
            "backup_created": str(backup_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


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
            "config": {"scraping": cfg.get("scraping", {}), "api": cfg.get("api", {})},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")


@app.get("/backup/list")
async def list_database_backups():
    """List all available database backups."""
    try:
        backups = list_backups()
        return {"count": len(backups), "backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@app.post("/backup/create")
async def create_database_backup():
    """Create a manual backup of the database."""
    try:
        backup_path = create_backup()
        return {"success": True, "message": "Backup created", "backup_path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@app.post("/backup/restore")
async def restore_database_backup(
    filename: str = Query(..., description="Backup filename to restore")
):
    """Restore database from backup."""
    try:
        restore_backup(filename)
        return {
            "success": True,
            "message": f"Database restored from {filename}",
            "db_count": db.get_count(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")


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
                "status": get_scheduler_status(),
            }
        else:
            return {"success": False, "message": "Scheduler already running or not configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@app.post("/scheduler/stop")
async def scheduler_stop():
    """Stop the scheduler."""
    try:
        if stop_sched():
            return {"success": True, "message": "Scheduler stopped"}
        else:
            return {"success": False, "message": "Scheduler not running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@app.post("/analyze-pairing")
async def analyze_cpu_gpu_pairing(request: PairingAnalysisRequest):
    """
    Analyze CPU+GPU pairing for bottlenecks and balance.

    Example:
        POST /analyze-pairing
        {"cpu": "Ryzen 7 7800X3D", "gpu": "RTX 4070"}
    """
    try:
        # Get config for suggestions
        rec_config = config.get_config().get("recommendation", {})
        enable_suggestions = rec_config.get("enable_suggestions", True)
        max_suggestions = rec_config.get("max_suggestions", 3)

        # Search for CPU
        cpu_result = db.search_component(request.cpu, "CPU")
        if not cpu_result:
            # Provide suggestions if enabled
            if enable_suggestions:
                similar = db.search_enhanced(request.cpu, "CPU")[:max_suggestions]
                suggestions = [s["name"] for s in similar] if similar else []
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "CPU not found",
                        "query": request.cpu,
                        "suggestions": suggestions,
                        "message": f"Did you mean: {', '.join(suggestions[:2])}" if suggestions else "Try a different search"
                    }
                )
            else:
                raise HTTPException(
                    status_code=404, detail=f"CPU not found: {request.cpu}"
                )

        # Search for GPU
        gpu_result = db.search_component(request.gpu, "GPU")
        if not gpu_result:
            # Provide suggestions if enabled
            if enable_suggestions:
                similar = db.search_enhanced(request.gpu, "GPU")[:max_suggestions]
                suggestions = [s["name"] for s in similar] if similar else []
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "GPU not found",
                        "query": request.gpu,
                        "suggestions": suggestions,
                        "message": f"Did you mean: {', '.join(suggestions[:2])}" if suggestions else "Try a different search"
                    }
                )
            else:
                raise HTTPException(
                    status_code=404, detail=f"GPU not found: {request.gpu}"
                )

        # Perform analysis
        analysis = analyze_pairing(cpu_result, gpu_result)

        # Build response with proper models
        cpu_response = BenchmarkResponse(
            name=cpu_result["name"],
            passmark_score=cpu_result["passmark_score"],
            normalized_score=cpu_result["normalized_score"],
            tier=cpu_result["tier"],
        )

        gpu_response = BenchmarkResponse(
            name=gpu_result["name"],
            passmark_score=gpu_result["passmark_score"],
            normalized_score=gpu_result["normalized_score"],
            tier=gpu_result["tier"],
        )

        # Convert category analyses to models
        by_category = {}
        for cat_name, cat_data in analysis["by_category"].items():
            by_category[cat_name] = CategoryAnalysis(**cat_data)

        return PairingAnalysisResponse(
            cpu=cpu_response,
            gpu=gpu_response,
            overall_balance_score=analysis["overall_balance_score"],
            overall_verdict=analysis["overall_verdict"],
            overall_bottleneck=analysis.get("overall_bottleneck"),
            by_category=by_category,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pairing analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/recommend-pairing")
async def recommend_pairing(
    cpu: str = Query(None, description="CPU name (provide either CPU or GPU)"),
    gpu: str = Query(None, description="GPU name (provide either CPU or GPU)"),
    game_focus: str = Query(
        None,
        description="Game category focus: esport, aaa_gpu, balanced, simulation",
    ),
    limit: int = Query(5, description="Max recommendations"),
):
    """
    Recommend compatible CPU or GPU based on what you have.

    Examples:
        /recommend-pairing?cpu=7800X3D&game_focus=aaa_gpu
        /recommend-pairing?gpu=RTX4090&game_focus=simulation
    """
    try:
        if not cpu and not gpu:
            raise HTTPException(
                status_code=400, detail="Must provide either cpu or gpu parameter"
            )

        if cpu and gpu:
            raise HTTPException(
                status_code=400, detail="Provide only one component (cpu OR gpu)"
            )

        # Validate game_focus
        if game_focus and game_focus not in GAME_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid game_focus. Must be one of: {', '.join(GAME_CATEGORIES.keys())}",
            )

        # Determine base component
        if cpu:
            base_result = db.search_component(cpu, "CPU")
            if not base_result:
                raise HTTPException(status_code=404, detail=f"CPU not found: {cpu}")
            component_type = "CPU"
            recommend_type = "GPU"
        else:
            base_result = db.search_component(gpu, "GPU")
            if not base_result:
                raise HTTPException(status_code=404, detail=f"GPU not found: {gpu}")
            component_type = "GPU"
            recommend_type = "CPU"

        # Get all components of the type we're recommending (desktop consumer only)
        all_candidates = db.get_top_components(recommend_type, limit=4000, category='consumer')

        # Get recommendations
        recommendations = recommend_components(
            base_result, component_type, all_candidates, game_focus, limit
        )

        # Build response
        base_component = BenchmarkResponse(
            name=base_result["name"],
            passmark_score=base_result["passmark_score"],
            normalized_score=base_result["normalized_score"],
            tier=base_result["tier"],
        )

        rec_list = []
        for rec in recommendations:
            comp = rec["component"]
            match_score = rec["match_score"]

            # Build balance description
            if match_score >= 90:
                balance_desc = "Perfect match"
            elif match_score >= 80:
                balance_desc = "Excellent balance"
            elif match_score >= 70:
                balance_desc = "Very good balance"
            else:
                balance_desc = "Good balance"

            rec_list.append(
                ComponentRecommendation(
                    name=comp["name"],
                    passmark_score=comp["passmark_score"],
                    normalized_score=comp["normalized_score"],
                    tier=comp["tier"],
                    match_score=match_score,
                    balance_description=balance_desc,
                )
            )

        return RecommendPairingResponse(
            base_component=base_component,
            base_component_type=component_type,
            game_focus=game_focus,
            recommendations=rec_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


@app.post("/gaming-profile")
async def gaming_profile(request: GamingProfileRequest):
    """
    Get comprehensive gaming performance profile for CPU+GPU combo.

    Example:
        POST /gaming-profile
        {"cpu": "7800X3D", "gpu": "RTX4070", "resolution": "1440p"}
    """
    try:
        # Validate resolution
        if request.resolution not in ["1080p", "1440p", "4K"]:
            raise HTTPException(
                status_code=400,
                detail="Resolution must be one of: 1080p, 1440p, 4K",
            )

        # Search components
        cpu_result = db.search_component(request.cpu, "CPU")
        if not cpu_result:
            raise HTTPException(
                status_code=404, detail=f"CPU not found: {request.cpu}"
            )

        gpu_result = db.search_component(request.gpu, "GPU")
        if not gpu_result:
            raise HTTPException(
                status_code=404, detail=f"GPU not found: {request.gpu}"
            )

        # Analyze pairing
        analysis = analyze_pairing(cpu_result, gpu_result)

        # Build performance by category
        performance_by_category = {}
        for cat_name, category in GAME_CATEGORIES.items():
            cat_analysis = analysis["by_category"][cat_name]

            # Build FPS estimate string
            if cat_analysis["performance"] == "excellent":
                if cat_name == "esport":
                    fps_estimate = "300-500+ FPS"
                elif cat_name == "aaa_gpu":
                    fps_estimate = f"100-120 FPS @ {request.resolution} Ultra"
                elif cat_name == "balanced":
                    fps_estimate = f"120-144 FPS @ {request.resolution} Ultra"
                else:  # simulation
                    fps_estimate = f"60-90 FPS @ {request.resolution}"
            elif cat_analysis["performance"] == "very_good":
                if cat_name == "esport":
                    fps_estimate = "200-300+ FPS"
                elif cat_name == "aaa_gpu":
                    fps_estimate = f"80-100 FPS @ {request.resolution} Ultra"
                elif cat_name == "balanced":
                    fps_estimate = f"90-120 FPS @ {request.resolution} Ultra"
                else:
                    fps_estimate = f"45-60 FPS @ {request.resolution}"
            else:
                fps_estimate = "Performance may vary"

            # Settings recommendation
            if cat_analysis["balance_score"] >= 85:
                settings = "Ultra"
            elif cat_analysis["balance_score"] >= 70:
                settings = "High-Ultra"
            elif cat_analysis["balance_score"] >= 50:
                settings = "Medium-High"
            else:
                settings = "Medium"

            performance_by_category[cat_name] = GameCategoryPerformance(
                games=category["examples"],
                fps_estimate=fps_estimate,
                settings=settings,
                bottleneck=cat_analysis["bottleneck"],
                cpu_utilization=f"{cat_analysis['cpu_utilization']}%",
                gpu_utilization=f"{cat_analysis['gpu_utilization']}%",
            )

        # Build upgrade recommendations
        upgrade_recommendations = {}
        if analysis["overall_bottleneck"] == "cpu":
            upgrade_recommendations["priority"] = "CPU"
            upgrade_recommendations[
                "reason"
            ] = "CPU is bottlenecking GPU performance"
        elif analysis["overall_bottleneck"] == "gpu":
            upgrade_recommendations["priority"] = "GPU"
            upgrade_recommendations[
                "reason"
            ] = "GPU is bottlenecking overall performance"
        else:
            upgrade_recommendations["priority"] = "None"
            upgrade_recommendations["reason"] = "System is well balanced"

        # Response models
        cpu_response = BenchmarkResponse(
            name=cpu_result["name"],
            passmark_score=cpu_result["passmark_score"],
            normalized_score=cpu_result["normalized_score"],
            tier=cpu_result["tier"],
        )

        gpu_response = BenchmarkResponse(
            name=gpu_result["name"],
            passmark_score=gpu_result["passmark_score"],
            normalized_score=gpu_result["normalized_score"],
            tier=gpu_result["tier"],
        )

        return GamingProfileResponse(
            cpu=cpu_response,
            gpu=gpu_response,
            resolution=request.resolution,
            overall_balance_score=analysis["overall_balance_score"],
            overall_verdict=analysis["overall_verdict"],
            performance_by_category=performance_by_category,
            upgrade_recommendations=upgrade_recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gaming profile error: {e}")
        raise HTTPException(status_code=500, detail=f"Profile error: {str(e)}")


@app.get("/estimate-performance")
async def estimate_performance(
    component: str = Query(..., description="Component name"),
    type: str = Query(..., description="Component type (CPU or GPU)"),
):
    """
    Estimate gaming performance for a component.

    Example:
        /estimate-performance?component=RTX4070&type=GPU
    """
    try:
        # Validate type
        if type.upper() not in ["CPU", "GPU"]:
            raise HTTPException(
                status_code=400, detail="Type must be CPU or GPU"
            )

        # Search component
        result = db.search_component(component, type.upper())
        if not result:
            raise HTTPException(
                status_code=404, detail=f"{type.upper()} not found: {component}"
            )

        # Build performance estimates (use normalized score 0-100)
        estimated_performance = {
            "1080p_low": f"{estimate_fps(result['normalized_score'], '1080p', 'low', 'balanced')}+ FPS",
            "1080p_medium": f"{estimate_fps(result['normalized_score'], '1080p', 'medium', 'balanced')}+ FPS",
            "1080p_high": f"{estimate_fps(result['normalized_score'], '1080p', 'high', 'balanced')}+ FPS",
            "1080p_ultra": f"{estimate_fps(result['normalized_score'], '1080p', 'ultra', 'balanced')}+ FPS",
            "1440p_high": f"{estimate_fps(result['normalized_score'], '1440p', 'high', 'balanced')}+ FPS",
            "1440p_ultra": f"{estimate_fps(result['normalized_score'], '1440p', 'ultra', 'balanced')}+ FPS",
            "4K_high": f"{estimate_fps(result['normalized_score'], '4K', 'high', 'balanced')}+ FPS",
            "4K_ultra": f"{estimate_fps(result['normalized_score'], '4K', 'ultra', 'balanced')}+ FPS",
        }

        # Gaming tiers
        gaming_tiers = {
            "1080p": get_performance_tier_for_resolution(
                result["normalized_score"], "1080p"
            ),
            "1440p": get_performance_tier_for_resolution(
                result["normalized_score"], "1440p"
            ),
            "4K": get_performance_tier_for_resolution(
                result["normalized_score"], "4K"
            ),
        }

        return PerformanceEstimateResponse(
            component_name=result["name"],
            component_type=type.upper(),
            passmark_score=result["passmark_score"],
            normalized_score=result["normalized_score"],
            tier=result["tier"],
            estimated_performance=estimated_performance,
            gaming_tiers=gaming_tiers,
            note="Estimates based on synthetic benchmarks and real-world correlations. Actual performance varies by game optimization.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance estimation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Estimation error: {str(e)}"
        )


@app.get("/game-categories")
async def get_game_categories():
    """
    Get list of all game categories with their characteristics.

    Example:
        /game-categories
    """
    categories = {}
    for name, data in GAME_CATEGORIES.items():
        categories[name] = {
            "display_name": data["display_name"],
            "description": data["description"],
            "cpu_importance": f"{int(data['cpu_importance'] * 100)}%",
            "gpu_importance": f"{int(data['gpu_importance'] * 100)}%",
            "weight_in_analysis": f"{int(data['weight'] * 100)}%",
            "examples": data["examples"],
        }

    return {"categories": categories}


@app.post("/power-analysis")
async def power_analysis_endpoint(request: PairingAnalysisRequest):
    """
    Analyze power consumption and cooling requirements for CPU+GPU pairing.

    Example:
        POST /power-analysis
        {"cpu": "Ryzen 7 7800X3D", "gpu": "RTX 4070"}
    """
    try:
        # Search for CPU
        cpu_result = db.search_component(request.cpu, "CPU")
        if not cpu_result:
            raise HTTPException(
                status_code=404, detail=f"CPU not found: {request.cpu}"
            )

        # Search for GPU
        gpu_result = db.search_component(request.gpu, "GPU")
        if not gpu_result:
            raise HTTPException(
                status_code=404, detail=f"GPU not found: {request.gpu}"
            )

        # Perform power analysis
        power_data = estimate_system_power(cpu_result, gpu_result)
        
        # Add cost estimates (default 4 hours/day, $0.15/kWh)
        gaming_power_cost = calculate_monthly_cost(
            power_data["estimated_gaming_power"],
            hours_per_day=4.0,
            cost_per_kwh=0.15
        )
        
        idle_power_cost = calculate_monthly_cost(
            power_data["estimated_idle_power"],
            hours_per_day=20.0,  # 20 hours idle per day
            cost_per_kwh=0.15
        )

        return {
            "cpu": {
                "name": cpu_result["name"],
                "tdp": power_data["cpu_tdp"]
            },
            "gpu": {
                "name": gpu_result["name"],
                "tdp": power_data["gpu_tdp"]
            },
            "power_consumption": {
                "total_tdp": power_data["total_tdp"],
                "idle_power": power_data["estimated_idle_power"],
                "gaming_power": power_data["estimated_gaming_power"],
                "max_power": power_data["estimated_max_power"],
            },
            "psu_recommendation": {
                "recommended_wattage": power_data["recommended_psu"],
                "wattage_range": power_data["recommended_psu_range"],
                "efficiency_rating": power_data["efficiency_rating"],
            },
            "thermal": {
                "heat_class": power_data["heat_class"],
                "cooling_recommendation": power_data["cooling_recommendation"],
            },
            "operating_costs": {
                "gaming": gaming_power_cost,
                "idle": idle_power_cost,
                "combined_monthly_usd": round(
                    gaming_power_cost["monthly_cost_usd"] + 
                    idle_power_cost["monthly_cost_usd"], 
                    2
                ),
                "combined_yearly_usd": round(
                    gaming_power_cost["yearly_cost_usd"] + 
                    idle_power_cost["yearly_cost_usd"], 
                    2
                ),
            },
            "note": "Estimates based on typical usage. Actual consumption may vary."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Power analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    html_file = Path("static/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    else:
        return {
            "name": "PassMark Scraper API",
            "version": "2.0.0",
            "status": "Production Ready",
            "db_count": db.get_count(),
            "features": {
                "benchmarks": "28k+ components with PassMark scores",
                "comparison": "Compare component performance",
                "recommendations": "CPU+GPU pairing recommendations",
                "bottleneck_analysis": "Intelligent bottleneck detection",
                "gaming_profiles": "Performance estimates per game type",
            },
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "search": "/search?name=<component>&type=<CPU|GPU>",
                "compare": "/compare?component1=<name>&component2=<name>",
                "analyze_pairing": "POST /analyze-pairing - Analyze CPU+GPU pairing",
                "recommend_pairing": "/recommend-pairing?cpu=<name> - Get GPU recommendations",
                "gaming_profile": "POST /gaming-profile - Get gaming performance profile",
                "estimate_performance": "/estimate-performance?component=<name>&type=<CPU|GPU>",
                "power_analysis": "POST /power-analysis - PSU & thermal analysis",
                "game_categories": "/game-categories - List game categories",
            },
        }
