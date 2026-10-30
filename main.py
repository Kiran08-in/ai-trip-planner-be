from fastapi import FastAPI,HTTPException,Depends
from services.geocode import geocode_city
from services.weather import get_weather
from services.places import get_places
from services.planner import group_into_days,pick_mix,add_travel,order_days_by_weather
import httpx
from services.budget import pick_tier, estimate_range
from fastapi.middleware.cors import CORSMiddleware
from services.clothing import packing_for_day
from services.wiki_pedia import get_nearby_places
from sqlalchemy.orm import Session
from database import get_db
from models import Trip
from schema import TripRequest, TripCreate, TripOut,TripSummary
from sqlalchemy import select
from schema import AskRequest
from services.ai import ask_ai, AIUnavailable
from services.trip_parser import parse_trip, NeedMoreInfo, ParseFailed
from schema import ChatRequest
from services.assistant import chat as assistant_chat

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

    days = order_days_by_weather(days, weather)
    plan = []
    planned_places = 0
    for i, day_places in enumerate(days):
        planned_places += len(day_places)
        day_weather = weather[i] if i < len(weather) else None
        plan.append({
            "day": i + 1,
            "weather": day_weather,
            "places":  add_travel(day_places),
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

@app.post("/trips", response_model=TripOut, status_code=201)
def create_trip(data: TripCreate, db: Session = Depends(get_db)):
    trip = Trip(**data.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@app.get("/trips", response_model=list[TripSummary])
def list_trips(db: Session = Depends(get_db)):
    query = select(Trip).order_by(Trip.created_at.desc())
    return db.scalars(query).all()


@app.get("/trips/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    return trip

@app.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="trip not found")
    db.delete(trip)
    db.commit()

@app.post("/ai/ask")
async def ai_ask(body: AskRequest):
    try:
        answer = await ask_ai([{"role": "user", "content": body.message}])
    except AIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"answer": answer}

@app.post("/ai/parse-trip", response_model=TripRequest)
async def ai_parse_trip(body: AskRequest):
    try:
        return await parse_trip(body.message)
    except (NeedMoreInfo, ParseFailed) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except AIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/ai/chat")
async def ai_chat(body: ChatRequest):
    try:
        return await assistant_chat([t.model_dump() for t in body.messages])
    except AIUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))