import urllib.request
import urllib.parse
import json
import os
import logging
from datetime import datetime
from core.threads import submit as _api_submit

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class EdsmApi:
    def __init__(self, base_url="https://www.edsm.net/api-v1", api_key=""):
        self.BASE = base_url.rstrip("/")
        self._api_key = api_key
        self._cache = {}
        self._load_cache()

    def _cache_path(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, "edsm_cache.json")

    def _load_cache(self):
        path = self._cache_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_path(), "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except OSError as e:
            logger.warning(f"Failed to save EDSM cache: {e}")

    def fetch_system(self, system_name, callback=None):
        system_name = (system_name or "").strip()
        if not system_name:
            return
        if system_name in self._cache:
            if callback:
                callback(self._cache[system_name])
            return
        _api_submit(self._do_fetch, system_name, callback)

    def _do_fetch(self, system_name, callback):
        url = (
            f"{self.BASE}/system"
            f"?systemName={urllib.parse.quote(system_name)}"
            f"&showInformation=1&showCoordinates=1&showPermit=1"
            f"&showBodies=1"
        )
        if self._api_key:
            url += f"&apiKey={urllib.parse.quote(self._api_key)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EDOverlay/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())

            info = data.get("information", {})
            discovery = info.get("discovery", {})
            traffic = data.get("traffic", {})

            bodies_list = data.get("bodies", [])
            stations = data.get("stations", [])

            result = {
                "name": data.get("name", system_name),
                "discoverer": (
                    discovery.get("commander")
                    if isinstance(discovery, dict) else None
                ),
                "discovered": (
                    discovery.get("date") if isinstance(discovery, dict) else None
                ),
                "traffic_day": traffic.get("day", 0),
                "traffic_week": traffic.get("week", 0),
                "traffic_total": traffic.get("total", 0),
                "allegiance": info.get("allegiance"),
                "population": info.get("population", 0),
                "bodies_count": len(bodies_list),
                "stations": self._categorize_stations(stations),
            }
            self._cache[system_name] = result
            self._save_cache()
            if callback:
                callback(result)
        except Exception as e:
            logger.debug(f"EDSM fetch failed for {system_name}: {e}")
            self._cache[system_name] = {"name": system_name, "error": True}
            self._save_cache()


    @staticmethod
    def _categorize_stations(stations):
        counts = {"starports": 0, "outposts": 0, "carriers": 0, "planetary": 0}
        if not isinstance(stations, list):
            return counts
        for s in stations:
            stype = (s.get("type", "") or "").lower()
            if "fleet carrier" in stype:
                counts["carriers"] += 1
            elif "outpost" in stype:
                counts["outposts"] += 1
            elif "planetary" in stype or "asteroid" in stype:
                counts["planetary"] += 1
            elif "starport" in stype or "port" in stype:
                counts["starports"] += 1
            elif "mega ship" in stype:
                counts["starports"] += 1
        return counts


class CanonnApi:
    def __init__(self, base_url="https://api.canonn.tech/api/systems"):
        self.BASE = base_url.rstrip("/")
        self._cache = {}
        self._load_cache()

    def _cache_path(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, "canonn_cache.json")

    def _load_cache(self):
        path = self._cache_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_path(), "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except OSError as e:
            logger.warning(f"Failed to save Canonn cache: {e}")

    def fetch_system(self, system_name, callback=None):
        system_name = (system_name or "").strip()
        if not system_name:
            return
        if system_name in self._cache:
            if callback:
                callback(self._cache[system_name])
            return
        _api_submit(self._do_fetch, system_name, callback)

    def _do_fetch(self, system_name, callback):
        url = (
            f"{self.BASE}"
            f"?systemName={urllib.parse.quote(system_name)}&showInfo=true"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EDOverlay/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())

            result = {
                "name": system_name,
                "guardian_ruins": 0,
                "guardian_structures": 0,
                "guardian_beacons": 0,
                "thargoid_sites": 0,
                "has_guardian": False,
                "has_thargoid": False,
            }

            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("data", data.get("results", [data]))

            for item in items:
                if isinstance(item, dict):
                    site_type = (item.get("type", "") or "").lower()
                    category = (item.get("category", "") or "").lower()
                    if "guardian" in site_type or "guardian" in category:
                        result["has_guardian"] = True
                        if "ruin" in site_type:
                            result["guardian_ruins"] += 1
                        elif "structure" in site_type:
                            result["guardian_structures"] += 1
                        elif "beacon" in site_type:
                            result["guardian_beacons"] += 1
                        else:
                            result["guardian_ruins"] += 1
                    if "thargoid" in site_type or "thargoid" in category:
                        result["has_thargoid"] = True
                        result["thargoid_sites"] += 1

            self._cache[system_name] = result
            self._save_cache()
            if callback:
                callback(result)

        except Exception as e:
            logger.debug(f"Canonn fetch failed for {system_name}: {e}")
            self._cache[system_name] = {"name": system_name, "error": True}
            self._save_cache()


class InaraApi:
    ENDPOINT = "https://api.inara.cz/v1/"

    RANK_NAMES = {
        "combat": ["Harmless", "Mostly Harmless", "Novice", "Competent", "Expert", "Master", "Dangerous", "Deadly", "Elite"],
        "trade": ["Penniless", "Mostly Penniless", "Pedlar", "Dealer", "Merchant", "Broker", "Entrepreneur", "Tycoon", "Elite"],
        "exploration": ["Aimless", "Mostly Aimless", "Scout", "Surveyor", "Explorer", "Pathfinder", "Ranger", "Pioneer", "Elite"],
        "cqc": ["Helpless", "Mostly Helpless", "Amateur", "Semi Professional", "Professional", "Champion", "Hero", "Legend", "Elite"],
        "soldier": ["Defenceless", "Mostly Defenceless", "Rookie", "Soldier", "Gunslinger", "Warrior", "Gladiator", "Deadeye", "Elite"],
        "exobiologist": ["Directionless", "Mostly Directionless", "Compiler", "Collector", "Cataloguer", "Taxonomist", "Ecologist", "Geneticist", "Elite"],
        "mercenary": ["Defenceless", "Mostly Defenceless", "Rookie", "Mercenary", "Soldier of Fortune", "Warlord", "Commander", "Squadron Leader", "Elite"],
    }

    def __init__(self, api_key=""):
        self._api_key = api_key
        self._cache = {}
        self._load_cache()

    def _cache_path(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        return os.path.join(CACHE_DIR, "inara_cache.json")

    def _load_cache(self):
        path = self._cache_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_path(), "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except OSError as e:
            logger.warning(f"Failed to save Inara cache: {e}")

    def fetch_commander(self, commander_name, callback=None):
        name = (commander_name or "").strip()
        if not name or not self._api_key:
            return
        if name in self._cache:
            if callback:
                callback(self._cache[name])
            return
        _api_submit(self._do_fetch_commander, name, callback)

    def _do_fetch_commander(self, commander_name, callback):
        payload = {
            "appName": "SPECTR",
            "appVersion": "1.0",
            "isDeveloped": True,
            "apiKey": self._api_key,
            "events": [
                {
                    "eventName": "getCommanderProfile",
                    "eventTimestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "eventData": {
                        "searchName": commander_name,
                    },
                }
            ],
        }
        try:
            req = urllib.request.Request(
                self.ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "SPECTR/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())

            result = self._parse_commander(data, commander_name)
            self._cache[commander_name] = result
            self._save_cache()
            if callback:
                callback(result)
        except Exception as e:
            logger.debug(f"Inara fetch failed for {commander_name}: {e}")
            self._cache[commander_name] = {"name": commander_name, "error": True}
            self._save_cache()

    @staticmethod
    def _parse_commander(data, fallback_name):
        events = data.get("events", []) if isinstance(data, dict) else []
        profile = {}
        for ev in events:
            if ev.get("eventName") == "getCommanderProfile" and ev.get("eventStatus") == 1:
                profile = ev.get("eventData", {})
                break
        cmdr = profile.get("commander", {})
        ranks = cmdr.get("commanderRanks", {})
        result = {
            "name": cmdr.get("commanderName", fallback_name),
            "ranks": {},
            "squadron": cmdr.get("commanderSquadron"),
            "allegiance": cmdr.get("preferredAllegianceName"),
            "power": cmdr.get("preferredPowerName"),
        }
        for key, names in InaraApi.RANK_NAMES.items():
            rdata = ranks.get(key, {})
            idx = rdata.get("rank", -1)
            if 0 <= idx < len(names):
                result["ranks"][key] = names[idx]
        return result


REGIONS = [
    ("Inner Orion Spur", -12500, 12500, -1500, 1500, -12500, 12500),
    ("Outer Orion Spur", -25000, -12500, -2000, 2000, -25000, -12500),
    ("Perseus Arm", -35000, -20000, -5000, 5000, -35000, -20000),
    ("Sagittarius-Carina Arm", -15000, 15000, -5000, 5000, -35000, -15000),
    ("Scutum-Centaurus Arm", -15000, 15000, -5000, 5000, 10000, 30000),
    ("Norma Arm", -10000, 10000, -5000, 5000, 20000, 35000),
    ("Outer Arm", -50000, -30000, -5000, 5000, -50000, -30000),
    ("Galactic Centre", -2000, 2000, -2000, 2000, -2000, 2000),
    ("Formidine Rift", -20000, -10000, -3000, 3000, -10000, 0),
    ("Conflux", -10000, 0, -2000, 2000, 10000, 20000),
    ("Hawking's Gap", 5000, 15000, -2000, 2000, -15000, -5000),
    ("Achilles Alter", -5000, 5000, -2000, 2000, -5000, 0),
    ("Newton's Vault", -15000, -5000, -2000, 2000, 5000, 15000),
    ("Dryman's Hope", 10000, 20000, -2000, 2000, 10000, 20000),
    ("Kepler's Crest", -20000, -10000, -2000, 2000, 10000, 20000),
    ("Mare Somnia", 5000, 15000, -2000, 2000, -20000, -10000),
    ("Temple", -10000, 0, -2000, 2000, -10000, 0),
    ("Odyssey Gap", 0, 10000, -2000, 2000, -10000, 0),
    ("The Void", -15000, -5000, -2000, 2000, -15000, -5000),
]


def resolve_region(star_pos):
    if not star_pos or len(star_pos) < 3:
        return None
    x, y, z = star_pos[0], star_pos[1], star_pos[2]
    for name, xmin, xmax, ymin, ymax, zmin, zmax in REGIONS:
        if xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax:
            return name
    return None
