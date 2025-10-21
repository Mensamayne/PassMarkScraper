"""Tests for gaming profiles module."""

import pytest
from app.gaming_profiles import (
    GAME_CATEGORIES,
    get_category,
    get_all_categories,
    get_category_examples,
    estimate_fps,
    get_performance_tier_for_resolution,
    get_bottleneck_threshold,
)


def test_game_categories_structure():
    """Test that game categories are properly structured."""
    assert "esport" in GAME_CATEGORIES
    assert "aaa_gpu" in GAME_CATEGORIES
    assert "balanced" in GAME_CATEGORIES
    assert "simulation" in GAME_CATEGORIES

    # Check esport category structure
    esport = GAME_CATEGORIES["esport"]
    assert "name" in esport
    assert "cpu_importance" in esport
    assert "gpu_importance" in esport
    assert "weight" in esport
    assert "examples" in esport

    # Check weights sum to proper values
    assert esport["cpu_importance"] == 0.80
    assert esport["gpu_importance"] == 0.20


def test_get_category():
    """Test getting specific category."""
    category = get_category("esport")
    assert category is not None
    assert category["name"] == "esport"

    # Test non-existent category
    category = get_category("nonexistent")
    assert category is None


def test_get_all_categories():
    """Test getting all categories."""
    categories = get_all_categories()
    assert isinstance(categories, dict)
    assert len(categories) == 4
    assert "esport" in categories


def test_get_category_examples():
    """Test getting example games."""
    examples = get_category_examples("esport")
    assert isinstance(examples, list)
    assert len(examples) > 0
    assert any("CS2" in game or "Valorant" in game for game in examples)

    # Test non-existent category
    examples = get_category_examples("nonexistent")
    assert examples == []


def test_estimate_fps():
    """Test FPS estimation."""
    # Test with reasonable scores
    fps = estimate_fps(20000, "1080p", "high", "balanced")
    assert isinstance(fps, int)
    assert fps > 0

    # Higher score should give higher FPS
    fps_high = estimate_fps(30000, "1080p", "high", "balanced")
    fps_low = estimate_fps(10000, "1080p", "high", "balanced")
    assert fps_high > fps_low

    # Resolution impact - higher res = lower FPS
    fps_1080p = estimate_fps(20000, "1080p", "high", "balanced")
    fps_4k = estimate_fps(20000, "4K", "high", "balanced")
    assert fps_1080p > fps_4k

    # Settings impact - ultra = lower FPS than low
    fps_low_settings = estimate_fps(20000, "1080p", "low", "balanced")
    fps_ultra_settings = estimate_fps(20000, "1080p", "ultra", "balanced")
    assert fps_low_settings > fps_ultra_settings

    # Category impact - esport should give highest FPS
    fps_esport = estimate_fps(20000, "1080p", "medium", "esport")
    fps_aaa = estimate_fps(20000, "1080p", "medium", "aaa_gpu")
    assert fps_esport > fps_aaa


def test_get_performance_tier_for_resolution():
    """Test performance tier description."""
    # Test 1080p tiers
    tier = get_performance_tier_for_resolution(90, "1080p")
    assert "ultra" in tier.lower() or "144" in tier

    tier = get_performance_tier_for_resolution(50, "1080p")
    assert "medium" in tier.lower() or "60" in tier

    tier = get_performance_tier_for_resolution(20, "1080p")
    assert "low" in tier.lower()

    # Test 1440p - should be more demanding
    tier = get_performance_tier_for_resolution(70, "1440p")
    assert isinstance(tier, str)
    assert len(tier) > 0

    # Test 4K - most demanding
    tier = get_performance_tier_for_resolution(95, "4K")
    assert isinstance(tier, str)

    # Test unknown resolution
    tier = get_performance_tier_for_resolution(50, "8K")
    assert tier == "unknown"


def test_get_bottleneck_threshold():
    """Test bottleneck threshold calculation."""
    # Test CPU-heavy category
    thresholds = get_bottleneck_threshold("esport")
    assert "cpu_bound" in thresholds
    assert "gpu_bound" in thresholds
    assert isinstance(thresholds["cpu_bound"], (int, float))
    assert isinstance(thresholds["gpu_bound"], (int, float))

    # Test GPU-heavy category
    thresholds = get_bottleneck_threshold("aaa_gpu")
    assert thresholds["cpu_bound"] > thresholds["gpu_bound"]

    # Test balanced category
    thresholds = get_bottleneck_threshold("balanced")
    assert 1.0 < thresholds["cpu_bound"] < 1.5
    assert 0.5 < thresholds["gpu_bound"] < 1.0

    # Test non-existent category (should return defaults)
    thresholds = get_bottleneck_threshold("nonexistent")
    assert "cpu_bound" in thresholds
    assert "gpu_bound" in thresholds


def test_category_weights_sum_correctly():
    """Test that all category weights sum to 1.0."""
    total_weight = sum(cat["weight"] for cat in GAME_CATEGORIES.values())
    assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error


def test_cpu_gpu_importance_sum():
    """Test that CPU and GPU importance sum to 1.0 for each category."""
    for cat_name, category in GAME_CATEGORIES.items():
        total = category["cpu_importance"] + category["gpu_importance"]
        assert (
            abs(total - 1.0) < 0.01
        ), f"Category {cat_name} importance doesn't sum to 1.0"


def test_fps_estimation_edge_cases():
    """Test FPS estimation with edge cases."""
    # Zero score
    fps = estimate_fps(0, "1080p", "medium", "balanced")
    assert fps == 0

    # Very low score
    fps = estimate_fps(100, "1080p", "low", "esport")
    assert fps >= 1  # Should still return at least 1

    # Very high score
    fps = estimate_fps(50000, "1080p", "ultra", "aaa_gpu")
    assert fps > 0
    assert isinstance(fps, int)


def test_resolution_multipliers_make_sense():
    """Test that resolution multipliers are ordered correctly."""
    from app.gaming_profiles import RESOLUTION_MULTIPLIERS

    # 1080p should have highest multipliers
    # 4K should have lowest multipliers
    for setting in ["low", "medium", "high", "ultra"]:
        mult_1080p = RESOLUTION_MULTIPLIERS["1080p"][setting]
        mult_4k = RESOLUTION_MULTIPLIERS["4K"][setting]
        assert mult_1080p > mult_4k, f"1080p should have higher multiplier than 4K for {setting}"


def test_fps_scaling_factors():
    """Test that FPS scaling factors are reasonable."""
    from app.gaming_profiles import FPS_SCALING_FACTORS

    # E-sport should have highest scaling (lightest games)
    # AAA GPU should have lowest scaling (heaviest games)
    assert FPS_SCALING_FACTORS["esport"] > FPS_SCALING_FACTORS["aaa_gpu"]
    assert FPS_SCALING_FACTORS["simulation"] > FPS_SCALING_FACTORS["aaa_gpu"]

