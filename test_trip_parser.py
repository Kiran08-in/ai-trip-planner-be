import asyncio

import pytest

from services import trip_parser
from services.trip_parser import parse_trip, NeedMoreInfo, ParseFailed


def fake_ai(monkeypatch, answers):
    calls = []

    async def fake(messages):
        calls.append(1)
        return answers[len(calls) - 1]

    monkeypatch.setattr(trip_parser, "ask_ai", fake)
    return calls


def test_good_json(monkeypatch):
    fake_ai(monkeypatch, ['{"destination": "Goa", "days": 3, "budget": 15000}'])
    trip = asyncio.run(parse_trip("3 days in Goa, 15000"))
    assert trip.destination == "Goa"
    assert trip.days == 3
    assert trip.budget == 15000


def test_json_inside_code_fence_and_extra_words(monkeypatch):
    answer = 'Sure! ```json\n{"destination": "Puri", "days": 2, "budget": 8000}\n```'
    fake_ai(monkeypatch, [answer])
    trip = asyncio.run(parse_trip("weekend in Puri, 8k"))
    assert trip.budget == 8000


def test_null_budget_asks_user_without_retry(monkeypatch):
    calls = fake_ai(monkeypatch, ['{"destination": "Goa", "days": 3, "budget": null}'])
    with pytest.raises(NeedMoreInfo):
        asyncio.run(parse_trip("3 days in Goa, low budget"))
    assert len(calls) == 1


def test_missing_destination_asks_user(monkeypatch):
    fake_ai(monkeypatch, ['{"destination": null, "days": 2, "budget": 5000}'])
    with pytest.raises(NeedMoreInfo):
        asyncio.run(parse_trip("2 days, 5000"))


def test_too_many_days_asks_user_without_retry(monkeypatch):
    calls = fake_ai(monkeypatch, ['{"destination": "Manali", "days": 10, "budget": 20000}'])
    with pytest.raises(NeedMoreInfo):
        asyncio.run(parse_trip("10 days in Manali, 20000"))
    assert len(calls) == 1


def test_broken_json_then_good_json_retries_once(monkeypatch):
    calls = fake_ai(monkeypatch, [
        "I think the trip is to Goa",
        '{"destination": "Goa", "days": 2, "budget": 6000}',
    ])
    trip = asyncio.run(parse_trip("Goa 2 days 6000"))
    assert trip.destination == "Goa"
    assert len(calls) == 2


def test_wrong_type_then_good_json_retries(monkeypatch):
    calls = fake_ai(monkeypatch, [
        '{"destination": "Puri", "days": 2, "budget": "8k"}',
        '{"destination": "Puri", "days": 2, "budget": 8000}',
    ])
    trip = asyncio.run(parse_trip("Puri 2 days 8k"))
    assert trip.budget == 8000
    assert len(calls) == 2


def test_two_bad_answers_fail_clearly(monkeypatch):
    calls = fake_ai(monkeypatch, ["no idea", "still no idea"])
    with pytest.raises(ParseFailed):
        asyncio.run(parse_trip("blah"))
    assert len(calls) == 2