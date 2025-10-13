"""Tests for component filters."""
import pytest
from app.filters import categorize_component


def test_categorize_consumer_cpu():
    """Test categorizing consumer CPU."""
    result = categorize_component("Intel Core i5-12400", "CPU")
    assert result == "consumer"


def test_categorize_workstation_cpu():
    """Test categorizing workstation CPU."""
    result = categorize_component("Intel Xeon E5-2680", "CPU")
    assert result == "server"  # Xeon E5 is classified as server


def test_categorize_server_cpu():
    """Test categorizing server CPU."""
    result = categorize_component("Intel Xeon Platinum 8280", "CPU")
    assert result == "server"


def test_categorize_consumer_gpu():
    """Test categorizing consumer GPU."""
    result = categorize_component("NVIDIA GeForce RTX 4090", "GPU")
    assert result == "consumer"


def test_categorize_workstation_gpu():
    """Test categorizing workstation GPU."""
    result = categorize_component("NVIDIA Quadro RTX 6000", "GPU")
    assert result == "workstation"


def test_categorize_server_gpu():
    """Test categorizing server GPU."""
    result = categorize_component("NVIDIA Tesla V100", "GPU")
    assert result == "server"


def test_categorize_ram():
    """Test categorizing RAM."""
    result = categorize_component("Corsair Vengeance LPX 16GB", "RAM")
    assert result == "consumer"


def test_categorize_storage():
    """Test categorizing storage."""
    result = categorize_component("Samsung 980 PRO 1TB", "STORAGE")
    assert result == "consumer"
