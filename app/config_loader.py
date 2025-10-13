"""Configuration loader."""

import json
from pathlib import Path
from typing import Dict, Any


class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self):
        """Load configuration from config.json."""
        config_path = Path("config/config.json")
        if not config_path.exists():
            # Fallback to default
            self._config = self._default_config()
        else:
            with open(config_path, "r") as f:
                self._config = json.load(f)

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            "database": {"path": "benchmarks.db"},
            "api": {"host": "0.0.0.0", "port": 9091},
            "scraping": {
                "limits": {"cpu": -1, "gpu": -1, "ram": -1, "storage": -1},
                "include_workstation": False,
            },
        }

    def get_db_path(self) -> str:
        """Get database path."""
        return self._config.get("database", {}).get("path", "benchmarks.db")

    def get_scraping_limit(self, component_type: str) -> int:
        """Get scraping limit for component type. -1 means all."""
        limits = self._config.get("scraping", {}).get("limits", {})
        return limits.get(component_type.lower(), 100)

    def get_include_workstation(self) -> bool:
        """Get whether to include workstation components."""
        return self._config.get("scraping", {}).get("include_workstation", False)

    def get_use_full_lists(self) -> bool:
        """Get whether to use full component lists (all CPUs/GPUs) or just high-end lists."""
        return self._config.get("scraping", {}).get("use_full_lists", False)

    def get_config(self) -> dict:
        """Get full configuration dict."""
        return self._config.copy()

    def get_scheduler_config(self) -> dict:
        """Get scheduler configuration."""
        return self._config.get("scheduler", {})


# Global config instance
config = Config()
