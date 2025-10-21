"""Filters for categorizing components."""


def categorize_component(name: str, component_type: str) -> str:
    """
    Categorize component as 'consumer', 'mobile', 'workstation', or 'server'.
    """
    name_lower = name.lower()

    if component_type == "CPU":
        # Apple - exclude (M1, M2, M3, M4 processors)
        if ("apple" in name_lower or name_lower.startswith("m1 ")
                or name_lower.startswith("m2 ") or name_lower.startswith("m3 ")
                or name_lower.startswith("m4 ")):
            return "mobile"

        # Server - exclude
        server_keywords = ["epyc", "xeon", "opteron", "ampere altra", "graviton", "neoverse"]
        if any(keyword in name_lower for keyword in server_keywords):
            return "server"

        # Workstation
        if any(keyword in name_lower for keyword in ["threadripper"]):
            return "workstation"

        # Mobile/Laptop - exclude
        import re

        # Check for mobile patterns
        mobile_patterns = [
            r'\d+(hx|hs|hq|h|p|u)',  # Numbers followed by mobile suffix (9955HX, 12900H, etc)
            r'(hx|hs|hq|u|p)@',  # Mobile suffix before @
            # Removed: r'@.*ghz' - this incorrectly classifies desktop CPUs as mobile
        ]
        if any(re.search(pattern, name_lower) for pattern in mobile_patterns):
            return "mobile"

        # Simple keyword check
        mobile_keywords = ["mobile", "laptop", "ultra 5", "ultra 7", "ultra 9"]
        if any(keyword in name_lower for keyword in mobile_keywords):
            return "mobile"

        # Desktop consumer
        return "consumer"

    elif component_type == "GPU":
        # Server - exclude
        if any(keyword in name_lower for keyword in ["tesla", "a100", "h100", "a40", "a30"]):
            return "server"

        # Workstation - exclude
        workstation_keywords = [
            "rtx pro", "rtx 6000", "rtx 5000", "rtx 4000", "rtx 4500", "rtx 3500",
            "quadro", "pro w", "ada generation",  # Workstation cards
            "radeon pro", "firepro", "ai pro",  # AMD workstation
        ]
        if any(keyword in name_lower for keyword in workstation_keywords):
            return "workstation"

        # Mobile/Laptop - exclude
        mobile_keywords = [
            "mobile", "laptop", "max-q", "ti mobile",
            "gtx.*m ", "rtx.*m ",  # Old mobile naming (GTX 1050M, RTX 2060M)
        ]
        if any(keyword in name_lower for keyword in mobile_keywords):
            return "mobile"

        # Desktop consumer
        return "consumer"

    return "consumer"  # Default


def should_include_component(name: str, component_type: str) -> bool:
    """Check if component should be included (exclude server, mobile, workstation)."""
    category = categorize_component(name, component_type)
    return category == "consumer"


def is_desktop_component(name: str, component_type: str) -> bool:
    """Check if component is desktop (consumer) - exclude mobile, workstation, server."""
    category = categorize_component(name, component_type)
    return category == "consumer"
