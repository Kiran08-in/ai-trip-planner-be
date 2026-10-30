import httpx
from fastapi import HTTPException

from services.geocode import geocode_city
from services.weather import get_weather
from services.wiki_pedia import get_nearby_places
from services.planner import group_into_days, pick_mix, add_travel, order_days_by_weather
from services.budget import pick_tier, estimate_range
from services.clothing import packing_for_day


async def build_plan(trip):
    location = await geocode_city(trip.destination)
    if location is None:
        raise HTTPException(status_code=404, detail="city not found")

    places = await get_nearby_places(location["lat"], location["lon"])
    if not places:
        raise HTTPException(status_code=404, detail="no places found")

    per_day = max(1, min(4, len(places) // trip.days))
    chosen = pick_mix(places, trip.days * per_day)
    days = group_into_days(chosen, trip.days, per_day=per_day)

    try:
        weather = await get_weather(location["lat"], location["lon"], trip.days)
    except (httpx.HTTPError, KeyError, ValueError):
        weather = []

    days = order_days_by_weather(days, weather)

    plan = []
    planned_places = 0
    for i, day_places in enumerate(days):
        planned_places += len(day_places)
        day_weather = weather[i] if i < len(weather) else None
        plan.append({
            "day": i + 1,
            "weather": day_weather,
            "places": add_travel(day_places),
            "packing": packing_for_day(day_weather, day_places),
        })

    tier = pick_tier(location["population"], len(places))
    cost = estimate_range(tier, len(days), planned_places, trip.budget)

    note = None
    if len(days) < trip.days:
        note = f"We found only {len(places)} places, so the plan has {len(days)} days."

    return {"destination": location["name"], "plan": plan, "cost": cost, "note": note}