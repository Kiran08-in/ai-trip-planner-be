import asyncio

import httpx

from services import photos
from services.photos import strip_html, attach_photos


def test_strip_html_removes_tags_and_entities():
    assert strip_html('<a href="x">Ann &amp; Bob</a>') == "Ann & Bob"


def test_strip_html_handles_none_and_long_text():
    assert strip_html(None) == ""
    assert len(strip_html("a" * 500)) == 120


def test_attach_photos_adds_photo_or_none():
    places = [{"name": "A", "pageid": 1}, {"name": "B", "pageid": 2}]
    result = attach_photos(places, {1: {"url": "u"}})
    assert result[0]["photo"] == {"url": "u"}
    assert result[1]["photo"] is None
    assert "photo" not in places[0]


def test_get_photos_uses_cache_and_skips_network(monkeypatch):
    stored = {
        "photo:1": {"url": "u", "author": "A", "license": "CC BY 4.0", "license_url": "l", "page": "p"},
        "photo:2": {"missing": True},
    }
    monkeypatch.setattr(photos, "get_cached", lambda key: stored.get(key))

    async def boom(*args, **kwargs):
        raise AssertionError("the network must not be used")

    monkeypatch.setattr(photos, "fetch_thumbnails", boom)
    result = asyncio.run(photos.get_photos([1, 2]))
    assert result[1]["license"] == "CC BY 4.0"
    assert result[2] is None


def test_get_photos_drops_photo_without_license_and_remembers(monkeypatch):
    saved = {}
    monkeypatch.setattr(photos, "get_cached", lambda key: None)
    monkeypatch.setattr(photos, "set_cached", lambda key, data, ttl: saved.__setitem__(key, data))

    async def fake_thumbs(client, ids):
        return {1: {"url": "u1", "file": "a.jpg"}, 2: {"url": "u2", "file": "b.jpg"}}

    async def fake_licenses(client, files):
        return {"a.jpg": {"author": "A", "license": "CC BY 4.0", "license_url": "l", "page": "p"}}

    monkeypatch.setattr(photos, "fetch_thumbnails", fake_thumbs)
    monkeypatch.setattr(photos, "fetch_licenses", fake_licenses)
    result = asyncio.run(photos.get_photos([1, 2, 3]))
    assert result[1]["url"] == "u1"
    assert result[2] is None
    assert result[3] is None
    assert saved["photo:2"] == {"missing": True}
    assert saved["photo:3"] == {"missing": True}


def test_get_photos_network_error_saves_nothing(monkeypatch):
    saved = {}
    monkeypatch.setattr(photos, "get_cached", lambda key: None)
    monkeypatch.setattr(photos, "set_cached", lambda key, data, ttl: saved.__setitem__(key, data))

    async def fail(client, ids):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(photos, "fetch_thumbnails", fail)
    result = asyncio.run(photos.get_photos([1]))
    assert result == {}
    assert saved == {}