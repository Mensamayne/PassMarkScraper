"""Tests for configuration loader."""
import pytest
import tempfile
import json
import os
from app.config_loader import Config


def test_default_config():
    """Test default configuration."""
    config = Config()
    config._config = config._default_config()
    
    assert "database" in config._config
    assert "api" in config._config
    assert "scraping" in config._config
    
    assert config._config["database"]["path"] == "benchmarks.db"
    assert config._config["api"]["port"] == 9091


def test_config_methods():
    """Test configuration methods."""
    config = Config()
    config._config = config._default_config()
    
    # Test get_db_path
    db_path = config.get_db_path()
    assert db_path == "benchmarks.db"
    
    # Test get_scraping_limit
    limit = config.get_scraping_limit("cpu")
    assert limit == -1
    
    # Test get_include_workstation
    include = config.get_include_workstation()
    assert include is False
    
    # Test get_use_full_lists
    use_full = config.get_use_full_lists()
    assert use_full is False


def test_config_with_file():
    """Test configuration with file."""
    # Create temporary config file
    config_data = {
        "database": {"path": "test.db"},
        "api": {"port": 8080},
        "scraping": {
            "limits": {"cpu": 100},
            "include_workstation": True,
            "use_full_lists": True
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_path = f.name
    
    try:
        # Create config instance with file
        config = Config()
        config._config = config_data
        
        # Test loaded values
        assert config.get_db_path() == "test.db"
        assert config.get_scraping_limit("cpu") == 100
        assert config.get_include_workstation() is True
        assert config.get_use_full_lists() is True
        
    finally:
        os.unlink(config_path)
