# TripBanao (backend)

TripBanao builds a day by day trip plan from a city name. It finds tourist places near the city, groups the places that are close to each other into the same day, adds the weather for each day, suggests what to pack, and estimates a cost range for your budget.

Frontend repo: https://github.com/Kiran08-in/AI-trip-planner-fe

## What it does

- Finds the location of a city (latitude, longitude, population)
- Finds notable tourist places near the city
- Groups places by distance, so each day stays in one area
- Gets the weather forecast for each day
- Suggests what to pack from the weather and the types of places
- Estimates a cost range, and says if the budget is "likely not enough", "may fit", or "comfortable"

## Tech stack

Python, FastAPI, Uvicorn, Pydantic, httpx, pytest

## Data sources (all free, no API key)

- **Nominatim (OpenStreetMap):** city name to latitude and longitude, and population when available
- **Open-Meteo:** weather forecast
- **Wikipedia GeoSearch:** notable places near a point (content from Wikipedia, credit to its contributors)
- **Overpass API (OpenStreetMap):** used by the optional `/places` endpoint. I stopped using it for the main plan, because it was often slow and busy.

Map data © OpenStreetMap contributors.

## How to run

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API in Swagger.

## How to run the tests

```
pytest
```

## Main endpoint

`POST /plan/trip`

Request:
```json
{"destination": "Puri, Odisha", "days": 3, "budget": 12000}
```
- `days` must be from 1 to 7
- `budget` is the total in rupees, and must be above 0

Response (shortened):
```json
{
  "destination": "Puri, Odisha, India",
  "plan": [
    {
      "day": 1,
      "weather": {"date": "2026-10-22", "temp_max": 32.1, "temp_min": 25.4, "rain_chance": 40},
      "places": [{"name": "Puri Beach", "type": "beach", "lat": 19.79, "lon": 85.82}],
      "packing": ["Light cotton clothes, a cap and sunscreen", "Swimwear and flip-flops"]
    }
  ],
  "cost": {"tier": "B", "low": 8100, "high": 15200, "budget": 12000, "verdict": "may fit", "confidence": "tier estimate"}
}
```

Other endpoints: `GET /health`, `GET /geocode?city=`, `GET /weather?lat=&lon=&days=`

## Project structure

```
main.py             the app and the routes
schema.py           Pydantic models for requests
services/
  geocode.py        city to latitude and longitude
  weather.py        forecast
  wiki_places.py    places near a point (Wikipedia)
  planner.py        distance and grouping places into days
  budget.py         price tiers and the cost range
  clothing.py       packing rules
costs.json          prices for each tier
test_planner.py     tests
```

## Limits

- **Costs are estimates.** A city is put in a price tier from its population and number of places, and each tier has a low and a high price in `costs.json`. These prices are rough, and they are not real quotes.
- **Places:** Wikipedia lists notable places only, within 10 km of the city point. Small local spots can be missing, and the type of a place (temple, beach, and so on) is guessed from its title.
- **Use a city name, not a state.** A state's point is far from any town, so few places are found.
- **Weather** is a short forecast from today.
- Free services have limits (for example, Nominatim allows about 1 request per second), so results are not cached yet.

## Planned for version 2

Local AI assistant (Ollama) that uses these functions as tools, local travel tips (RAG), PostgreSQL for saved trips and caching, place photos, richer weather, login, and Docker.