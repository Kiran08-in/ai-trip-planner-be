import httpx
import asyncio
from cache import get_cached, set_cached

GEOCODE_TTL_HOURS = 24 * 30

async def geocode_city(city: str):
    key = f"geocode:{city.strip().lower()}"
    cached = await asyncio.to_thread(get_cached, key)
    if cached is not None:
        return cached
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1, "extratags": 1}
    headers = {"user-agent": "ai-trip-planner/1.0(student project)"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

    data = response.json()
    if not data: 
        return None

    extra = data[0].get("extratags") or {}
    population = None
    raw = extra.get("population")
    if raw:
        try:
            population = int(raw.replace(",", ""))
        except ValueError:
            population = None

    result = {
        "name": data[0]["display_name"],
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
        "population": population,
    }
    await asyncio.to_thread(set_cached, key, result, GEOCODE_TTL_HOURS)
    return result