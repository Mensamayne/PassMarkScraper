"""Score normalization logic."""

import re


def normalize_name(name: str) -> str:
    """
    Normalize component name for matching.

    Examples:
        "GeForce RTX 4070" -> "rtx 4070"
        "AMD Ryzen 5 7600X" -> "ryzen 5 7600x"
    """
    name = name.lower()
    # Remove common prefixes
    name = re.sub(r"\b(nvidia|amd|intel|geforce|radeon)\b", "", name)
    # Remove special chars
    name = re.sub(r"[^a-z0-9\s]", "", name)
    # Remove extra spaces
    name = " ".join(name.split())
    return name.strip()


def normalize_cpu_score(passmark_score: int) -> int:
    """
    Normalize CPU score to 0-100 scale.

    PassMark CPU scores range: ~500 (low-end) to ~60,000 (HEDT)
    Gaming CPUs typically: 2,000 - 45,000
    """
    if passmark_score < 2000:
        return 10
    if passmark_score < 5000:
        return 20
    if passmark_score < 10000:
        return 35
    if passmark_score < 15000:
        return 50
    if passmark_score < 20000:
        return 65
    if passmark_score < 28000:
        return 80
    if passmark_score < 40000:
        return 92
    return 100


def normalize_gpu_score(g3d_score: int) -> int:
    """
    Normalize GPU score to 0-100 scale.

    PassMark G3D scores range: ~200 (GT 1030) to ~35,000 (RTX 4090)
    """
    if g3d_score < 1000:
        return 5
    if g3d_score < 3000:
        return 15
    if g3d_score < 6000:
        return 30
    if g3d_score < 10000:
        return 50
    if g3d_score < 15000:
        return 65
    if g3d_score < 20000:
        return 80
    if g3d_score < 28000:
        return 92
    return 100


def normalize_ram_score(ram_score: int) -> int:
    """
    Normalize RAM score to 0-100 scale.

    Real-world RAM scores (based on Read/Write GB/s):
    - Calculated as: (Read * 0.6 + Write * 0.4) * 300
    - Range: ~3,800 (entry DDR5) to ~7,500 (high-end DDR5)
    """
    if ram_score < 3500:
        return 10  # Below DDR5 standards
    if ram_score < 4200:
        return 25  # Entry DDR5 (4800-5200 MT/s)
    if ram_score < 4800:
        return 40  # Basic DDR5 (5200-5600 MT/s)
    if ram_score < 5400:
        return 55  # Mid-range DDR5 (5600-6000 MT/s)
    if ram_score < 6000:
        return 70  # Good DDR5 (6000-6400 MT/s)
    if ram_score < 6600:
        return 85  # High-end DDR5 (6400-6800 MT/s)
    if ram_score < 7200:
        return 92  # Top-tier DDR5 (6800-7200 MT/s)
    return 100  # Extreme DDR5 (7200+ MT/s)


def normalize_storage_score(disk_score: int) -> int:
    """
    Normalize Storage/Disk score to 0-100 scale.

    PassMark Disk scores range: ~500 (old HDD) to ~50,000 (top NVMe)
    """
    if disk_score < 1000:
        return 5  # Old HDD
    if disk_score < 5000:
        return 20  # Basic SSD
    if disk_score < 10000:
        return 35  # SATA SSD
    if disk_score < 20000:
        return 55  # Entry NVMe
    if disk_score < 30000:
        return 70  # Mid-range NVMe
    if disk_score < 40000:
        return 85  # High-end NVMe
    if disk_score < 50000:
        return 95  # Top-tier NVMe
    return 100


def get_tier(normalized_score: int) -> str:
    """Get performance tier based on normalized score."""
    if normalized_score < 30:
        return "low"
    if normalized_score < 60:
        return "mid"
    if normalized_score < 85:
        return "high"
    return "ultra"


def normalize_component_score(component_type: str, passmark_score: int) -> int:
    """
    Normalize component score based on type.

    Args:
        component_type: CPU, GPU, RAM, or STORAGE
        passmark_score: Raw PassMark score

    Returns:
        Normalized score (0-100)
    """
    type_upper = component_type.upper()

    if type_upper == "CPU":
        return normalize_cpu_score(passmark_score)
    elif type_upper == "GPU":
        return normalize_gpu_score(passmark_score)
    elif type_upper == "RAM":
        return normalize_ram_score(passmark_score)
    elif type_upper == "STORAGE":
        return normalize_storage_score(passmark_score)
    else:
        return 50  # Default fallback
