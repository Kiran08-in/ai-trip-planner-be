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
from services.plan_builder import build_plan

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
    return await build_plan(trip)

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