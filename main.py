from fastapi import FastAPI,HTTPException
from schema import TripRequest
from services.geocode import geocode_city
from services.weather import get_weather
from services.places import get_places
from services.planner import group_into_days

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan/trip")
async def plan_trip(trip: TripRequest):
    location = await geocode_city(trip.destination)
    if location is None:
        raise HTTPException(status_code=404, detail="city not found")

    places = await get_places(location["lat"], location["lon"], "attraction", 10000)
    if not places:
        raise HTTPException(status_code=404, detail="no places found")

    days = group_into_days(places, trip.days, per_day=3)

    return {"destination": location["name"], "days": days}

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