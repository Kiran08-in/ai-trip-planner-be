import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
import models
from main import app

load_dotenv()
test_url = make_url(os.getenv("DATABASE_URL")).set(database="tripbanao_test")
test_engine = create_engine(test_url)
TestSession = sessionmaker(bind=test_engine, autoflush=False)

assert test_engine.url.database == "tripbanao_test"


@pytest.fixture()
def client():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


GOOD = {
    "destination": "Goa",
    "days": 2,
    "budget": 5000,
    "plan": [{"day": 1}],
    "cost": {"low": 1000, "high": 3000},
}


def test_create_trip_returns_201(client):
    r = client.post("/trips", json=GOOD)
    assert r.status_code == 201
    assert r.json()["destination"] == "Goa"
    assert r.json()["id"] >= 1


def test_create_trip_rejects_too_many_days(client):
    r = client.post("/trips", json={**GOOD, "days": 10})
    assert r.status_code == 422


def test_list_trips_has_no_plan(client):
    client.post("/trips", json=GOOD)
    r = client.get("/trips")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert "plan" not in r.json()[0]


def test_get_trip_and_404(client):
    trip_id = client.post("/trips", json=GOOD).json()["id"]
    assert client.get(f"/trips/{trip_id}").json()["plan"] == [{"day": 1}]
    assert client.get("/trips/9999").status_code == 404


def test_delete_trip(client):
    trip_id = client.post("/trips", json=GOOD).json()["id"]
    assert client.delete(f"/trips/{trip_id}").status_code == 204
    assert client.delete(f"/trips/{trip_id}").status_code == 404