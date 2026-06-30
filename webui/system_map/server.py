import os

from fastapi import FastAPI, Query as Q
from fastapi.responses import HTMLResponse

from long_range_sensor import edsm
from long_range_sensor import journal as lrs_journal
from webui._utils import read_config, find_journal_dir, get_latest_journal

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR System Map")

PLANET_COLORS = {
    "Metal rich body": "#aa8866",
    "Rocky body": "#997755",
    "Icy body": "#aaccff",
    "Rocky ice world": "#88aadd",
    "Earth-like world": "#44cc88",
    "Water world": "#4488ff",
    "Water giant": "#3366dd",
    "Ammonia world": "#cc8844",
    "Gas giant with water based life": "#88bbcc",
    "Gas giant with ammonia based life": "#bb8844",
    "Gas giant": "#ddaa77",
    "High metal content world": "#bb8866",
    "Helium rich gas giant": "#cc9977",
    "Helium gas giant": "#ccaa88",
    "Sudarsky class i gas giant": "#ddbb99",
    "Sudarsky class ii gas giant": "#88bbcc",
    "Sudarsky class iii gas giant": "#ccaa77",
    "Sudarsky class iv gas giant": "#bb7766",
    "Sudarsky class v gas giant": "#aa5544",
}

STAR_CLASS_COLORS = {
    "O": "#9bb0ff", "B": "#aabfff", "A": "#dae8ff",
    "F": "#f8f7ff", "G": "#fff4e8", "K": "#ffd2a1",
    "M": "#ffb56b", "L": "#ff8f40", "T": "#ff6a2b",
    "Y": "#ff4422", "TTS": "#ff6633", "AeBe": "#ffccaa",
    "W": "#cceeff", "WN": "#cceeff", "WNC": "#cceeff",
    "WC": "#ddddff", "WO": "#eeeeef", "C": "#ffcccc",
    "CS": "#ffcccc", "CN": "#ffcccc", "H": "#ffffff",
    "MS": "#ffcccc", "S": "#ff8866", "D": "#ffffff",
    "WhiteDwarf": "#eef6ff", "NeutronStar": "#66ddff",
    "BlackHole": "#8844cc",
}

BODY_COLORS = {
    "Star": "#ff9900",
    "Planet": "#4488cc",
    "Moon": "#44aa66",
    "Belt": "#cc8844",
    "Station": "#ff6633",
    "Carrier": "#00bbcc",
}

BODY_ICONS = {
    "Star": "★",
    "Planet": "●",
    "Moon": "◎",
    "Belt": "◈",
    "Station": "⬡",
    "Carrier": "⊞",
}


def _star_color(star_type: str) -> str:
    """Map star spectral type to a color."""
    if not star_type:
        return "#ffcc88"
    # Try full match, then prefix match
    if star_type in STAR_CLASS_COLORS:
        return STAR_CLASS_COLORS[star_type]
    for prefix, color in STAR_CLASS_COLORS.items():
        if star_type.startswith(prefix):
            return color
    return "#ffcc88"


def _planet_color(sub_type: str) -> str:
    """Map planet subtype to a color."""
    if not sub_type:
        return "#4488cc"
    for key, color in PLANET_COLORS.items():
        if sub_type.lower() == key.lower():
            return color
    return "#4488cc"


def _body_category(body_type: str, sub_type: str = "", parents: list | None = None) -> str:
    t = body_type.lower()
    if t == "star":
        return "Star"
    if t == "planet":
        # EDSM returns parents as a list: [{"Star": 0}, {"Planet": 1}]
        if parents and isinstance(parents, list):
            for p in parents:
                if isinstance(p, dict) and "Planet" in p:
                    return "Moon"
        if "moon" in sub_type.lower():
            return "Moon"
        return "Planet"
    if "belt" in t or "ring" in t:
        return "Belt"
    return body_type or "Unknown"


def _get_journal_dir():
    config = read_config()
    return config.get("journal_path", "") or find_journal_dir()


def _get_current_system() -> str | None:
    jdir = _get_journal_dir()
    jfile = get_latest_journal(jdir)
    if not jfile:
        return None
    return lrs_journal.read_current_system(jfile)


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/system")
def api_system():
    sys_name = _get_current_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    info = client.system_info(sys_name)
    return {
        "ok": True,
        "system": sys_name,
        "coords": info.get("coords") if info else None,
    }


@sub_app.get("/api/bodies")
def api_bodies():
    sys_name = _get_current_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    bodies = client.system_bodies(sys_name)
    stations = client.system_stations(sys_name)

    # Normalise bodies
    mapped = []
    for b in bodies:
        cat = _body_category(b.get("type", ""), b.get("subType", ""), b.get("parents"))
        sc = _star_color(b.get("starType", "")) if cat == "Star" else None
        mapped.append({
            "name": b.get("name", "?"),
            "bodyId": b.get("bodyId", None),
            "type": b.get("type", ""),
            "subType": b.get("subType", ""),
            "category": cat,
            "distance": b.get("distanceToArrival", 0),
            "starType": b.get("starType", ""),
            "starColor": sc if cat == "Star" else None,
            "color": _planet_color(b.get("subType", "")) if cat == "Planet" else BODY_COLORS.get(cat, "#555"),
            "icon": BODY_ICONS.get(cat, "?"),
            "isLandable": b.get("isLandable", False),
            "gravity": b.get("gravity", None),
            "radius": b.get("radius", None),
            "surfaceTemp": b.get("surfaceTemperature", None),
            "atmosphere": b.get("atmosphere", ""),
            "tidallyLocked": b.get("tidallyLocked", False),
            "terraformingState": b.get("terraformingState", ""),
            "semiMajorAxis": b.get("semiMajorAxis", None),
            "eccentricity": b.get("eccentricity", None),
            "orbitalInclination": b.get("orbitalInclination", None),
            "periapsis": b.get("periapsis", None),
            "axialTilt": b.get("axialTilt", None),
            "orbitalPeriod": b.get("orbitalPeriod", None),
            "rotationalPeriod": b.get("rotationalPeriod", None),
            "rings": b.get("rings", None),
            "parents": b.get("parents", None),
            "stellarMass": b.get("stellarMass", None),
            "absoluteMagnitude": b.get("absoluteMagnitude", None),
        })

    # Normalise stations
    for s in stations:
        stype = s.get("type", "Station")
        is_carrier = stype.lower() == "fleetcarrier"
        cat = "Carrier" if is_carrier else "Station"
        mapped.append({
            "name": s.get("name", "?"),
            "type": stype,
            "subType": stype,
            "category": cat,
            "distance": s.get("distanceToArrival", 0),
            "starType": "",
            "starColor": None,
            "color": BODY_COLORS[cat],
            "icon": BODY_ICONS[cat],
            "isLandable": False,
            "gravity": None,
            "radius": None,
            "surfaceTemp": None,
            "atmosphere": "",
            "tidallyLocked": False,
            "terraformingState": "",
            "semiMajorAxis": None,
            "eccentricity": None,
            "orbitalInclination": None,
            "periapsis": None,
            "axialTilt": None,
            "orbitalPeriod": None,
            "rotationalPeriod": None,
            "rings": None,
            "parents": None,
            "stellarMass": None,
            "absoluteMagnitude": None,
            "stationType": stype,
            "allegiance": s.get("allegiance", ""),
            "economy": s.get("economy", ""),
            "government": s.get("government", ""),
            "pad": "L" if s.get("maxLandingPadSize", "").lower() == "large" else s.get("maxLandingPadSize", "?"),
        })

    mapped.sort(key=lambda x: x["distance"])

    return {"ok": True, "system": sys_name, "bodies": mapped}


@sub_app.get("/api/nav")
def api_nav():
    """Return nearby systems for navigation context (within 50 LY)."""
    sys_name = _get_current_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    spheres = client.sphere_systems(sys_name, radius=50)
    return {"ok": True, "system": sys_name, "nearby": spheres}
