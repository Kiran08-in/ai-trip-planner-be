from services.planner import haversine_km, group_into_days,pick_mix,travel_between,add_travel
from services.budget import pick_tier
from services.clothing import packing_for_day
from services.wiki_pedia import kind_of


def test_haversine_same_point_is_zero():
    assert haversine_km(15.5, 73.7, 15.5, 73.7) == 0


def test_haversine_one_degree_of_latitude():
    assert 110 < haversine_km(0, 0, 1, 0) < 112


def test_group_into_days_splits_places():
    places = [{"name": str(i), "lat": 15 + i * 0.01, "lon": 73.0} for i in range(6)]
    days = group_into_days(places, 2, per_day=3)
    assert len(days) == 2
    assert all(len(d) == 3 for d in days)


def test_pick_tier_unknown_population_is_b():
    assert pick_tier(None, 10) == "B"


def test_pick_tier_big_city_is_a():
    assert pick_tier(6_000_000, 5) == "A"


def test_pick_tier_many_places_moves_up():
    assert pick_tier(150_000, 10) == "C"
    assert pick_tier(150_000, 50) == "B"


def test_packing_rain_adds_umbrella():
    weather = {"temp_max": 28, "rain_chance": 80}
    assert "Umbrella or light raincoat" in packing_for_day(weather, [])


def test_packing_without_weather_does_not_crash():
    result = packing_for_day(None, [{"type": "temple"}])
    assert result == ["Cover shoulders and knees, and wear shoes that come off easily"]


def test_kind_of_temple():
    assert kind_of("Konark Sun Temple") == "temple"


def test_kind_of_skips_stations():
    assert kind_of("Puri Railway Station") is None

def make_weather(**changes):
    w = {
        "temp_max": 25, "temp_min": 20, "feels_like_max": None,
        "rain_chance": 0, "rain_mm": None, "humidity": None,
        "wind_max": None, "uv_max": None,
    }
    w.update(changes)
    return w


def test_high_uv_adds_sunscreen():
    items = packing_for_day(make_weather(uv_max=7.6), [])
    assert "Sunscreen and sunglasses" in items


def test_none_values_do_not_crash():
    items = packing_for_day(make_weather(temp_max=None, rain_chance=None), [])
    assert items == []


def test_attraction_gets_walking_shoes():
    items = packing_for_day(None, [{"type": "attraction"}])
    assert "Comfortable walking shoes" in items

def test_pick_mix_does_not_fill_with_one_type():
    places = [{"name": str(i), "type": "temple"} for i in range(6)]
    places.append({"name": "zoo", "type": "park"})
    chosen = pick_mix(places, 4)
    types = [p["type"] for p in chosen]
    assert len(chosen) == 4
    assert "park" in types

def test_travel_between_uses_road_factor():
    t = travel_between({"lat": 0, "lon": 0}, {"lat": 1, "lon": 0})
    assert 140 < t["km"] < 146
    assert 340 < t["minutes"] < 355


def test_add_travel_first_stop_has_no_travel():
    day = [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 0.1}]
    result = add_travel(day)
    assert result[0]["travel"] is None
    assert result[1]["travel"]["km"] > 0