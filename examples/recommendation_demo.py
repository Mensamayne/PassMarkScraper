"""
Demonstration script for PassMark Recommendation API.

This script shows how to use the new gaming analysis and recommendation features.
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:9091"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_json(data: Dict[Any, Any]):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def analyze_pairing_example():
    """Example: Analyze CPU+GPU pairing."""
    print_section("Example 1: Analyze CPU+GPU Pairing")

    payload = {"cpu": "Ryzen 7 7800X3D", "gpu": "RTX 4070"}

    print(f"Analyzing pairing: {payload['cpu']} + {payload['gpu']}")

    response = requests.post(f"{BASE_URL}/analyze-pairing", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Analysis complete!")
        print(f"   Overall Balance Score: {data['overall_balance_score']}/100")
        print(f"   Verdict: {data['overall_verdict']}")
        print(f"   Bottleneck: {data['overall_bottleneck'] or 'None'}")

        print("\n📊 Performance by Game Category:")
        for category, analysis in data["by_category"].items():
            print(f"\n   {category.upper()}")
            print(f"     Balance: {analysis['balance_score']}/100")
            print(f"     Performance: {analysis['performance']}")
            print(f"     Bottleneck: {analysis['bottleneck'] or 'None'}")
            print(f"     CPU Usage: {analysis['cpu_utilization']}%")
            print(f"     GPU Usage: {analysis['gpu_utilization']}%")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


def extreme_mismatch_example():
    """Example: Test extreme component mismatch."""
    print_section("Example 2: Extreme Mismatch (i3 + RTX 4090)")

    payload = {"cpu": "i3-12100F", "gpu": "RTX 4090"}

    print(f"Testing absurd pairing: {payload['cpu']} + {payload['gpu']}")

    response = requests.post(f"{BASE_URL}/analyze-pairing", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n⚠️  Analysis complete!")
        print(f"   Overall Balance Score: {data['overall_balance_score']}/100")
        print(f"   Verdict: {data['overall_verdict']}")
        print(f"   Bottleneck: {data['overall_bottleneck']}")

        print("\n🔍 Issues Found:")
        for category, analysis in data["by_category"].items():
            if not analysis["meets_minimum"] or analysis["balance_score"] < 50:
                print(f"\n   {category.upper()}: PROBLEMS DETECTED")
                print(f"     Balance: {analysis['balance_score']}/100")
                if analysis["issues"]:
                    for issue in analysis["issues"]:
                        print(f"     ⚠️  {issue}")
    else:
        print(f"❌ Error: {response.status_code}")


def recommend_gpu_example():
    """Example: Get GPU recommendations for a CPU."""
    print_section("Example 3: Recommend GPU for CPU")

    cpu = "7800X3D"
    game_focus = "aaa_gpu"

    print(f"Finding best GPUs for {cpu} (focus: {game_focus})")

    response = requests.get(
        f"{BASE_URL}/recommend-pairing",
        params={"cpu": cpu, "game_focus": game_focus, "limit": 3},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Recommendations for {data['base_component']['name']}:")

        for i, rec in enumerate(data["recommendations"], 1):
            print(f"\n   {i}. {rec['name']}")
            print(f"      Match Score: {rec['match_score']}/100")
            print(f"      Tier: {rec['tier']}")
            print(f"      Balance: {rec['balance_description']}")
    else:
        print(f"❌ Error: {response.status_code}")


def gaming_profile_example():
    """Example: Get complete gaming profile."""
    print_section("Example 4: Gaming Performance Profile")

    payload = {"cpu": "Ryzen 5 7600", "gpu": "RTX 4060", "resolution": "1440p"}

    print(f"Gaming profile for: {payload['cpu']} + {payload['gpu']} @ {payload['resolution']}")

    response = requests.post(f"{BASE_URL}/gaming-profile", json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Profile generated!")
        print(f"   Overall Score: {data['overall_balance_score']}/100")
        print(f"   Verdict: {data['overall_verdict']}")

        print("\n🎮 Performance by Game Type:")
        for category, perf in data["performance_by_category"].items():
            print(f"\n   {category.upper()}")
            print(f"     Games: {', '.join(perf['games'][:2])}")
            print(f"     FPS: {perf['fps_estimate']}")
            print(f"     Settings: {perf['settings']}")
            print(f"     Bottleneck: {perf['bottleneck'] or 'None'}")

        print(f"\n💡 Upgrade Priority: {data['upgrade_recommendations']['priority']}")
        print(f"   Reason: {data['upgrade_recommendations']['reason']}")
    else:
        print(f"❌ Error: {response.status_code}")


def performance_estimate_example():
    """Example: Estimate performance for single component."""
    print_section("Example 5: Performance Estimation")

    component = "RTX 4070"
    comp_type = "GPU"

    print(f"Estimating performance for: {component}")

    response = requests.get(
        f"{BASE_URL}/estimate-performance", params={"component": component, "type": comp_type}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ {data['component_name']}")
        print(f"   Tier: {data['tier']}")
        print(f"   Score: {data['normalized_score']}/100")

        print("\n📊 Gaming Tiers:")
        for res, tier in data["gaming_tiers"].items():
            print(f"   {res}: {tier}")

        print("\n🎯 FPS Estimates (selected):")
        estimates = data["estimated_performance"]
        print(f"   1080p High: {estimates['1080p_high']}")
        print(f"   1080p Ultra: {estimates['1080p_ultra']}")
        print(f"   1440p Ultra: {estimates['1440p_ultra']}")
        print(f"   4K Ultra: {estimates['4K_ultra']}")

        print(f"\n⚠️  {data['note']}")
    else:
        print(f"❌ Error: {response.status_code}")


def game_categories_example():
    """Example: List all game categories."""
    print_section("Example 6: Game Categories")

    response = requests.get(f"{BASE_URL}/game-categories")

    if response.status_code == 200:
        data = response.json()
        print("Available game categories:\n")

        for name, info in data["categories"].items():
            print(f"📁 {info['display_name']}")
            print(f"   {info['description']}")
            print(f"   CPU: {info['cpu_importance']} | GPU: {info['gpu_importance']}")
            print(f"   Weight: {info['weight_in_analysis']}")
            print(f"   Examples: {', '.join(info['examples'][:3])}")
            print()
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    """Run all examples."""
    print("\n" + "🎮" * 30)
    print("  PassMark Recommendation API - Demo")
    print("🎮" * 30)

    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ Server not responding. Make sure API is running on port 9091")
            return
    except requests.exceptions.RequestException:
        print("\n❌ Cannot connect to server. Make sure API is running on port 9091")
        print("   Start server with: uvicorn app.main:app --port 9091")
        return

    # Run examples
    analyze_pairing_example()
    extreme_mismatch_example()
    recommend_gpu_example()
    gaming_profile_example()
    performance_estimate_example()
    game_categories_example()

    print("\n" + "=" * 60)
    print("  ✅ Demo completed!")
    print("  📚 Full documentation: http://localhost:9091/docs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

