import asyncio
import html
import re
import httpx
from cache import get_cached, set_cached
from services.wiki_pedia import URL, HEADERS

PHOTO_TTL_HOURS = 24 * 30


async def fetch_thumbnails(client, ids):
    params = {
        "action": "query",
        "pageids": "|".join(str(i) for i in ids),
        "prop": "pageimages",
        "piprop": "thumbnail|name",
        "pithumbsize": 400,
        "format": "json",
    }
    response = await client.get(URL, params=params, headers=HEADERS)
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    found = {}
    for pid, page in pages.items():
        thumb = page.get("thumbnail")
        name = page.get("pageimage")
        if thumb and name:
            found[int(pid)] = {
                "url": thumb["source"],
                "width": thumb.get("width"),
                "height": thumb.get("height"),
                "file": name,
            }
    return found

def strip_html(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return " ".join(html.unescape(text).split())[:120]


async def fetch_licenses(client, files):
    titles = ["File:" + f for f in files]
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "extmetadata|url",
        "format": "json",
    }
    response = await client.get(URL, params=params, headers=HEADERS)
    response.raise_for_status()
    query = response.json().get("query", {})
    renamed = {n["from"]: n["to"] for n in query.get("normalized", [])}

    info_by_title = {}
    for page in query.get("pages", {}).values():
        infos = page.get("imageinfo")
        if not infos:
            continue
        meta = infos[0].get("extmetadata", {})
        license_name = strip_html(meta.get("LicenseShortName", {}).get("value", ""))
        if not license_name:
            continue
        info_by_title[page["title"]] = {
            "author": strip_html(meta.get("Artist", {}).get("value", "")) or "Unknown author",
            "license": license_name,
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "page": infos[0].get("descriptionurl", ""),
        }

    result = {}
    for f in files:
        title = "File:" + f
        title = renamed.get(title, title)
        if title in info_by_title:
            result[f] = info_by_title[title]
    return result

async def get_photos(pageids):
    result = {}
    missing = []
    for pid in pageids:
        cached = await asyncio.to_thread(get_cached, f"photo:{pid}")
        if cached is None:
            missing.append(pid)
        elif cached.get("missing"):
            result[pid] = None
        else:
            result[pid] = cached

    missing = missing[:50]
    if not missing:
        return result

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            thumbs = await fetch_thumbnails(client, missing)
            licenses = {}
            if thumbs:
                licenses = await fetch_licenses(client, [t["file"] for t in thumbs.values()])
    except (httpx.HTTPError, ValueError, KeyError) as e:
        print("photo error:", repr(e))
        return result

    for pid in missing:
        photo = None
        thumb = thumbs.get(pid)
        if thumb and thumb["file"] in licenses:
            photo = {"url": thumb["url"], **licenses[thumb["file"]]}
        await asyncio.to_thread(
            set_cached, f"photo:{pid}", photo or {"missing": True}, PHOTO_TTL_HOURS
        )
        result[pid] = photo
    return result

def attach_photos(places, photos):
    return [{**p, "photo": photos.get(p.get("pageid"))} for p in places]