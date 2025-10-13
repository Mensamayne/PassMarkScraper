"""Global scraping status tracker."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import threading


@dataclass
class ScrapeStatus:
    """Track scraping progress."""

    is_running: bool = False
    component_type: Optional[str] = None
    started_at: Optional[str] = None
    current_progress: int = 0
    total_items: int = 0
    saved_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    current_item: Optional[str] = None
    errors: list = field(default_factory=list)

    def start(self, component_type: str, total: int):
        """Start scraping."""
        self.is_running = True
        self.component_type = component_type
        self.started_at = datetime.now().isoformat()
        self.current_progress = 0
        self.total_items = total
        self.saved_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.current_item = None
        self.errors = []

    def update(self, current: int, item_name: str = None):
        """Update progress."""
        self.current_progress = current
        if item_name:
            self.current_item = item_name

    def increment_saved(self):
        """Increment saved count."""
        self.saved_count += 1

    def increment_skipped(self):
        """Increment skipped count."""
        self.skipped_count += 1

    def add_error(self, error_msg: str):
        """Add error message."""
        self.error_count += 1
        self.errors.append({"timestamp": datetime.now().isoformat(), "message": error_msg})
        # Keep only last 10 errors
        if len(self.errors) > 10:
            self.errors = self.errors[-10:]

    def finish(self):
        """Finish scraping."""
        self.is_running = False
        self.current_item = None

    def to_dict(self):
        """Convert to dict."""
        return {
            "is_running": self.is_running,
            "component_type": self.component_type,
            "started_at": self.started_at,
            "progress": {
                "current": self.current_progress,
                "total": self.total_items,
                "percentage": (
                    round((self.current_progress / self.total_items * 100), 1)
                    if self.total_items > 0
                    else 0
                ),
            },
            "stats": {
                "saved": self.saved_count,
                "skipped": self.skipped_count,
                "errors": self.error_count,
            },
            "current_item": self.current_item,
            "recent_errors": self.errors[-5:] if self.errors else [],
        }


# Global status instance
_status = ScrapeStatus()
_status_lock = threading.Lock()


def get_status() -> ScrapeStatus:
    """Get global status."""
    return _status


def update_status(**kwargs):
    """Thread-safe status update."""
    with _status_lock:
        for key, value in kwargs.items():
            if hasattr(_status, key):
                setattr(_status, key, value)
