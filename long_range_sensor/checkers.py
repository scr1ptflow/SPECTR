import time

_checkers = {}


def checker(name, description):
    def wrapper(func):
        _checkers[name] = {"func": func, "description": description}
        return func
    return wrapper


def list_checkers():
    return {k: v["description"] for k, v in _checkers.items()}


def run_check(name, *args, **kwargs):
    c = _checkers.get(name)
    if not c:
        raise ValueError(f"Unknown check: {name}")
    return c["func"](*args, **kwargs)

_PAD_ORDER = {"S": 1, "M": 2, "L": 3}

STATION_TYPES = (
    ("planetary", "Planetary Port", "L"),
    ("planetary", "Planetary Outpost", "M"),
    ("planetary", "Asteroid base", "L"),
    ("station",   "Coriolis Starport", "L"),
    ("station",   "Ocellus Starport", "L"),
    ("station",   "Orbis Starport", "L"),
    ("station",   "Outpost", "M"),
    ("station",   "Mega Ship", "M"),
    ("carrier",   "Fleet Carrier", "L"),
)


def _station_info(station_type, ship_size):
    needed = _PAD_ORDER.get(ship_size, 3)
    for cat, match, pad in STATION_TYPES:
        if station_type == match or match.lower() in station_type.lower():
            have = _PAD_ORDER.get(pad, 3)
            return cat, pad, have >= needed
    return "other", "L", False


@checker("exobiology", "Find nearest Vista Genomics (planetary, station, carrier)")
def exobiology(system, edsm, radius=100, ship_size="L"):
    nearby = edsm.sphere_systems(system, radius=radius)
    nearby.sort(key=lambda s: s.get("distance") or 0)

    best = {}
    seen = set()

    for sys_data in nearby:
        sys_name = sys_data.get("name")
        if not sys_name or sys_name.lower() == system.lower():
            continue
        if sys_name in seen:
            continue
        seen.add(sys_name)

        stations = edsm.system_stations(sys_name)
        if not stations:
            time.sleep(0.05)
            continue

        d = sys_data.get("distance", 0)
        if not isinstance(d, (int, float)):
            d = 0

        for station in stations:
            svc_names = set()
            for lst in ("services", "otherServices"):
                for svc in station.get(lst, []):
                    if isinstance(svc, dict):
                        svc_names.add(svc.get("name", "").lower())
                    elif isinstance(svc, str):
                        svc_names.add(svc.lower())

            if not ("vista genomics" in svc_names or "vistagenomics" in svc_names):
                continue

            s_type = station.get("type", "Unknown")
            cat, pad, ok = _station_info(s_type, ship_size)
            if not ok or cat == "other":
                continue

            prev = best.get(cat)
            arrival = station.get("distanceToArrival", 0)
            if prev is None or d < prev["distance_ly"] or (d == prev["distance_ly"] and arrival < prev.get("distance_to_arrival_ls", 0)):
                best[cat] = {
                    "station": station.get("name", "Unknown"),
                    "system": sys_name,
                    "distance_ly": round(d, 2),
                    "type": s_type,
                    "category": cat,
                    "distance_to_arrival_ls": arrival,
                    "max_pad": pad,
                }

        time.sleep(0.1)

        if len(best) == 3:
            break

    results = [best[k] for k in ("planetary", "station", "carrier") if k in best]
    results.sort(key=lambda r: r["distance_ly"])
    return results
