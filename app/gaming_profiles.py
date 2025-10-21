"""Gaming profiles and categories configuration."""

from typing import Dict, List, Optional


# Game categories with CPU/GPU importance weights
GAME_CATEGORIES = {
    "esport": {
        "name": "esport",
        "display_name": "E-sport / CPU-heavy",
        "weight": 0.25,
        "cpu_importance": 0.80,
        "gpu_importance": 0.20,
        "single_thread_critical": True,
        "examples": ["Valorant", "CS2", "League of Legends", "Fortnite"],
        "description": "Competitive games requiring high CPU single-thread performance",
    },
    "aaa_gpu": {
        "name": "aaa_gpu",
        "display_name": "AAA GPU-heavy",
        "weight": 0.35,
        "cpu_importance": 0.25,
        "gpu_importance": 0.75,
        "vram_critical": True,
        "ray_tracing": True,
        "examples": ["Cyberpunk 2077", "Hogwarts Legacy", "Starfield", "Alan Wake 2"],
        "description": "Modern AAA games with heavy GPU requirements and ray tracing",
    },
    "balanced": {
        "name": "balanced",
        "display_name": "Balanced CPU+GPU",
        "weight": 0.25,
        "cpu_importance": 0.50,
        "gpu_importance": 0.50,
        "synergy_critical": True,
        "examples": ["GTA V", "Red Dead Redemption 2", "AC Mirage", "Horizon Forbidden West"],
        "description": "Games requiring balanced CPU and GPU performance",
    },
    "simulation": {
        "name": "simulation",
        "display_name": "CPU-intensive simulation",
        "weight": 0.15,
        "cpu_importance": 0.90,
        "gpu_importance": 0.10,
        "multi_thread_critical": True,
        "examples": ["Cities Skylines II", "Microsoft Flight Simulator", "Total War"],
        "description": "Simulation games with heavy CPU load and physics",
    },
}


# Minimum requirements per category (normalized scores)
CATEGORY_MINIMUM_REQUIREMENTS = {
    "esport": {
        "min_cpu_score": 15,
        "min_gpu_score": 10,
        "min_cpu_single_thread": 2000,
        "min_gpu_memory": 4,  # GB VRAM
    },
    "aaa_gpu": {
        "min_cpu_score": 30,
        "min_gpu_score": 40,
        "min_cpu_cores": 6,
        "min_gpu_memory": 8,
    },
    "balanced": {
        "min_cpu_score": 20,
        "min_gpu_score": 35,
        "min_gpu_memory": 3,
    },
    "simulation": {
        "min_cpu_score": 40,
        "min_gpu_score": 15,  # Even 10% weight requires minimum
        "min_cpu_cores": 8,
        "min_cpu_threads": 12,
    },
}


# Maximum tier difference allowed per category
MAX_TIER_DIFFERENCE = {
    "esport": 1,  # CPU ultra + GPU high = OK
    "aaa_gpu": 1,  # GPU ultra + CPU high = OK
    "balanced": 1,  # Both similar (max 1 tier diff)
    "simulation": 2,  # CPU ultra + GPU mid = OK
}


# Maximum normalized score difference per category
MAX_SCORE_DIFFERENCE = {
    "esport": 50,  # CPU can be 50pts better than GPU
    "aaa_gpu": 50,  # GPU can be 50pts better than CPU
    "balanced": 30,  # Max 30pts difference
    "simulation": 60,  # CPU can be 60pts better
}


# Tier values for comparison
TIER_VALUES = {"low": 1, "mid": 2, "high": 3, "ultra": 4}


# Resolution performance multipliers
RESOLUTION_MULTIPLIERS = {
    "1080p": {"low": 1.2, "medium": 1.0, "high": 0.85, "ultra": 0.70},
    "1440p": {"low": 0.78, "medium": 0.65, "high": 0.55, "ultra": 0.45},
    "4K": {"low": 0.42, "medium": 0.35, "high": 0.28, "ultra": 0.25},
}


# FPS scaling factors per category
FPS_SCALING_FACTORS = {
    "esport": 3.5,  # Light games
    "aaa_gpu": 1.2,  # Heavy AAA
    "balanced": 2.0,  # Medium
    "simulation": 2.5,  # CPU-bound
}


def get_category(category_name: str) -> Optional[Dict]:
    """Get game category configuration by name."""
    return GAME_CATEGORIES.get(category_name)


def get_all_categories() -> Dict[str, Dict]:
    """Get all game categories."""
    return GAME_CATEGORIES


def get_category_examples(category_name: str) -> List[str]:
    """Get example games for a category."""
    category = GAME_CATEGORIES.get(category_name)
    return category["examples"] if category else []


def estimate_fps(
    component_score: int, resolution: str, settings: str, category_name: str
) -> int:
    """
    Estimate FPS based on component score, resolution, and settings.

    Args:
        component_score: PassMark score (normalized 0-100)
        resolution: "1080p", "1440p", or "4K"
        settings: "low", "medium", "high", or "ultra"
        category_name: Game category name

    Returns:
        Estimated FPS
    """
    if component_score <= 0:
        return 0

    # Get scaling factor for category
    base_scaling = FPS_SCALING_FACTORS.get(category_name, 2.0)

    # Get resolution multiplier
    res_mult = RESOLUTION_MULTIPLIERS.get(resolution, {}).get(settings, 1.0)

    # Calculate FPS - use normalized score (0-100)
    # Formula: normalized_score * category_scaling * resolution_mult
    fps = component_score * base_scaling * res_mult

    return max(1, round(fps))


def get_performance_tier_for_resolution(normalized_score: int, resolution: str) -> str:
    """
    Get performance tier description for a given resolution.

    Args:
        normalized_score: Normalized score (0-100)
        resolution: "1080p", "1440p", or "4K"

    Returns:
        Performance tier description
    """
    if resolution == "1080p":
        if normalized_score >= 80:
            return "ultra (144+ FPS)"
        elif normalized_score >= 60:
            return "high (100+ FPS)"
        elif normalized_score >= 40:
            return "medium (60+ FPS)"
        else:
            return "low (30-60 FPS)"

    elif resolution == "1440p":
        if normalized_score >= 85:
            return "ultra (100+ FPS)"
        elif normalized_score >= 70:
            return "high (80+ FPS)"
        elif normalized_score >= 50:
            return "medium (60+ FPS)"
        else:
            return "low (30-60 FPS)"

    elif resolution == "4K":
        if normalized_score >= 92:
            return "ultra (60+ FPS)"
        elif normalized_score >= 80:
            return "high (50+ FPS)"
        elif normalized_score >= 60:
            return "medium (40+ FPS)"
        else:
            return "low (30+ FPS)"

    return "unknown"


def get_bottleneck_threshold(category_name: str) -> Dict[str, float]:
    """
    Get bottleneck detection thresholds for a category.

    Returns dict with 'cpu_bound' and 'gpu_bound' ratio thresholds.
    """
    category = GAME_CATEGORIES.get(category_name)
    if not category:
        return {"cpu_bound": 1.3, "gpu_bound": 0.7}

    cpu_importance = category["cpu_importance"]

    if cpu_importance > 0.6:  # CPU-heavy
        return {"cpu_bound": 1.2, "gpu_bound": 0.5}
    elif cpu_importance < 0.4:  # GPU-heavy
        return {"cpu_bound": 1.8, "gpu_bound": 0.8}
    else:  # Balanced
        return {"cpu_bound": 1.3, "gpu_bound": 0.7}
