from fastapi import FastAPI
from schema import TripRequest

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/plan/trip")
def plan_trip(trip: TripRequest):
    return {"received": trip}