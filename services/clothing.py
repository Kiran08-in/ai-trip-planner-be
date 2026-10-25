def at_least(value, limit):
    return value is not None and value >= limit


def at_most(value, limit):
    return value is not None and value <= limit


def packing_for_day(weather, places):
    items = []

    if weather is not None:
        if at_least(weather.get("temp_max"), 32):
            items.append("Light cotton clothes and a cap")
        if at_most(weather.get("temp_max"), 15):
            items.append("Warm layers and a jacket")
        if at_least(weather.get("feels_like_max"), 38):
            items.append("Carry water and rest in shade")
        if at_least(weather.get("humidity"), 75) and at_least(weather.get("temp_max"), 28):
            items.append("Breathable, quick-dry clothes")
        if at_least(weather.get("wind_max"), 30):
            items.append("Windproof jacket, and hold your cap")
        if at_least(weather.get("uv_max"), 6):
            items.append("Sunscreen and sunglasses")
        if at_least(weather.get("rain_chance"), 50):
            items.append("Umbrella or light raincoat")
            items.append("Quick-dry clothes and shoes with good grip")
        if at_least(weather.get("rain_mm"), 10):
            items.append("Waterproof cover for your bag and phone")


    types = [p["type"] for p in places]
    if "temple" in types:
        items.append("Cover shoulders and knees, and wear shoes that come off easily")
    if "beach" in types:
        items.append("Swimwear and flip-flops")
    if "park" in types or "viewpoint" in types or "attraction" in types:
        items.append("Comfortable walking shoes")
    return items


if __name__ == "__main__":
    weather = {"date": "2026-10-19", "temp_max": 31.2, "temp_min": 24.9, "rain_chance": 80}
    places = [
        {"name": "Kuskem Waterfall", "type": "attraction"},
        {"name": "Dattatraya Temple", "type": "temple"},
    ]
    print(packing_for_day(weather, places))