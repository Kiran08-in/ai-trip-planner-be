import httpx

async def get_weather(lat: float, lon: float, days: int):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
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
            "rain_chance": data["precipitation_probability_max"][i],
        })
    return result