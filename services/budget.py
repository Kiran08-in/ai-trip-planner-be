import json
from pathlib import Path

COSTS_FILE = Path(__file__).parent.parent / "costs.json"


def load_costs():
    with open(COSTS_FILE) as f:
        return json.load(f)
    
ORDER = ["D", "C", "B", "A"]  # from cheapest to most expensive


def pick_tier(population, num_places):
    if population is None:
        return "B"

    if population >= 5_000_000:
        level = 3
    elif population >= 1_000_000:
        level = 2
    elif population >= 100_000:
        level = 1
    else:
        level = 0

    if num_places >= 40 and level < 3:
        level += 1

    return ORDER[level]


def total_cost(prices, nights, days, num_places, i):
    return (
        nights * prices["stay"][i]
        + days * prices["food"][i]
        + days * prices["transport"][i]
        + num_places * prices["entry"][i]
    )


def estimate_range(tier, days, num_places, budget):
    prices = load_costs()[tier]
    nights = max(days - 1, 0)

    low = total_cost(prices, nights, days, num_places, 0)
    high = total_cost(prices, nights, days, num_places, 1)

    if budget < low:
        verdict = "likely not enough"
    elif budget <= high:
        verdict = "may fit"
    else:
        verdict = "comfortable"

    return {
        "tier": tier,
        "low": low,
        "high": high,
        "budget": budget,
        "verdict": verdict,
        "confidence": "tier estimate",
    }