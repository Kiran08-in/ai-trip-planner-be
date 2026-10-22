import httpx
import asyncio
from fastapi import HTTPException

CATEGORIES = {
    "beach": '["natural"="beach"]',
    "fort": '["historic"="fort"]',
    "food": '["amenity"="restaurant"]',
    "cafe": '["amenity"="cafe"]',
    "museum": '["tourism"="museum"]',
    "viewpoint": '["tourism"="viewpoint"]',
    "park": '["leisure"="park"]',
    "waterfall": '["waterway"="waterfall"]',
    "temple": '["amenity"="place_of_worship"]',
    "market": '["amenity"="marketplace"]',
    "nightlife": '["amenity"="bar"]',
    "attraction": '["tourism"="attraction"]',
}

async def get_places(lat: float, lon: float, category: str, radius: int):
    tag = CATEGORIES.get(category)
    if not tag:
        return None
    query = f"""
    [out:json][timeout:15];
    nwr{tag}(around:{radius},{lat},{lon});
    out center 10;
    """
    url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "ai-trip-planner/1.0 (student project)"}

    response = None
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(3):
            try:
                response = await client.post(url, data={"data": query}, headers=headers)
            except httpx.RequestError:
                response = None
            if response is not None and response.status_code == 200:
                break
            await asyncio.sleep(3)

    if response is None or response.status_code != 200:
        raise HTTPException(status_code=503, detail="Places service is busy. Try again in a minute.")

    elements = response.json()["elements"]
    places = []
    for e in elements:
        name = e.get("tags", {}).get("name")
        if not name:
            continue
        point = e.get("center", e)
        places.append({
            "name": name,
            "type": category,
            "lat": point["lat"],
            "lon": point["lon"],
        })
    return places