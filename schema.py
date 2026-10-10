from pydantic import BaseModel

class TripRequest(BaseModel):
    destination: str
    days: int
    budget: int