"""Power consumption and thermal analysis."""

import logging
from typing import Dict, Optional
from app.config_loader import config

logger = logging.getLogger(__name__)

# Get PSU overhead from config
_config = config.get_config()
_rec_config = _config.get("recommendation", {})
PSU_OVERHEAD_PERCENT = _rec_config.get("psu_overhead_percent", 30)


def estimate_system_power(cpu: Dict, gpu: Dict) -> Dict:
    """
    Estimate system power consumption and cooling requirements.
    
    Args:
        cpu: CPU data dict (should include tdp)
        gpu: GPU data dict (should include tdp)
        
    Returns:
        Dict with power estimates and recommendations
    """
    # Get TDP values (handle None from database)
    cpu_tdp = cpu.get("tdp") or 0
    gpu_tdp = gpu.get("tdp") or 0
    
    # Estimate based on tier if TDP not available
    if cpu_tdp == 0 or cpu_tdp is None:
        cpu_tdp = estimate_tdp_from_tier(cpu, "CPU")
    if gpu_tdp == 0 or gpu_tdp is None:
        gpu_tdp = estimate_tdp_from_tier(gpu, "GPU")
    
    # System overhead (motherboard, RAM, storage, fans)
    system_overhead = 100
    
    # Total system power
    total_tdp = cpu_tdp + gpu_tdp + system_overhead
    
    # Recommended PSU (with configurable headroom)
    psu_headroom = PSU_OVERHEAD_PERCENT / 100
    recommended_psu = int(total_tdp * (1 + psu_headroom))
    
    # Round to common PSU wattages
    recommended_psu = round_to_common_psu(recommended_psu)
    
    # Determine heat class
    heat_class = determine_heat_class(total_tdp)
    
    # Cooling recommendations
    cooling_rec = get_cooling_recommendation(cpu_tdp, heat_class)
    
    # Efficiency recommendation
    efficiency_rec = get_efficiency_recommendation(recommended_psu)
    
    return {
        "cpu_tdp": cpu_tdp,
        "gpu_tdp": gpu_tdp,
        "system_overhead": system_overhead,
        "total_tdp": total_tdp,
        "recommended_psu": recommended_psu,
        "recommended_psu_range": get_psu_range(recommended_psu),
        "heat_class": heat_class,
        "cooling_recommendation": cooling_rec,
        "efficiency_rating": efficiency_rec,
        "estimated_idle_power": estimate_idle_power(cpu_tdp, gpu_tdp),
        "estimated_gaming_power": int(total_tdp * 0.8),  # Typical gaming load
        "estimated_max_power": total_tdp,
    }


def estimate_tdp_from_tier(component: Dict, component_type: str) -> int:
    """
    Estimate TDP based on component tier and score when actual TDP unavailable.
    
    Args:
        component: Component dict
        component_type: "CPU" or "GPU"
        
    Returns:
        Estimated TDP in watts
    """
    tier = component.get("tier", "mid")
    score = component.get("normalized_score", 50)
    
    if component_type == "CPU":
        # CPU TDP estimates by tier
        base_tdp = {
            "low": 35,
            "mid": 65,
            "high": 105,
            "ultra": 125
        }.get(tier, 65)
        
        # Adjust by score within tier
        if score > 80:
            base_tdp += 20
        elif score > 60:
            base_tdp += 10
            
    else:  # GPU
        # GPU TDP estimates by tier
        base_tdp = {
            "low": 75,
            "mid": 150,
            "high": 250,
            "ultra": 350
        }.get(tier, 150)
        
        # Adjust by score within tier
        if score > 90:
            base_tdp += 50
        elif score > 70:
            base_tdp += 30
    
    logger.debug(f"Estimated TDP for {component.get('name', 'unknown')}: {base_tdp}W")
    return base_tdp


def round_to_common_psu(wattage: int) -> int:
    """Round to common PSU wattages."""
    common_wattages = [450, 550, 650, 750, 850, 1000, 1200, 1500]
    
    for w in common_wattages:
        if wattage <= w:
            return w
    
    return 1500  # Max common


def determine_heat_class(total_tdp: int) -> str:
    """Determine heat output class."""
    if total_tdp < 200:
        return "low"
    elif total_tdp < 350:
        return "medium"
    elif total_tdp < 500:
        return "high"
    else:
        return "extreme"


def get_cooling_recommendation(cpu_tdp: int, heat_class: str) -> str:
    """Get cooling recommendation based on CPU TDP and overall heat."""
    if cpu_tdp < 65:
        return "Stock cooler sufficient"
    elif cpu_tdp < 105:
        return "Good tower air cooler or 120mm AIO"
    elif cpu_tdp < 125:
        return "High-end tower cooler or 240mm AIO"
    elif cpu_tdp < 150:
        return "240-280mm AIO recommended"
    else:
        return "360mm AIO or custom loop recommended"


def get_efficiency_recommendation(psu_wattage: int) -> str:
    """Get PSU efficiency rating recommendation."""
    if psu_wattage <= 550:
        return "80+ Bronze minimum, 80+ Gold recommended"
    elif psu_wattage <= 750:
        return "80+ Gold recommended"
    elif psu_wattage <= 1000:
        return "80+ Gold or 80+ Platinum recommended"
    else:
        return "80+ Platinum or 80+ Titanium recommended"


def get_psu_range(recommended_psu: int) -> str:
    """Get PSU wattage range string."""
    lower = max(450, recommended_psu - 100)
    upper = recommended_psu + 100
    return f"{lower}-{upper}W"


def estimate_idle_power(cpu_tdp: int, gpu_tdp: int) -> int:
    """Estimate idle power consumption."""
    # Idle is typically 10-15% of max TDP + base system power
    cpu_idle = int(cpu_tdp * 0.12)
    gpu_idle = int(gpu_tdp * 0.10)
    system_base = 30  # MB, RAM, storage idle
    
    return cpu_idle + gpu_idle + system_base


def calculate_monthly_cost(
    power_watts: int,
    hours_per_day: float = 4.0,
    cost_per_kwh: float = 0.15
) -> Dict:
    """
    Calculate estimated electricity costs.
    
    Args:
        power_watts: Power consumption in watts
        hours_per_day: Average gaming hours per day
        cost_per_kwh: Electricity cost per kWh (USD)
        
    Returns:
        Dict with cost estimates
    """
    # Convert to kWh
    daily_kwh = (power_watts / 1000) * hours_per_day
    monthly_kwh = daily_kwh * 30
    yearly_kwh = daily_kwh * 365
    
    monthly_cost = monthly_kwh * cost_per_kwh
    yearly_cost = yearly_kwh * cost_per_kwh
    
    return {
        "daily_kwh": round(daily_kwh, 2),
        "monthly_kwh": round(monthly_kwh, 2),
        "yearly_kwh": round(yearly_kwh, 2),
        "monthly_cost_usd": round(monthly_cost, 2),
        "yearly_cost_usd": round(yearly_cost, 2),
        "assumptions": {
            "hours_per_day": hours_per_day,
            "cost_per_kwh_usd": cost_per_kwh,
        }
    }

