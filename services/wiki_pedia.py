import re
import httpx
from fastapi import HTTPException


URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "TripBanao/1.0 (https://github.com/Kiran08-in) httpx/0.28"}

KINDS = [
    ("temple", {"temple", "mandir", "church", "mosque", "gurudwara", "basilica", "cathedral", "shrine", "math", "monastery"}),
    ("beach", {"beach"}),
    ("park", {"park", "garden", "gardens", "sanctuary", "zoo"}),
    ("viewpoint", {"viewpoint", "point", "hill", "peak", "lake", "falls", "waterfall", "dam"}),
    ("attraction", {"fort", "palace", "museum", "monument", "tomb", "cave", "caves", "ghat", "market", "tower", "memorial", "lighthouse", "ruins"}),
]
SKIP = {"school", "college", "university", "station", "hospital", "airport", "district", "block", "village", "tehsil", "stadium"}


def kind_of(title):
    words = set(re.findall(r"[a-z]+", title.lower()))
    if words & SKIP:
        return None
    for kind, keys in KINDS:
        if words & keys:
            return kind
    return None


async def get_nearby_places(lat, lon, radius=10000, limit=50):
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius,
        "gslimit": limit,
        "format": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(URL, params=params, headers=HEADERS)
        response.raise_for_status()
        items = response.json()["query"]["geosearch"]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        print("wiki error:", repr(e))
        raise HTTPException(status_code=503, detail="Places service is busy. Try again in a minute.")

    places = []
    for item in items:
        kind = kind_of(item["title"])
        if kind is None:
            continue
        places.append({
            "name": item["title"],
            "type": kind,
            "lat": item["lat"],
            "lon": item["lon"],
            "pageid": item["pageid"],
        })

    return places