from fastapi.testclient import TestClient

import main
from schema import PlanOptions
from services.ai import AIUnavailable
from services.replanner import ReplanFailed

client = TestClient(main.app)
BODY = {"trip": {"destination": "Goa", "days": 2, "budget": 5000}, "message": "less walking"}


def test_replan_returns_plan_reason_and_options(monkeypatch):
    seen = {}

    async def fake_understand(text):
        return PlanOptions(places_per_day=2), "Two places a day."

    async def fake_build(trip, options):
        seen["options"] = options
        return {"destination": "Goa", "plan": [], "cost": {}, "note": None}

    monkeypatch.setattr(main, "understand_request", fake_understand)
    monkeypatch.setattr(main, "build_plan", fake_build)

    r = client.post("/ai/replan", json=BODY)
    assert r.status_code == 200
    assert r.json()["reason"] == "Two places a day."
    assert r.json()["options"]["places_per_day"] == 2
    assert seen["options"].places_per_day == 2


def test_replan_nothing_to_change_is_422(monkeypatch):
    async def fake_understand(text):
        raise ReplanFailed("I could not find a change to make.")

    monkeypatch.setattr(main, "understand_request", fake_understand)
    r = client.post("/ai/replan", json=BODY)
    assert r.status_code == 422


def test_replan_ai_down_is_503(monkeypatch):
    async def fake_understand(text):
        raise AIUnavailable("down")

    monkeypatch.setattr(main, "understand_request", fake_understand)
    r = client.post("/ai/replan", json=BODY)
    assert r.status_code == 503


def test_replan_bad_trip_is_422_before_any_ai_call():
    bad = {"trip": {"destination": "Goa", "days": 10, "budget": 5000}, "message": "x"}
    assert client.post("/ai/replan", json=bad).status_code == 422