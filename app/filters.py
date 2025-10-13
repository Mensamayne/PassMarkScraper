"""Filters for categorizing components."""


def categorize_component(name: str, component_type: str) -> str:
    """
    Categorize component as 'consumer', 'workstation', or 'server'.
    Server components will be filtered out.
    """
    name_lower = name.lower()

    if component_type == "CPU":
        # Server - exclude only true server CPUs
        server_keywords = ["epyc", "xeon", "opteron", "ampere altra", "graviton", "neoverse"]
        if any(keyword in name_lower for keyword in server_keywords):
            return "server"

        # Workstation
        if any(keyword in name_lower for keyword in ["threadripper"]):
            return "workstation"

        # Everything else is consumer (includes Ryzen, Core, Pentium, Celeron, Athlon, FX, etc.)
        return "consumer"

    elif component_type == "GPU":
        # Server - exclude these
        if any(keyword in name_lower for keyword in ["tesla", "a100", "h100", "a40", "a30"]):
            return "server"

        # Workstation
        if any(
            keyword in name_lower
            for keyword in ["rtx pro", "rtx 6000", "rtx 5000", "rtx 4000", "quadro"]
        ):
            return "workstation"

        # Consumer
        return "consumer"

    return "consumer"  # Default


def should_include_component(name: str, component_type: str) -> bool:
    """Check if component should be included (exclude server components)."""
    category = categorize_component(name, component_type)
    return category != "server"
