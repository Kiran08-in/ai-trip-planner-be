from fastapi import FastAPI,HTTPException
from schema import TripRequest
from services.geocode import geocode_city
from services.weather import get_weather
from services.places import get_places
from services.planner import group_into_days
import asyncio
from services.budget import pick_tier, estimate_range
from fastapi.middleware.cors import CORSMiddleware

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

    categories = ["attraction", "beach", "temple", "viewpoint", "park"]
    places = []
    seen = set()
    for cat in categories:
        try:
            found = await get_places(location["lat"], location["lon"], cat, 10000)
        except HTTPException:
            continue
        for p in found:
            if p["name"] not in seen:
                seen.add(p["name"])
                places.append(p)
        await asyncio.sleep(2)

    if not places:
        raise HTTPException(status_code=404, detail="no places found")

    days = group_into_days(places, trip.days, per_day=3)
    weather = await get_weather(location["lat"], location["lon"], trip.days)

    plan = []
    planned_places = 0
    for i, day_places in enumerate(days):
        planned_places += len(day_places)
        plan.append({
            "day": i + 1,
            "weather": weather[i] if i < len(weather) else None,
            "places": day_places,
        })

    tier = pick_tier(location["population"], len(places))
    cost = estimate_range(tier, len(days), planned_places, trip.budget, trip.stay_per_night)

    return {"destination": location["name"], "plan": plan, "cost": cost}

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