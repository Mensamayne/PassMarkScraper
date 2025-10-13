"""Scheduler for automatic scraping."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import requests

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None
_scheduler_enabled = False


def init_scheduler(config: dict):
    """
    Initialize scheduler based on configuration.

    Config format:
    {
        "scheduler": {
            "enabled": true,
            "scrape_time": "03:00",
            "scrape_days": "sunday",
            "timezone": "UTC"
        }
    }
    """
    global _scheduler, _scheduler_enabled

    scheduler_config = config.get("scheduler", {})
    _scheduler_enabled = scheduler_config.get("enabled", False)

    if not _scheduler_enabled:
        logger.info("Scheduler disabled in configuration")
        return None

    _scheduler = BackgroundScheduler()

    # Parse schedule
    scrape_time = scheduler_config.get("scrape_time", "03:00")
    scrape_days = scheduler_config.get("scrape_days", "sunday")
    timezone = scheduler_config.get("timezone", "UTC")

    hour, minute = scrape_time.split(":")

    # Map day names to cron day_of_week
    day_map = {
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun",
    }

    day_of_week = day_map.get(scrape_days.lower(), "sun")

    # Add job
    _scheduler.add_job(
        scheduled_scrape_all,
        CronTrigger(day_of_week=day_of_week, hour=int(hour), minute=int(minute), timezone=timezone),
        id="scrape_all_job",
        name="Weekly PassMark Scrape",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(f"Scheduler started: {scrape_days} at {scrape_time} {timezone}")

    return _scheduler


def scheduled_scrape_all():
    """Execute full scrape (called by scheduler)."""
    logger.info("=== SCHEDULED SCRAPE STARTED ===")

    try:
        # Get API URL from environment or use default
        import os

        api_host = os.getenv("API_HOST", "localhost")
        api_port = os.getenv("API_PORT", "9091")
        base_url = f"http://{api_host}:{api_port}"

        # Call scrape endpoint for each component type
        component_types = ["CPU", "GPU", "RAM", "STORAGE"]

        for comp_type in component_types:
            logger.info(f"Scraping {comp_type}...")

            try:
                response = requests.post(
                    f"{base_url}/scrape-and-save",
                    params={
                        "type": comp_type,
                        "limit": 10000,  # High limit for all components
                        "include_workstation": False,
                        "skip_backup": False,  # Create backup
                    },
                    timeout=600,
                )

                if response.status_code == 200:
                    result = response.json()
                    saved = result.get("saved", 0)
                    skipped = result.get("skipped", 0)
                    logger.info(f"{comp_type}: Saved {saved}, Skipped {skipped}")
                else:
                    logger.error(f"{comp_type}: HTTP {response.status_code}")

            except Exception as e:
                logger.error(f"Failed to scrape {comp_type}: {e}")

        logger.info("=== SCHEDULED SCRAPE COMPLETED ===")

    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")


def get_scheduler():
    """Get scheduler instance."""
    return _scheduler


def is_scheduler_enabled():
    """Check if scheduler is enabled."""
    return _scheduler_enabled


def get_scheduler_status():
    """Get scheduler status and next run time."""
    if not _scheduler or not _scheduler_enabled:
        return {"enabled": False, "running": False}

    jobs = _scheduler.get_jobs()
    next_run = None

    if jobs:
        job = jobs[0]
        next_run = job.next_run_time.isoformat() if job.next_run_time else None

    return {"enabled": True, "running": _scheduler.running, "jobs": len(jobs), "next_run": next_run}


def start_scheduler():
    """Start the scheduler."""
    if _scheduler and not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler started manually")
        return True
    return False


def stop_scheduler():
    """Stop the scheduler."""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped manually")
        return True
    return False
