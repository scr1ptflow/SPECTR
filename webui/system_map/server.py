import json
import os

from fastapi import FastAPI, Query as Q
from fastapi.responses import HTMLResponse

from long_range_sensor import edsm
from webui._utils import get_system, read_config, resolve_db, get_conn
from blackbox.exobiology import SPECIES_VALUE, HIGH_VALUE_GENUS, variant_base_name

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


def _value_tier(sub_type: str, valuable_exo: bool, terraforming_state: str) -> int:
    """0 = low, 1 = medium, 2 = high."""
    if valuable_exo:
        return 2
    st = sub_type.lower()
    high_types = {"earth-like world", "water world", "ammonia world", "water giant"}
    if st in high_types:
        return 2
    if terraforming_state and "terraformable" in terraforming_state.lower():
        return 2
    medium_types = {
        "high metal content world", "metal rich body",
        "gas giant with water based life", "gas giant with ammonia based life",
        "gas giant", "helium rich gas giant", "helium gas giant",
        "sudarsky class i gas giant", "sudarsky class ii gas giant",
        "sudarsky class iii gas giant", "sudarsky class iv gas giant",
        "sudarsky class v gas giant",
    }
    if st in medium_types:
        return 1
    return 0


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


def _build_user_value_map(conn) -> dict[str, int]:
    """Build {species -> per-set CR} from this user's SellOrganicData events."""
    rows = conn.execute(
        "SELECT raw_json FROM events WHERE event = 'SellOrganicData'"
    ).fetchall()
    m: dict[str, int] = {}
    for r in rows:
        d = json.loads(r[0])
        for item in d.get("BioData", []):
            va = item.get("Value", 0) or item.get("BaseValue", 0)
            sp = item.get("Species_Localised", "")
            if sp and va > 0:
                m[sp] = va
            vr = item.get("Variant_Localised", "")
            if vr and va > 0:
                base = variant_base_name(vr)
                if base not in m:
                    m[base] = va
    return m


def _get_valuable_bodies(conn, system: str) -> dict[int, bool]:
    """Return {bodyId -> has_valuable_exo} for the given system.

    A body is valuable if any scanned species on it has a per-set
    value >= 1 000 000 CR — checked first from this user's sold data,
    then from the shared price table, then by genus heuristic.
    """
    user_vals = _build_user_value_map(conn)

    rows = conn.execute(
        "SELECT raw_json FROM events WHERE event = 'ScanOrganic' AND system = ?",
        (system,),
    ).fetchall()

    body_valuable: dict[int, bool] = {}
    for r in rows:
        d = json.loads(r[0])
        body_id = d.get("Body")
        if body_id is None:
            continue
        if body_valuable.get(body_id):
            continue

        species = d.get("Species_Localised", "") or d.get("Species", "")
        genus = d.get("Genus_Localised", "") or ""

        # 1. Check user's actual sold data
        val = user_vals.get(species, 0)
        if val >= 1_000_000:
            body_valuable[body_id] = True
            continue

        # 2. Check shared price table
        if species in SPECIES_VALUE and SPECIES_VALUE[species] >= 1_000_000:
            body_valuable[body_id] = True
            continue

        # 3. Genus heuristic (high-value genus with no specific species data)
        if genus in HIGH_VALUE_GENUS:
            body_valuable[body_id] = True

    return body_valuable


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/system")
def api_system():
    sys_name = get_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    try:
        info = client.system_info(sys_name)
    except edsm.EdsmError as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": True,
        "system": sys_name,
        "coords": info.get("coords") if info else None,
    }


@sub_app.get("/api/bodies")
def api_bodies():
    sys_name = get_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    try:
        bodies = client.system_bodies(sys_name)
        stations = client.system_stations(sys_name)
    except edsm.EdsmError as e:
        return {"ok": False, "error": str(e)}

    # Valuable exobiology per body
    db_path = resolve_db()
    valuable_bodies: dict[int, bool] = {}
    if db_path and os.path.exists(db_path):
        conn = get_conn(db_path)
        try:
            valuable_bodies = _get_valuable_bodies(conn, sys_name)
        finally:
            conn.close()

    # Normalise bodies
    mapped = []
    for b in bodies:
        cat = _body_category(b.get("type", ""), b.get("subType", ""), b.get("parents"))
        sc = _star_color(b.get("starType", "")) if cat == "Star" else None
        ve = valuable_bodies.get(b.get("bodyId", None), False)
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
            "valuableExo": ve,
            "valueTier": _value_tier(b.get("subType", ""), ve, b.get("terraformingState", "")),
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
            "valuableExo": False,
            "valueTier": 0,
        })

    mapped.sort(key=lambda x: x["distance"])

    return {"ok": True, "system": sys_name, "bodies": mapped}


@sub_app.get("/api/nav")
def api_nav():
    """Return nearby systems for navigation context (within 50 LY)."""
    sys_name = get_system()
    if not sys_name:
        return {"ok": False, "error": "could not determine current system"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    try:
        spheres = client.sphere_systems(sys_name, radius=50)
    except edsm.EdsmError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "system": sys_name, "nearby": spheres}
