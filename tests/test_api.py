"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200


def test_config_endpoint():
    """Test config endpoint."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "api" in data


def test_search_endpoint():
    """Test search endpoint with valid parameters."""
    response = client.get("/search?name=test&type=CPU")
    assert response.status_code == 200
    data = response.json()
    assert "found" in data


def test_compare_endpoint():
    """Test compare endpoint with valid parameters."""
    response = client.get("/compare?component1=test1&component2=test2")
    assert response.status_code == 200
    data = response.json()
    assert "found" in data


def test_list_endpoint():
    """Test list endpoint with valid parameters."""
    response = client.get("/list?type=CPU&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "type" in data
    assert "count" in data


def test_scheduler_status():
    """Test scheduler status endpoint."""
    response = client.get("/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data


def test_scrape_status():
    """Test scrape status endpoint."""
    response = client.get("/scrape-status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data


def test_backup_list():
    """Test backup list endpoint."""
    response = client.get("/backup/list")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "backups" in data
