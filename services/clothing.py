def packing_for_day(weather, places):
    items = []

    if weather is not None:
        if weather["temp_max"] >= 32:
            items.append("Light cotton clothes, a cap and sunscreen")
        if weather["temp_max"] <= 15:
            items.append("Warm layers and a jacket")
        if weather["rain_chance"] >= 50:
            items.append("Umbrella or light raincoat")
            items.append("Quick-dry clothes and shoes with good grip")

    types = [p["type"] for p in places]
    if "temple" in types:
        items.append("Cover shoulders and knees, and wear shoes that come off easily")
    if "beach" in types:
        items.append("Swimwear and flip-flops")
    if "park" in types or "viewpoint" in types:
        items.append("Comfortable walking shoes")

    return items


if __name__ == "__main__":
    weather = {"date": "2026-10-19", "temp_max": 31.2, "temp_min": 24.9, "rain_chance": 80}
    places = [
        {"name": "Kuskem Waterfall", "type": "attraction"},
        {"name": "Dattatraya Temple", "type": "temple"},
    ]
    print(packing_for_day(weather, places))