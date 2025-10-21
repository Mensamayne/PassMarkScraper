"""Component pairing recommendation and bottleneck analysis."""

import logging
from typing import Dict, List, Optional, Tuple
from app.gaming_profiles import (
    GAME_CATEGORIES,
    CATEGORY_MINIMUM_REQUIREMENTS,
    MAX_TIER_DIFFERENCE,
    MAX_SCORE_DIFFERENCE,
    TIER_VALUES,
    get_bottleneck_threshold,
    estimate_fps,
    get_performance_tier_for_resolution,
)
from app.config_loader import config
from app.filters import is_desktop_component

# Setup logging
logger = logging.getLogger(__name__)

# Get config values with defaults
_config = config.get_config()
_rec_config = _config.get("recommendation", {})
MIN_MATCH_SCORE = _rec_config.get("min_match_score", 40)
BOTTLENECK_THRESHOLD = _rec_config.get("bottleneck_threshold", 40)
MAX_RECOMMENDATIONS = _rec_config.get("max_recommendations", 5)


def get_tier_name(tier_value: int) -> str:
    """Convert tier value to tier name."""
    for name, value in TIER_VALUES.items():
        if value == tier_value:
            return name
    return "unknown"


def check_minimum_requirements(
    cpu: Dict, gpu: Dict, category_name: str
) -> Tuple[bool, List[str]]:
    """
    Check if components meet minimum requirements for category.

    Args:
        cpu: CPU data dict
        gpu: GPU data dict
        category_name: Game category name

    Returns:
        Tuple of (passed, list of issues)
    """
    issues = []
    min_reqs = CATEGORY_MINIMUM_REQUIREMENTS.get(category_name, {})

    # Check CPU requirements
    if "min_cpu_score" in min_reqs:
        cpu_score = cpu.get("normalized_score", 0)
        if cpu_score < min_reqs["min_cpu_score"]:
            issues.append(
                f"CPU score ({cpu_score}) below minimum ({min_reqs['min_cpu_score']}) for {category_name}"
            )

    if "min_cpu_cores" in min_reqs:
        cpu_cores = cpu.get("cores", 0)
        if cpu_cores and cpu_cores < min_reqs["min_cpu_cores"]:
            issues.append(
                f"CPU has only {cpu_cores} cores, {category_name} needs {min_reqs['min_cpu_cores']}+"
            )

    if "min_cpu_threads" in min_reqs:
        cpu_threads = cpu.get("threads", 0)
        if cpu_threads and cpu_threads < min_reqs["min_cpu_threads"]:
            issues.append(
                f"CPU has only {cpu_threads} threads, {category_name} needs {min_reqs['min_cpu_threads']}+"
            )

    if "min_cpu_single_thread" in min_reqs:
        cpu_st = cpu.get("single_thread_rating", 0)
        if cpu_st and cpu_st < min_reqs["min_cpu_single_thread"]:
            issues.append(
                f"CPU single-thread ({cpu_st}) below minimum ({min_reqs['min_cpu_single_thread']})"
            )

    # Check GPU requirements
    if "min_gpu_score" in min_reqs:
        gpu_score = gpu.get("normalized_score", 0)
        if gpu_score < min_reqs["min_gpu_score"]:
            issues.append(
                f"GPU score ({gpu_score}) below minimum ({min_reqs['min_gpu_score']}) for {category_name}"
            )

    if "min_gpu_memory" in min_reqs:
        gpu_mem = gpu.get("memory_size", 0)
        if gpu_mem and gpu_mem < min_reqs["min_gpu_memory"]:
            issues.append(
                f"GPU has only {gpu_mem}GB VRAM, {category_name} needs {min_reqs['min_gpu_memory']}GB+"
            )

    return len(issues) == 0, issues


def check_tier_compatibility(
    cpu: Dict, gpu: Dict, category_name: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if tier difference is acceptable.

    Args:
        cpu: CPU data dict
        gpu: GPU data dict
        category_name: Game category name

    Returns:
        Tuple of (compatible, issue, recommendation)
    """
    cpu_tier = TIER_VALUES.get(cpu.get("tier", "low"), 1)
    gpu_tier = TIER_VALUES.get(gpu.get("tier", "low"), 1)

    max_diff = MAX_TIER_DIFFERENCE.get(category_name, 1)
    tier_diff = abs(cpu_tier - gpu_tier)

    if tier_diff <= max_diff:
        return True, None, None

    # Find which component is weaker
    if cpu_tier < gpu_tier:
        target_tier = gpu_tier - max_diff
        target_name = get_tier_name(target_tier)
        return (
            False,
            "cpu_too_weak",
            f"Upgrade CPU to at least '{target_name}' tier (currently '{cpu.get('tier')}')",
        )
    else:
        target_tier = cpu_tier - max_diff
        target_name = get_tier_name(target_tier)
        return (
            False,
            "gpu_too_weak",
            f"Upgrade GPU to at least '{target_name}' tier (currently '{gpu.get('tier')}')",
        )


def check_score_balance(
    cpu: Dict, gpu: Dict, category_name: str
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Check if score difference is acceptable using passmark scores.
    
    Uses actual PassMark scores instead of normalized (0-100) to properly differentiate
    between high-end components that would all have normalized_score=100.

    Args:
        cpu: CPU data dict
        gpu: GPU data dict
        category_name: Game category name

    Returns:
        Tuple of (balanced, weak_component, recommended_min_passmark_score)
    """
    cpu_score = cpu.get("passmark_score", 0)
    gpu_score = gpu.get("passmark_score", 0)
    
    if cpu_score == 0 or gpu_score == 0:
        return True, None, None

    # Get category to determine expected ratio
    category = GAME_CATEGORIES.get(category_name, {})
    cpu_importance = category.get("cpu_importance", 0.5)
    gpu_importance = category.get("gpu_importance", 0.5)
    
    # Calculate ratio (accounts for different scales: CPU ~70k max, GPU ~42k max)
    # For balanced categories, expect ~1.5-1.8 ratio (CPU typically higher)
    # Adjust expected ratio based on category importance
    if cpu_importance > gpu_importance:
        # CPU-heavy games: CPU can be much stronger
        expected_ratio = 2.2  # CPU can be 2.2x GPU score
        tolerance = 0.8
    elif gpu_importance > cpu_importance:
        # GPU-heavy games: GPU should be closer to CPU
        expected_ratio = 1.4  # CPU ~1.4x GPU score
        tolerance = 0.4
    else:
        # Balanced: moderate ratio
        expected_ratio = 1.7  # CPU ~1.7x GPU score
        tolerance = 0.5
    
    actual_ratio = cpu_score / gpu_score if gpu_score > 0 else 999
    
    # Check if ratio is within tolerance
    if abs(actual_ratio - expected_ratio) <= tolerance:
        return True, None, None
    
    # Determine weak component
    if actual_ratio < (expected_ratio - tolerance):
        # CPU too weak relative to GPU
        needed_score = round(gpu_score * (expected_ratio - tolerance))
        return False, "cpu", needed_score
    else:
        # GPU too weak relative to CPU
        needed_score = round(cpu_score / (expected_ratio + tolerance))
        return False, "gpu", needed_score


def calculate_balance_score(cpu: Dict, gpu: Dict, category_name: str) -> int:
    """
    Calculate balance score for CPU+GPU pairing in given category.
    Uses passmark_score for better differentiation between high-end components.

    Returns score 0-100 (100 = perfect balance).
    """
    # 1. Check minimum requirements
    meets_min, _ = check_minimum_requirements(cpu, gpu, category_name)
    if not meets_min:
        return 0

    # 2. Check tier compatibility
    tier_ok, _, _ = check_tier_compatibility(cpu, gpu, category_name)
    if not tier_ok:
        cpu_tier = TIER_VALUES.get(cpu.get("tier", "low"), 1)
        gpu_tier = TIER_VALUES.get(gpu.get("tier", "low"), 1)
        tier_diff = abs(cpu_tier - gpu_tier)
        return max(0, 30 - (tier_diff * 10))

    # 3. Check score balance using passmark scores
    score_ok, _, _ = check_score_balance(cpu, gpu, category_name)
    
    cpu_passmark = cpu.get("passmark_score", 0)
    gpu_passmark = gpu.get("passmark_score", 0)
    
    if cpu_passmark == 0 or gpu_passmark == 0:
        return 50  # Unknown, give medium score
    
    # Get category weights
    category = GAME_CATEGORIES.get(category_name, {})
    cpu_importance = category.get("cpu_importance", 0.5)
    gpu_importance = category.get("gpu_importance", 0.5)
    
    # Calculate ratio and compare to expected ratio
    actual_ratio = cpu_passmark / gpu_passmark
    
    # Expected ratio based on category (CPU ~70k max, GPU ~42k max = ~1.7 for balanced)
    if cpu_importance > gpu_importance:
        expected_ratio = 2.2  # CPU-heavy
        tolerance = 0.8
    elif gpu_importance > cpu_importance:
        expected_ratio = 1.4  # GPU-heavy
        tolerance = 0.4
    else:
        expected_ratio = 1.7  # Balanced
        tolerance = 0.5
    
    # Calculate how close to ideal ratio (0 = perfect)
    ratio_deviation = abs(actual_ratio - expected_ratio)
    
    # Convert deviation to score (0 deviation = 100, max tolerance = 80, beyond = lower)
    if ratio_deviation <= tolerance:
        # Within tolerance: 80-100 score
        ratio_score = 100 - (ratio_deviation / tolerance) * 20
    else:
        # Beyond tolerance: 0-80 score
        extra_deviation = ratio_deviation - tolerance
        ratio_score = max(0, 80 - (extra_deviation * 30))
    
    # Normalize component scores to 0-100 scale for weighting
    # Use rough maximums: CPU ~70k, GPU ~42k
    cpu_normalized = min(100, (cpu_passmark / 70000) * 100)
    gpu_normalized = min(100, (gpu_passmark / 42000) * 100)
    
    # Calculate absolute performance score (how powerful the setup is)
    performance_score = (cpu_normalized * cpu_importance + gpu_normalized * gpu_importance)
    
    # Final balance score: 60% ratio balance + 40% absolute performance
    balance_score = round(ratio_score * 0.6 + performance_score * 0.4)
    
    return min(100, max(0, balance_score))


def detect_bottleneck(cpu: Dict, gpu: Dict, category_name: str) -> Optional[str]:
    """
    Detect bottleneck type for given pairing and category.
    Uses passmark_score for accurate bottleneck detection.

    Returns:
        "cpu_bottleneck", "gpu_bottleneck", "slight_cpu", "slight_gpu", or None
    """
    cpu_score = cpu.get("passmark_score", 0)
    gpu_score = gpu.get("passmark_score", 0)

    if cpu_score == 0 or gpu_score == 0:
        return None

    # Calculate ratio (CPU/GPU) - typically ~1.4-2.2 for balanced systems
    ratio = cpu_score / gpu_score
    
    # Get category importance
    category = GAME_CATEGORIES.get(category_name, {})
    cpu_importance = category.get("cpu_importance", 0.5)
    gpu_importance = category.get("gpu_importance", 0.5)
    
    # Determine expected ratio and thresholds based on category
    if cpu_importance > gpu_importance:
        # CPU-heavy: expect higher ratio, CPU should be stronger
        ideal_ratio = 2.2
        cpu_bottleneck_threshold = 1.2  # Below 1.2 = CPU too weak
        gpu_bottleneck_threshold = 3.2  # Above 3.2 = GPU too weak
    elif gpu_importance > cpu_importance:
        # GPU-heavy: expect lower ratio, GPU should be stronger
        ideal_ratio = 1.4
        cpu_bottleneck_threshold = 0.9  # Below 0.9 = CPU too weak
        gpu_bottleneck_threshold = 2.0  # Above 2.0 = GPU too weak
    else:
        # Balanced: moderate ratio
        ideal_ratio = 1.7
        cpu_bottleneck_threshold = 1.0  # Below 1.0 = CPU too weak
        gpu_bottleneck_threshold = 2.5  # Above 2.5 = GPU too weak

    # Detect bottleneck
    if ratio < cpu_bottleneck_threshold:
        # CPU much weaker than GPU for this category
        if ratio < cpu_bottleneck_threshold * 0.7:
            return "cpu_bottleneck"
        else:
            return "slight_cpu"
    
    elif ratio > gpu_bottleneck_threshold:
        # GPU much weaker than CPU for this category
        if ratio > gpu_bottleneck_threshold * 1.3:
            return "gpu_bottleneck"
        else:
            return "slight_gpu"

    return None


def calculate_utilization(cpu: Dict, gpu: Dict, category_name: str) -> Dict[str, int]:
    """
    Estimate CPU and GPU utilization percentage.
    Uses passmark_score for accurate utilization estimates.

    Returns:
        Dict with "cpu" and "gpu" utilization estimates (0-100)
    """
    category = GAME_CATEGORIES.get(category_name, {})
    cpu_importance = category.get("cpu_importance", 0.5)
    gpu_importance = category.get("gpu_importance", 0.5)

    cpu_score = cpu.get("passmark_score", 0)
    gpu_score = gpu.get("passmark_score", 0)
    
    if cpu_score == 0 or gpu_score == 0:
        return {"cpu": 50, "gpu": 50}

    # Calculate ratio
    ratio = cpu_score / gpu_score
    
    # Determine expected ratio for this category
    if cpu_importance > gpu_importance:
        expected_ratio = 2.2
    elif gpu_importance > cpu_importance:
        expected_ratio = 1.4
    else:
        expected_ratio = 1.7

    # Base utilization from importance weights
    base_cpu_util = cpu_importance * 100
    base_gpu_util = gpu_importance * 100

    # Adjust based on relative power and expected ratio
    if ratio > expected_ratio * 1.2:
        # CPU much stronger - GPU will be maxed out, CPU underutilized
        gpu_util = min(100, round(base_gpu_util * 1.2))
        cpu_util = min(100, round(base_cpu_util * 0.8))
    elif ratio < expected_ratio * 0.8:
        # GPU stronger (relatively) - CPU will be maxed out, GPU underutilized
        cpu_util = min(100, round(base_cpu_util * 1.2))
        gpu_util = min(100, round(base_gpu_util * 0.8))
    else:
        # Well balanced - both utilized according to importance
        cpu_util = min(100, round(base_cpu_util))
        gpu_util = min(100, round(base_gpu_util))

    return {"cpu": cpu_util, "gpu": gpu_util}


def get_overall_verdict(balance_scores: Dict[str, int]) -> str:
    """
    Get overall verdict based on balance scores across all categories.

    Args:
        balance_scores: Dict of category_name -> balance_score

    Returns:
        Overall verdict string
    """
    if not balance_scores:
        return "unknown"

    avg_score = sum(balance_scores.values()) / len(balance_scores)

    if avg_score >= 90:
        return "excellent"
    elif avg_score >= 75:
        return "very_good"
    elif avg_score >= 60:
        return "good"
    elif avg_score >= 40:
        return "fair"
    else:
        return "poor"


def analyze_pairing(cpu: Dict, gpu: Dict) -> Dict:
    """
    Perform complete pairing analysis across all game categories.

    Args:
        cpu: CPU data dict (must include normalized_score, tier)
        gpu: GPU data dict (must include normalized_score, tier)

    Returns:
        Complete analysis dict
    """
    analysis = {"by_category": {}, "balance_scores": {}}

    # Analyze each category
    for cat_name, category in GAME_CATEGORIES.items():
        balance_score = calculate_balance_score(cpu, gpu, cat_name)
        bottleneck = detect_bottleneck(cpu, gpu, cat_name)
        utilization = calculate_utilization(cpu, gpu, cat_name)
        meets_min, issues = check_minimum_requirements(cpu, gpu, cat_name)

        category_analysis = {
            "balance_score": balance_score,
            "bottleneck": bottleneck,
            "cpu_utilization": utilization["cpu"],
            "gpu_utilization": utilization["gpu"],
            "meets_minimum": meets_min,
            "issues": issues,
        }

        # Add performance rating
        if balance_score >= 90:
            category_analysis["performance"] = "excellent"
        elif balance_score >= 75:
            category_analysis["performance"] = "very_good"
        elif balance_score >= 60:
            category_analysis["performance"] = "good"
        elif balance_score >= 40:
            category_analysis["performance"] = "fair"
        else:
            category_analysis["performance"] = "poor"

        analysis["by_category"][cat_name] = category_analysis
        analysis["balance_scores"][cat_name] = balance_score

    # Calculate weighted overall score
    weighted_sum = 0
    weight_total = 0
    for cat_name, score in analysis["balance_scores"].items():
        weight = GAME_CATEGORIES[cat_name]["weight"]
        weighted_sum += score * weight
        weight_total += weight

    analysis["overall_balance_score"] = round(weighted_sum / weight_total) if weight_total > 0 else 0
    analysis["overall_verdict"] = get_overall_verdict(analysis["balance_scores"])

    # Detect overall bottleneck using passmark scores
    cpu_score = cpu.get("passmark_score", 0)
    gpu_score = gpu.get("passmark_score", 0)
    
    if cpu_score > 0 and gpu_score > 0:
        ratio = cpu_score / gpu_score
        # General threshold: expect ratio ~1.4-2.2, outside means imbalance
        if ratio < 1.0:
            analysis["overall_bottleneck"] = "cpu"
        elif ratio > 2.8:
            analysis["overall_bottleneck"] = "gpu"
        else:
            analysis["overall_bottleneck"] = None
    else:
        analysis["overall_bottleneck"] = None

    return analysis


def recommend_components(
    base_component: Dict,
    component_type: str,
    all_components: List[Dict],
    game_focus: Optional[str] = None,
    limit: int = 5,
) -> List[Dict]:
    """
    Recommend compatible components based on a base component.

    Args:
        base_component: The component you already have (CPU or GPU)
        component_type: Type of base component ("CPU" or "GPU")
        all_components: List of available components to recommend
        game_focus: Optional game category to focus on
        limit: Max number of recommendations

    Returns:
        List of recommended components with match scores
    """
    recommendations = []

    # Determine which component type we're recommending
    recommend_type = "GPU" if component_type == "CPU" else "CPU"

    # Filter to correct type and only desktop consumer components
    # Double-check: even if DB has category='consumer', verify it's truly desktop
    candidates = []
    for c in all_components:
        if c.get("component_type") != recommend_type:
            continue
        
        # Check category from database
        db_category = c.get("category", "consumer")
        if db_category in ["server", "workstation"]:
            continue
            
        # Double-check name for mobile/laptop indicators
        if not is_desktop_component(c.get("name", ""), recommend_type):
            print(f"DEBUG: Filtered out {c.get('name', 'Unknown')} - not desktop component")
            continue
            
        candidates.append(c)

    # Calculate match scores
    for candidate in candidates:
        if component_type == "CPU":
            cpu = base_component
            gpu = candidate
        else:
            cpu = candidate
            gpu = base_component

        # Calculate scores for all categories or focused category
        if game_focus:
            categories = [game_focus]
        else:
            categories = list(GAME_CATEGORIES.keys())

        balance_scores = {}
        for cat_name in categories:
            score = calculate_balance_score(cpu, gpu, cat_name)
            weight = GAME_CATEGORIES[cat_name]["weight"]
            balance_scores[cat_name] = {"score": score, "weight": weight}

        # Calculate weighted match score
        weighted_sum = 0
        weight_total = 0
        for cat_data in balance_scores.values():
            weighted_sum += cat_data["score"] * cat_data["weight"]
            weight_total += cat_data["weight"]

        match_score = round(weighted_sum / weight_total) if weight_total > 0 else 0
        
        # Add bonus for good passmark ratio match
        cpu_passmark = cpu.get("passmark_score", 0)
        gpu_passmark = gpu.get("passmark_score", 0)
        
        if cpu_passmark > 0 and gpu_passmark > 0:
            ratio = cpu_passmark / gpu_passmark
            # Bonus for ratio close to ideal (1.4-2.2 range)
            if 1.3 <= ratio <= 2.3:
                match_score += 15
            elif 1.0 <= ratio <= 2.8:
                match_score += 5

        # Only include decent matches (configurable threshold)
        if match_score >= MIN_MATCH_SCORE:
            recommendations.append(
                {
                    "component": candidate,
                    "match_score": match_score,
                    "balance_scores": balance_scores,
                }
            )
        else:
            # Debug: log rejected candidates
            print(f"DEBUG: Rejected {candidate.get('name', 'Unknown')} - match_score: {match_score}, min_required: {MIN_MATCH_SCORE}")

    # Sort by match score (profile fit), then by passmark ratio compatibility
    # If game_focus is specified, prioritize match_score; otherwise prioritize good ratio
    base_passmark = base_component.get("passmark_score", 0)
    
    if game_focus:
        # Profile-focused: match_score is primary, passmark ratio is secondary
        def sort_key_focused(x):
            comp_passmark = x["component"].get("passmark_score", 0)
            if base_passmark > 0 and comp_passmark > 0:
                if component_type == "CPU":
                    ratio = base_passmark / comp_passmark  # CPU / GPU
                else:
                    ratio = comp_passmark / base_passmark  # CPU / GPU
                ratio_deviation = abs(ratio - 1.7)  # Ideal balanced ratio
            else:
                ratio_deviation = 999
            return (-x["match_score"], ratio_deviation)
        recommendations.sort(key=sort_key_focused)
    else:
        # General recommendation: good ratio is primary, match_score is secondary
        def sort_key_general(x):
            comp_passmark = x["component"].get("passmark_score", 0)
            if base_passmark > 0 and comp_passmark > 0:
                if component_type == "CPU":
                    ratio = base_passmark / comp_passmark  # CPU / GPU
                else:
                    ratio = comp_passmark / base_passmark  # CPU / GPU
                ratio_deviation = abs(ratio - 1.7)  # Ideal balanced ratio
            else:
                ratio_deviation = 999
            return (ratio_deviation, -x["match_score"])
        recommendations.sort(key=sort_key_general)

    # Apply limit (use config default if limit exceeds it)
    effective_limit = min(limit, MAX_RECOMMENDATIONS * 2)  # Allow 2x for flexibility
    return recommendations[:effective_limit]

