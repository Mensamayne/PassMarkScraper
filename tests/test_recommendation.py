"""Tests for recommendation engine."""

import pytest
from app.recommendation import (
    calculate_balance_score,
    detect_bottleneck,
    check_minimum_requirements,
    check_tier_compatibility,
    check_score_balance,
    analyze_pairing,
    get_overall_verdict,
)


def test_check_minimum_requirements():
    """Test minimum requirements checking."""
    cpu = {
        "normalized_score": 50,
        "cores": 8,
        "threads": 16,
        "single_thread_rating": 3000,
    }
    gpu = {"normalized_score": 50, "memory_size": 8}

    # Test esport category
    passed, issues = check_minimum_requirements(cpu, gpu, "esport")
    assert passed is True
    assert len(issues) == 0

    # Test with CPU below minimum
    weak_cpu = {"normalized_score": 20, "cores": 4}
    passed, issues = check_minimum_requirements(weak_cpu, gpu, "aaa_gpu")
    assert passed is False
    assert len(issues) > 0


def test_check_tier_compatibility():
    """Test tier compatibility checking."""
    cpu_ultra = {"tier": "ultra"}
    gpu_high = {"tier": "high"}
    gpu_low = {"tier": "low"}

    # Compatible - 1 tier diff
    compatible, issue, rec = check_tier_compatibility(cpu_ultra, gpu_high, "esport")
    assert compatible is True

    # Incompatible - 3 tier diff
    compatible, issue, rec = check_tier_compatibility(cpu_ultra, gpu_low, "esport")
    assert compatible is False
    assert issue is not None


def test_check_score_balance():
    """Test score balance checking."""
    cpu_high = {"normalized_score": 80}
    gpu_mid = {"normalized_score": 50}

    # Test balanced category (max 30 diff) - exactly at limit is OK
    balanced, weak, score = check_score_balance(cpu_high, gpu_mid, "balanced")
    assert balanced is True  # 30 diff is exactly at limit

    # Test with bigger difference
    gpu_low = {"normalized_score": 40}
    balanced, weak, score = check_score_balance(cpu_high, gpu_low, "balanced")
    assert balanced is False  # 40 diff exceeds limit of 30

    # Test simulation (max 60 diff)
    balanced, weak, score = check_score_balance(cpu_high, gpu_mid, "simulation")
    assert balanced is True  # 30 diff is OK for simulation


def test_calculate_balance_score():
    """Test balance score calculation."""
    # Good pairing
    cpu = {"normalized_score": 75, "tier": "high", "cores": 8, "threads": 16}
    gpu = {"normalized_score": 70, "tier": "high", "memory_size": 12}

    score = calculate_balance_score(cpu, gpu, "balanced")
    assert isinstance(score, int)
    assert 0 <= score <= 100
    assert score > 70  # Should be good score

    # Bad pairing - huge difference
    weak_gpu = {"normalized_score": 10, "tier": "low", "memory_size": 2}
    score = calculate_balance_score(cpu, weak_gpu, "aaa_gpu")
    assert score < 40  # Should be poor score


def test_detect_bottleneck():
    """Test bottleneck detection."""
    # Balanced setup
    cpu = {"normalized_score": 70}
    gpu = {"normalized_score": 70}

    bottleneck = detect_bottleneck(cpu, gpu, "balanced")
    assert bottleneck is None  # No bottleneck

    # GPU MUCH stronger (extreme case)
    cpu_weak = {"normalized_score": 30}
    strong_gpu = {"normalized_score": 95}
    bottleneck = detect_bottleneck(cpu_weak, strong_gpu, "aaa_gpu")
    assert bottleneck in ["cpu_bottleneck", "slight_cpu"]

    # CPU much stronger
    strong_cpu = {"normalized_score": 95}
    weak_gpu = {"normalized_score": 20}
    bottleneck = detect_bottleneck(strong_cpu, weak_gpu, "esport")
    # E-sport is CPU-heavy so GPU bottleneck might not be severe
    assert bottleneck in [None, "gpu_bottleneck", "slight_gpu"]


def test_analyze_pairing():
    """Test complete pairing analysis."""
    cpu = {
        "name": "Test CPU",
        "normalized_score": 75,
        "tier": "high",
        "cores": 8,
        "threads": 16,
        "single_thread_rating": 3500,
    }
    gpu = {
        "name": "Test GPU",
        "normalized_score": 70,
        "tier": "high",
        "memory_size": 12,
    }

    analysis = analyze_pairing(cpu, gpu)

    # Check structure
    assert "by_category" in analysis
    assert "balance_scores" in analysis
    assert "overall_balance_score" in analysis
    assert "overall_verdict" in analysis

    # Check all categories analyzed
    assert "esport" in analysis["by_category"]
    assert "aaa_gpu" in analysis["by_category"]
    assert "balanced" in analysis["by_category"]
    assert "simulation" in analysis["by_category"]

    # Check category analysis structure
    cat_analysis = analysis["by_category"]["balanced"]
    assert "balance_score" in cat_analysis
    assert "bottleneck" in cat_analysis
    assert "cpu_utilization" in cat_analysis
    assert "gpu_utilization" in cat_analysis
    assert "performance" in cat_analysis


def test_get_overall_verdict():
    """Test overall verdict calculation."""
    # Excellent scores
    scores = {"esport": 95, "aaa_gpu": 90, "balanced": 92, "simulation": 88}
    verdict = get_overall_verdict(scores)
    assert verdict == "excellent"

    # Poor scores
    scores = {"esport": 30, "aaa_gpu": 25, "balanced": 35, "simulation": 20}
    verdict = get_overall_verdict(scores)
    assert verdict == "poor"

    # Mixed scores
    scores = {"esport": 70, "aaa_gpu": 65, "balanced": 75, "simulation": 60}
    verdict = get_overall_verdict(scores)
    assert verdict in ["good", "fair"]


def test_extreme_mismatch():
    """Test detection of extreme component mismatches."""
    # Threadripper + GTX 1030 scenario
    threadripper = {
        "name": "Threadripper 5995WX",
        "normalized_score": 100,
        "tier": "ultra",
        "cores": 64,
        "threads": 128,
        "single_thread_rating": 3800,
    }
    gtx1030 = {
        "name": "GTX 1030",
        "normalized_score": 8,
        "tier": "low",
        "memory_size": 2,
    }

    analysis = analyze_pairing(threadripper, gtx1030)

    # Should have very poor scores
    assert analysis["overall_balance_score"] < 30
    assert analysis["overall_verdict"] == "poor"

    # Should detect GPU bottleneck
    assert analysis["overall_bottleneck"] == "gpu"


def test_i3_with_rtx4090():
    """Test i3 + RTX 4090 extreme mismatch."""
    i3 = {
        "name": "i3-12100F",
        "normalized_score": 25,
        "tier": "low",
        "cores": 4,
        "threads": 8,
        "single_thread_rating": 3200,
    }
    rtx4090 = {
        "name": "RTX 4090",
        "normalized_score": 100,
        "tier": "ultra",
        "memory_size": 24,
    }

    analysis = analyze_pairing(i3, rtx4090)

    # Should have poor scores
    assert analysis["overall_balance_score"] < 40
    assert analysis["overall_verdict"] in ["poor", "fair"]

    # Should detect CPU bottleneck
    assert analysis["overall_bottleneck"] == "cpu"

    # AAA GPU category should show CPU issues
    aaa_analysis = analysis["by_category"]["aaa_gpu"]
    assert aaa_analysis["balance_score"] < 50
    assert "cpu" in str(aaa_analysis.get("bottleneck", "")).lower() or not aaa_analysis[
        "meets_minimum"
    ]


def test_balanced_mid_tier_pairing():
    """Test balanced mid-tier pairing."""
    ryzen5 = {
        "name": "Ryzen 5 7600",
        "normalized_score": 45,
        "tier": "mid",
        "cores": 6,
        "threads": 12,
        "single_thread_rating": 4000,
    }
    rtx4060 = {
        "name": "RTX 4060",
        "normalized_score": 40,
        "tier": "mid",
        "memory_size": 8,
    }

    analysis = analyze_pairing(ryzen5, rtx4060)

    # Should have decent scores (mid-tier = fair to good)
    assert analysis["overall_balance_score"] >= 50
    assert analysis["overall_verdict"] in ["fair", "good", "very_good", "excellent"]

    # Should have no major bottleneck
    assert analysis["overall_bottleneck"] is None

    # E-sport should be reasonable (mid-tier components)
    esport_analysis = analysis["by_category"]["esport"]
    assert esport_analysis["balance_score"] > 40

