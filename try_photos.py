import asyncio
from services.wiki_pedia import get_nearby_places
from services.photos import get_photos


async def main():
    places = await get_nearby_places(20.26, 85.84)
    top = places[:8]
    photos = await get_photos([p["pageid"] for p in top])
    for p in top:
        photo = photos.get(p["pageid"])
        print(p["name"], "->", photo["license"] if photo else None)


asyncio.run(main())