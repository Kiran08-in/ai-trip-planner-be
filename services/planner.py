import math

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # radius of the Earth in km

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def nearest_place(current, candidates):
    best = None
    best_dist = None
    for p in candidates:
        d = haversine_km(current["lat"], current["lon"], p["lat"], p["lon"])
        if best_dist is None or d < best_dist:
            best = p
            best_dist = d
    return best


def group_into_days(places, days, per_day=3):
    remaining = places[:]
    plan = []

    for _ in range(days):
        if not remaining:
            break
        day = [remaining.pop(0)]
        while len(day) < per_day and remaining:
            nxt = nearest_place(day[-1], remaining)
            remaining.remove(nxt)
            day.append(nxt)
        plan.append(day)

    return plan

def pick_mix(places, count, max_share=0.5):
    cap = max(1, math.ceil(count * max_share))
    chosen = []
    used = {}

    for p in places:
        if len(chosen) == count:
            break
        kind = p["type"]
        if used.get(kind, 0) >= cap:
            continue
        chosen.append(p)
        used[kind] = used.get(kind, 0) + 1

    for p in places:
        if len(chosen) == count:
            break
        if p not in chosen:
            chosen.append(p)

    return chosen

if __name__ == "__main__":
    places = [
        {"name": "Calangute Beach", "lat": 15.5439, "lon": 73.7553},
        {"name": "Palolem Beach", "lat": 15.0100, "lon": 74.0232},
        {"name": "Baga Beach", "lat": 15.5553, "lon": 73.7517},
        {"name": "Agonda Beach", "lat": 15.0480, "lon": 73.9869},
        {"name": "Fort Aguada", "lat": 15.4925, "lon": 73.7736},
        {"name": "Cabo de Rama Fort", "lat": 15.0889, "lon": 73.9187},
    ]
    result = group_into_days(places, days=2, per_day=3)
    for i, day in enumerate(result, start=1):
        print("Day", i, [p["name"] for p in day])