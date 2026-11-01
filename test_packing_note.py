import asyncio

from fastapi.testclient import TestClient

import main
from services import packing_note
from services.ai import AIUnavailable

client = TestClient(main.app)

DAY = {
    "day": 1,
    "weather": {"temp_max": 33, "feels_like_max": 39, "rain_chance": 0,
                "humidity": None, "wind_max": 12, "uv_max": 8},
    "places": [{"name": "Dhauli", "type": "viewpoint"}],
    "packing": ["Sunscreen and sunglasses"],
}
RESULT = {"destination": "Bhubaneswar, Odisha, India", "plan": [DAY], "cost": {}, "note": None}
BODY = {"trip": {"destination": "Bhubaneswar", "days": 1, "budget": 5000}, "about_me": "I feel cold easily"}


def test_describe_day_has_facts_and_handles_none():
    text = packing_note.describe_day(DAY)
    assert "Dhauli" in text
    assert "Sunscreen" in text
    assert "rain chance 0%" in text
    assert "humidity unknown" in text


def test_write_note_sends_traveler_words_and_strips(monkeypatch):
    seen = {}

    async def fake_ask(messages):
        seen["messages"] = messages
        return "  Pack light.  "

    monkeypatch.setattr(packing_note, "ask_ai", fake_ask)
    note = asyncio.run(packing_note.write_note(RESULT, "I travel with my mother"))
    assert note == "Pack light."
    content = seen["messages"][1]["content"]
    assert "I travel with my mother" in content
    assert "Trip to Bhubaneswar." in content


def test_endpoint_returns_note_and_rule_list(monkeypatch):
    async def fake_build(trip, options):
        return RESULT

    async def fake_write(result, about_me):
        return "Pack light."

    monkeypatch.setattr(main, "build_plan", fake_build)
    monkeypatch.setattr(main, "write_note", fake_write)
    r = client.post("/ai/packing-note", json=BODY)
    assert r.status_code == 200
    assert r.json()["note"] == "Pack light."
    assert r.json()["packing"] == [["Sunscreen and sunglasses"]]


def test_endpoint_ai_down_is_503(monkeypatch):
    async def fake_build(trip, options):
        return RESULT

    async def fake_write(result, about_me):
        raise AIUnavailable("down")

    monkeypatch.setattr(main, "build_plan", fake_build)
    monkeypatch.setattr(main, "write_note", fake_write)
    assert client.post("/ai/packing-note", json=BODY).status_code == 503