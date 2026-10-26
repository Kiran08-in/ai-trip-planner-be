import re
import httpx
import math
import asyncio
from fastapi import HTTPException
import httpx
from cache import get_cached, set_cached


URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "TripBanao/1.0 (https://github.com/Kiran08-in) httpx/0.28"}
PLACES_TTL_HOURS = 24 * 7
KINDS = [
    ("temple", {"temple", "mandir", "church", "mosque", "gurudwara", "basilica", "cathedral", "shrine", "math", "monastery", "dargah"}),
    ("beach", {"beach", "bay", "coast"}),
    ("park", {"park", "garden", "gardens", "sanctuary", "zoo", "reserve"}),
    ("viewpoint", {"viewpoint", "point", "hill", "hills", "peak", "lake", "falls", "waterfall", "dam", "island", "valley"}),
    ("attraction", {"fort", "palace", "museum", "monument", "tomb", "cave", "caves", "ghat", "market", "tower", "memorial", "lighthouse", "ruins", "heritage", "attraction", "aquarium", "planetarium"}),
]
SKIP = {
    "school", "college", "university", "station", "hospital", "airport", "district", "block",
    "village", "tehsil", "stadium", "neighbourhood", "neighborhood", "locality", "suburb", "road",
    "street", "junction", "colony", "ward", "railway", "technology", "business", "industrial", "it",
}


def kind_of(title, description=""):
    title_words = set(re.findall(r"[a-z]+", title.lower()))
    if title_words & SKIP:
        return None
    words = title_words | set(re.findall(r"[a-z]+", description.lower()))
    for kind, keys in KINDS:
        if words & keys:
            return kind
    return None


async def search_point(lat, lon, radius=10000, limit=200):
    params = {
        "action": "query",
        "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}",
        "ggsradius": radius,
        "ggslimit": limit,
        "prop": "coordinates|description",
        "colimit": "max",
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(URL, params=params, headers=HEADERS)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
    except (httpx.HTTPError, ValueError) as e:
        print("wiki error:", repr(e))
        raise HTTPException(status_code=503, detail="Places service is busy. Try again in a minute.")

    places = []
    for page in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        coords = page.get("coordinates")
        if not coords:
            continue
        kind = kind_of(page["title"], page.get("description", ""))
        if kind is None:
            continue
        places.append({
            "name": page["title"],
            "type": kind,
            "lat": coords[0]["lat"],
            "lon": coords[0]["lon"],
            "pageid": page["pageid"],
        })

    print("wiki: found", len(pages), "pages, kept", len(places))
    return places


def points_around(lat, lon, km=8):
    dlat = km / 111
    dlon = km / (111 * math.cos(math.radians(lat)))
    return [
        (lat, lon),
        (lat + dlat, lon),
        (lat - dlat, lon),
        (lat, lon + dlon),
        (lat, lon - dlon),
    ]

async def fetch_views(client, ids):
    params = {
        "action": "query",
        "pageids": "|".join(str(i) for i in ids),
        "prop": "pageviews",
        "format": "json",
    }
    result = {}
    for _ in range(10):
        response = await client.get(URL, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        for pid, page in data.get("query", {}).get("pages", {}).items():
            total = sum(v for v in page.get("pageviews", {}).values() if v)
            result[int(pid)] = max(result.get(int(pid), 0), total)
        if "continue" not in data:
            break
        params.update(data["continue"])
    return result


async def add_views(places):
    seat = asyncio.Semaphore(3)

    async with httpx.AsyncClient(timeout=10) as client:

        async def one_group(ids):
            async with seat:
                try:
                    return await fetch_views(client, ids)
                except (httpx.HTTPError, ValueError) as e:
                    print("views error:", repr(e))
                    return {}

        groups = [
            [p["pageid"] for p in places[i:i + 50]]
            for i in range(0, len(places), 50)
        ]
        results = await asyncio.gather(*(one_group(g) for g in groups))

    views = {}
    for r in results:
        views.update(r)

    for p in places:
        p["views"] = views.get(p["pageid"], 0)
    places.sort(key=lambda p: p["views"], reverse=True)
    return places

async def get_nearby_places(lat, lon):
    key = f"places:{round(lat, 2)}:{round(lon, 2)}"
    cached = await asyncio.to_thread(get_cached, key)
    if cached is not None:
        print("cache hit:", key)
        return cached

    seat = asyncio.Semaphore(3)

    async def limited_search(p_lat, p_lon):
        async with seat:
            return await search_point(p_lat, p_lon)

    points = points_around(lat, lon)
    results = await asyncio.gather(
        *(limited_search(p_lat, p_lon) for p_lat, p_lon in points),
        return_exceptions=True,
    )

    if isinstance(results[0], Exception):
        raise results[0]

    seen = set()
    places = []
    for found in results:
        if isinstance(found, Exception):
            continue
        for place in found:
            if place["pageid"] in seen:
                continue
            seen.add(place["pageid"])
            places.append(place)
    places = await add_views(places)
    if places:
        await asyncio.to_thread(set_cached, key, places, PLACES_TTL_HOURS)
    print("wiki: total unique places", len(places))
    
    return places