from fastapi import FastAPI,HTTPException
from schema import TripRequest
from services.geocode import geocode_city

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan/trip")
def plan_trip(trip: TripRequest):
    return {"received": trip}

@app.get("/geocode")
async def geocode(city:str):
    result = await geocode_city(city)
    if result is None:
        raise HTTPException(status_code = 404, detail = "city not found")
    return result