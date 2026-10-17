ORDER = ["D", "C", "B", "A"]  # from cheapest to most expensive


def pick_tier(population, num_places):
    if population is None:
        return "B"

    if population >= 5_000_000:
        level = 3
    elif population >= 1_000_000:
        level = 2
    elif population >= 100_000:
        level = 1
    else:
        level = 0

    if num_places >= 40 and level < 3:
        level += 1

    return ORDER[level]


if __name__ == "__main__":
    print(pick_tier(None, 10))
    print(pick_tier(6_000_000, 5))
    print(pick_tier(150_000, 10))
    print(pick_tier(150_000, 50))
    print(pick_tier(30_000, 5))