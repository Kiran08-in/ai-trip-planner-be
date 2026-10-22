from pydantic import BaseModel,Field

class TripRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    days: int = Field(ge=1, le=7)
    budget: int = Field(gt=0)