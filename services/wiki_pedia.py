import re
import httpx
from fastapi import HTTPException

URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "TripBanao/1.0 (https://github.com/Kiran08-in) httpx/0.28"}

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


async def get_nearby_places(lat, lon, radius=10000, limit=200):
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