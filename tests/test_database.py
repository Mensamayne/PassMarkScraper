"""Tests for database operations."""
import pytest
import tempfile
import os
from app.database import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    yield db
    
    # Cleanup
    os.unlink(db_path)


def test_database_creation(temp_db):
    """Test database creation."""
    assert temp_db is not None


def test_database_count(temp_db):
    """Test database count."""
    count = temp_db.get_count()
    assert count >= 0


def test_database_search(temp_db):
    """Test database search."""
    result = temp_db.search_component("nonexistent", "CPU")
    assert result is None


def test_database_insert(temp_db):
    """Test database insert."""
    component_data = {
        'name': 'Test CPU',
        'normalized_name': 'test_cpu',
        'component_type': 'CPU',
        'category': 'consumer',
        'passmark_score': 1000,
        'normalized_score': 50,
        'tier': 'mid'
    }
    
    temp_db.insert_component(component_data)
    count = temp_db.get_count()
    assert count >= 1


def test_database_get_top_components(temp_db):
    """Test getting top components."""
    components = temp_db.get_top_components("CPU", 10)
    assert isinstance(components, list)
