import asyncio
import httpx
from cache import get_cached, set_cached

WEATHER_TTL_HOURS = 3


DAILY = [
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "precipitation_probability_max",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "wind_speed_10m_max",
    "uv_index_max",
]
async def get_weather(lat: float, lon: float, days: int):
    key = f"weather:{round(lat, 2)}:{round(lon, 2)}:{days}"
    cached = await asyncio.to_thread(get_cached, key)
    if cached is not None:
        return cached
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(DAILY),
        "timezone": "auto",
        "forecast_days": days
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    data = response.json()["daily"]

    result = []
    for i in range(len(data["time"])):
                result.append({
            "date": data["time"][i],
            "temp_max": data["temperature_2m_max"][i],
            "temp_min": data["temperature_2m_min"][i],
            "feels_like_max": data["apparent_temperature_max"][i],
            "rain_chance": data["precipitation_probability_max"][i],
            "rain_mm": data["precipitation_sum"][i],
            "humidity": data["relative_humidity_2m_mean"][i],
            "wind_max": data["wind_speed_10m_max"][i],
            "uv_max": data["uv_index_max"][i],
        })
    await asyncio.to_thread(set_cached, key, result, WEATHER_TTL_HOURS)
    return result