import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from services.geocode import geocode_city
from services.weather import get_weather
from services.wiki_pedia import get_nearby_places


class WeatherArgs(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    days: int = Field(ge=1, le=7)


class PlacesArgs(BaseModel):
    city: str = Field(min_length=2, max_length=100)
    limit: int = Field(default=8, ge=1, le=15)


async def tool_get_weather(city, days):
    location = await geocode_city(city)
    if location is None:
        return {"error": f"city not found: {city}"}
    weather = await get_weather(location["lat"], location["lon"], days)
    return {"city": location["name"], "days": weather}


async def tool_find_places(city, limit):
    location = await geocode_city(city)
    if location is None:
        return {"error": f"city not found: {city}"}
    places = await get_nearby_places(location["lat"], location["lon"])
    top = [{"name": p["name"], "type": p["type"]} for p in places[:limit]]
    return {"city": location["name"], "places": top}


TOOL_FUNCTIONS = {
    "get_weather": (WeatherArgs, tool_get_weather),
    "find_places": (PlacesArgs, tool_find_places),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the daily weather forecast for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, for example Goa"},
                    "days": {"type": "integer", "description": "Number of days, 1 to 7"},
                },
                "required": ["city", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_places",
            "description": "Find famous places to visit near a city, most famous first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, for example Puri"},
                    "limit": {"type": "integer", "description": "How many places, 1 to 15"},
                },
                "required": ["city"],
            },
        },
    },
]


async def run_tool(name, arguments):
    entry = TOOL_FUNCTIONS.get(name)
    if entry is None:
        return {"error": f"unknown tool: {name}"}
    args_model, func = entry
    try:
        args = args_model(**(arguments or {}))
    except (ValidationError, TypeError) as e:
        return {"error": f"invalid arguments: {e}"}
    try:
        return await func(**args.model_dump())
    except (HTTPException, httpx.HTTPError, KeyError, ValueError) as e:
        print("tool error:", name, repr(e))
        return {"error": "the tool failed, try again later"}