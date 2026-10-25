from fastapi import FastAPI,HTTPException
from schema import TripRequest
from services.geocode import geocode_city
from services.weather import get_weather
from services.places import get_places
from services.planner import group_into_days,pick_mix
import httpx
from services.budget import pick_tier, estimate_range
from fastapi.middleware.cors import CORSMiddleware
from services.clothing import packing_for_day
from services.wiki_pedia import get_nearby_places

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan/trip")
async def plan_trip(trip: TripRequest):
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

    plan = []
    planned_places = 0
    for i, day_places in enumerate(days):
        planned_places += len(day_places)
        day_weather = weather[i] if i < len(weather) else None
        plan.append({
            "day": i + 1,
            "weather": day_weather,
            "places": day_places,
            "packing": packing_for_day(day_weather, day_places),
        })

    tier = pick_tier(location["population"], len(places))
    cost = estimate_range(tier, len(days), planned_places, trip.budget)

    note = None
    if len(days) < trip.days:
        note = f"We found only {len(places)} places, so the plan has {len(days)} days."

    return {"destination": location["name"], "plan": plan, "cost": cost, "note": note}

@app.get("/geocode")
async def geocode(city:str):
    result = await geocode_city(city)
    if result is None:
        raise HTTPException(status_code = 404, detail = "city not found")
    return result

@app.get("/weather")
async def weather(lat: float, lon: float, days: int):
    result = await get_weather(lat,lon,days)
    return result

@app.get("/places")
async def places(lat: float, lon: float, category: str, radius: int):
    result = await get_places(lat,lon,category,radius)
    if result is None:
        raise HTTPException(status_code=400, detail="Unknown category")
    return result