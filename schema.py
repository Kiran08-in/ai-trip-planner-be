from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    days: int = Field(ge=1, le=7)
    budget: int = Field(gt=0)

class TripCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=300)
    days: int = Field(ge=1, le=7)
    budget: int = Field(gt=0)
    plan: list[dict]
    cost: dict


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination: str
    days: int
    budget: int
    plan: list[dict]
    cost: dict
    created_at: datetime


class TripSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination: str
    days: int
    budget: int
    created_at: datetime

class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)