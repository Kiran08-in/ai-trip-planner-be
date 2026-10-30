from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

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

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[ChatTurn] = Field(min_length=1, max_length=20)

class PlanOptions(BaseModel):
    places_per_day: int | None = Field(default=None, ge=1, le=4)
    avoid_types: list[Literal["temple", "beach", "park", "viewpoint", "attraction"]] = Field(default_factory=list)
    indoor_only: bool = False
    max_hop_km: float | None = Field(default=None, gt=0, le=50)