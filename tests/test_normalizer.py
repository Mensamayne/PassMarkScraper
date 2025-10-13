"""Tests for component normalizer."""
import pytest
from app.normalizer import normalize_name, normalize_component_score, get_tier


def test_normalize_name():
    """Test name normalization."""
    # Test basic normalization
    result = normalize_name("Intel Core i5-12400")
    assert "core" in result.lower() and "i5" in result.lower()
    
    # Test with special characters
    result = normalize_name("AMD Ryzen 9 7950X")
    assert "ryzen" in result.lower() and "7950" in result.lower()
    
    # Test with spaces and special chars
    result = normalize_name("NVIDIA GeForce RTX 4090")
    assert "rtx" in result.lower() and "4090" in result.lower()


def test_normalize_component_score():
    """Test score normalization."""
    # Test CPU score normalization
    result = normalize_component_score("CPU", 10000)
    assert isinstance(result, (int, float))
    assert result > 0
    
    # Test GPU score normalization
    result = normalize_component_score("GPU", 20000)
    assert isinstance(result, (int, float))
    assert result > 0
    
    # Test RAM score normalization
    result = normalize_component_score("RAM", 5000)
    assert isinstance(result, (int, float))
    assert result > 0
    
    # Test STORAGE score normalization
    result = normalize_component_score("STORAGE", 3000)
    assert isinstance(result, (int, float))
    assert result > 0


def test_get_tier():
    """Test tier calculation."""
    # Test different score ranges
    result = get_tier(10)
    assert result in ["low", "mid", "high", "enthusiast", "ultra"]
    
    result = get_tier(50)
    assert result in ["low", "mid", "high", "enthusiast", "ultra"]
    
    result = get_tier(90)
    assert result in ["low", "mid", "high", "enthusiast", "ultra"]
    
    result = get_tier(100)
    assert result in ["low", "mid", "high", "enthusiast", "ultra"]


def test_normalize_edge_cases():
    """Test normalization edge cases."""
    # Test empty string
    result = normalize_name("")
    assert result == ""
    
    # Test very long name
    long_name = "A" * 100
    result = normalize_name(long_name)
    assert len(result) > 0
    
    # Test with numbers only
    result = normalize_name("12345")
    assert result == "12345"
