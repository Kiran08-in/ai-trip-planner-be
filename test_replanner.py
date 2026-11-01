import asyncio

import pytest

from services import replanner
from services.replanner import understand_request, ReplanFailed


def fake_ai(monkeypatch, answers):
    calls = []

    async def fake(messages):
        calls.append(1)
        return answers[len(calls) - 1]

    monkeypatch.setattr(replanner, "ask_ai", fake)
    return calls


def test_less_walking(monkeypatch):
    fake_ai(monkeypatch, [
        '{"places_per_day": 2, "avoid_types": [], "indoor_only": false, "max_hop_km": 3, "reason": "Two close places a day."}'
    ])
    options, reason = asyncio.run(understand_request("less walking"))
    assert options.places_per_day == 2
    assert options.max_hop_km == 3
    assert reason == "Two close places a day."


def test_json_in_code_fence_and_nulls(monkeypatch):
    answer = 'Sure ```json\n{"places_per_day": null, "avoid_types": ["temple"], "indoor_only": null, "max_hop_km": null, "reason": "No temples."}\n```'
    fake_ai(monkeypatch, [answer])
    options, reason = asyncio.run(understand_request("no temples"))
    assert options.avoid_types == ["temple"]
    assert options.places_per_day is None


def test_made_up_type_then_good_answer_retries(monkeypatch):
    calls = fake_ai(monkeypatch, [
        '{"avoid_types": ["spaceship"], "reason": "x"}',
        '{"avoid_types": ["beach"], "reason": "No beaches."}',
    ])
    options, reason = asyncio.run(understand_request("no beaches"))
    assert options.avoid_types == ["beach"]
    assert len(calls) == 2


def test_nothing_to_change_asks_user_without_retry(monkeypatch):
    calls = fake_ai(monkeypatch, [
        '{"places_per_day": null, "avoid_types": [], "indoor_only": false, "max_hop_km": null, "reason": "ok"}'
    ])
    with pytest.raises(ReplanFailed):
        asyncio.run(understand_request("hello"))
    assert len(calls) == 1


def test_two_bad_answers_fail(monkeypatch):
    calls = fake_ai(monkeypatch, ["no idea", "still no idea"])
    with pytest.raises(ReplanFailed):
        asyncio.run(understand_request("blah"))
    assert len(calls) == 2