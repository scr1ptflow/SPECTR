# Elite Dangerous journal parser — reads .log journal files and extracts
# commander state: ranks, progress, credits, ship, location, powerplay,
# exobiology scans, and more.
#
# Journal files are JSON-lines format. One JSON object per line, each line
# is a separate "event" with an "event" field naming the type.
# Files are named Journal.<timestamp>.log and rotated by the game.
#
# Key class: JournalReader
#   - find_journal_files() — scans the journal directory
#   - read_events() — yields JournalEvent objects line-by-line
#   - get_latest_event(type) — returns the most recent event of a given type
#   - get_*() methods — convenience wrappers that extract specific data

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Iterator

from spectr.data.species import base_value as data_base_value

log = logging.getLogger(__name__)


def _clean_str(val: str) -> str:
    """Strip Frontier placeholder prefixes like $government_None; -> None."""
    if not val:
        return ""
    cleaned = re.sub(r"^\$\w+_", "", val).rstrip(";")
    return cleaned if cleaned and cleaned != "None" else ""


# ---------------------------------------------------------------------------
# Ship type name resolution
# Maps the internal ship ID (e.g. "cobramkiii") to a display name.
# ---------------------------------------------------------------------------

_SHIP_TYPES: dict[str, str] = {
    # Small ships
    "sidewinder": "Sidewinder Mk I",
    "eagle": "Eagle",
    "empire_eagle": "Imperial Eagle",
    "hauler": "Hauler",
    "adder": "Adder",
    "viper": "Viper Mk III",
    "viper_mkiii": "Viper Mk III",
    "viper_mkiv": "Viper Mk IV",
    "cobramkiii": "Cobra Mk III",
    "cobra_mkiii": "Cobra Mk III",
    "cobramkiv": "Cobra Mk IV",
    "cobra_mkiv": "Cobra Mk IV",
    "cobra_mk_v": "Cobra Mk V",

    # Lakon
    "type6": "Type-6 Transporter",
    "type7": "Type-7 Transporter",
    "type8": "Type-8 Transporter",
    "type9": "Type-9 Heavy",
    "type9_military": "Type-10 Defender",
    "type11": "Type-11 Prospector",
    "keelback": "Keelback",

    # Saud Kruger
    "dolphin": "Dolphin",
    "orca": "Orca",
    "belugaliner": "Beluga Liner",
    "beluga": "Beluga Liner",

    # Zorgon Peterson
    "ferdelance": "Fer-de-Lance",
    "mamba": "Mamba",

    # Faulcon DeLacy
    "python": "Python",
    "python_nx": "Python Mk II",
    "anaconda": "Anaconda",

    # Krait
    "krait_mkii": "Krait Mk II",
    "krait_light": "Krait Phantom",

    # Diamondback / Asp
    "diamondback": "Diamondback Scout",
    "diamondbackxl": "Diamondback Explorer",
    "dbs": "Diamondback Scout",
    "dbx": "Diamondback Explorer",
    "asp": "Asp Explorer",
    "asp_scout": "Asp Scout",

    # Combat
    "vulture": "Vulture",

    # Federal
    "federation_dropship": "Federal Dropship",
    "federation_dropship_mkii": "Federal Assault Ship",
    "federation_gunship": "Federal Gunship",
    "federation_corvette": "Federal Corvette",

    # Imperial
    "empire_courier": "Imperial Courier",
    "empire_trader": "Imperial Clipper",
    "cutter": "Imperial Cutter",

    # Alliance
    "alliance_chieftain": "Alliance Chieftain",
    "alliance_challenger": "Alliance Challenger",
    "alliance_crusader": "Alliance Crusader",

    # New generation ships
    "explorer_nx": "Caspian Explorer",
    "mandalay": "Mandalay",
    "corsair": "Corsair",
    "kestrel": "Kestrel Mk II",
    "panther_mk2": "Panther Clipper Mk II",
    "lynx": "Lynx Highliner",

    # Ship-Launched Fighters
    "federal_fighter": "F63 Condor",
    "independent_fighter": "Taipan",
    "gdn_hybrid_fighter_v1": "Guardian Trident",
    "gdn_hybrid_fighter_v2": "Guardian Javelin",
    "gdn_hybrid_fighter_v3": "Guardian Lance",

    # Surface Vehicles
    "testbuggy": "SRV Scarab",
    "buggy": "SRV Scarab",
    "buggy_02": "SRV Scorpion",
    "V_LANDER01": "Nomad",

    # Misc
    "planetary_suite": "Planetary Approach Suite",
}


def resolve_ship_type(internal_id: str) -> str:
    return _SHIP_TYPES.get(internal_id, internal_id)


# ---------------------------------------------------------------------------
# Event wrapper
# ---------------------------------------------------------------------------

class JournalEvent:
    """Thin wrapper around a raw JSON event dict.

    Provides typed access (.event, .timestamp) and dict-like get()/[]/in.
    """

    def __init__(self, data: dict):
        self._data = data
        self.event = data.get("event", "")
        self.timestamp = data.get("timestamp", "")

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data


# ---------------------------------------------------------------------------
# Journal reader
# ---------------------------------------------------------------------------

class JournalReader:
    """Scans Elite Dangerous journal files and extracts game state.

    Usage:
        reader = JournalReader("/path/to/JournalDir")
        reader.get_commander()      # -> "Cmdr Name"
        reader.get_rank_levels()    # -> {"Combat": 5, ...}
        reader.get_organic_summary()  # -> aggregated exobiology data
    """

    def __init__(self, journal_path: str = ""):
        # Expand ~ so users can write ~/Saved Games/...
        self.journal_path = Path(journal_path).expanduser() if journal_path else None
        self._file_cache: list[Path] | None = None
        self._cache_path: Path | None = None

    def set_path(self, path: str) -> None:
        """Update the journal directory at runtime (called by SettingsPanel)."""
        self.journal_path = Path(path).expanduser() if path else None
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        self._file_cache = None
        self._cache_path = None

    def find_journal_files(self) -> list[Path]:
        """Return all Journal.*.log files sorted newest-first.

        Results are cached per directory to avoid repeated globs.
        """
        if not self.journal_path or not self.journal_path.exists():
            return []
        if self._file_cache is not None and self._cache_path == self.journal_path:
            return self._file_cache
        self._file_cache = sorted(
            self.journal_path.glob("Journal.*.log"), reverse=True
        )
        self._cache_path = self.journal_path
        return self._file_cache

    def latest_journal(self) -> Path | None:
        """Return the most recent journal file (highest timestamp)."""
        files = self.find_journal_files()
        return files[0] if files else None

    def read_events(self, filepath: Path | None = None) -> Iterator[JournalEvent]:
        """Yield all events from *filepath* (or the latest journal).

        Each line is parsed as JSON; malformed lines are silently skipped.
        """
        path = filepath or self.latest_journal()
        if not path or not path.exists():
            return

        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield JournalEvent(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    def read_all_events(self) -> Iterator[JournalEvent]:
        """Yield events from ALL journal files, newest files first."""
        for path in self.find_journal_files():
            yield from self.read_events(path)

    def get_latest_event(self, event_type: str) -> JournalEvent | None:
        """Find the most recent occurrence of *event_type* across all journals.

        Searches newest journal first and returns the LAST match in that file
        (since files are chronological, the last match in the newest file is
        the most recent event overall).
        """
        for path in self.find_journal_files():
            result = None
            for event in self.read_events(path):
                if event.event == event_type:
                    result = event
            if result is not None:
                return result
        return None

    def get_latest_events(self, *event_types: str) -> dict[str, JournalEvent | None]:
        """Find the most recent occurrence of each event type in a single pass.

        Returns a dict mapping each requested event type to its most recent
        JournalEvent (or None if not found). Scans journals only once.
        """
        wanted = set(event_types)
        results: dict[str, JournalEvent | None] = {t: None for t in event_types}
        found: set[str] = set()

        for path in self.find_journal_files():
            for event in self.read_events(path):
                if event.event in wanted and event.event not in found:
                    results[event.event] = event
                    found.add(event.event)
            if found == wanted:
                break

        return results

    def get_all_events(self, event_type: str) -> list[JournalEvent]:
        """Return ALL events of *event_type* across all journal files."""
        result: list[JournalEvent] = []
        for path in self.find_journal_files():
            for event in self.read_events(path):
                if event.event == event_type:
                    result.append(event)
        return result

    # --- Convenience getters ---

    def get_commander(self) -> str | None:
        event = self.get_latest_event("Commander")
        if event:
            return event.get("Name")
        return None

    def get_current_system(self) -> str | None:
        event = self.get_latest_event("Location")
        if event:
            return event.get("StarSystem")
        event = self.get_latest_event("FSDJump")
        if event:
            return event.get("StarSystem")
        return None

    def get_system_bodies(self) -> list[dict]:
        """Return bodies from the current system's Location or FSDJump event."""
        for event_type in ("Location", "FSDJump"):
            event = self.get_latest_event(event_type)
            if event:
                bodies = event.get("Bodies", [])
                if bodies:
                    return bodies
        return []

    def get_system_info(self) -> dict:
        """Return system-level metadata from Location or FSDJump."""
        for event_type in ("Location", "FSDJump"):
            event = self.get_latest_event(event_type)
            if event:
                faction = event.get("SystemFaction", "")
                if isinstance(faction, dict):
                    faction = faction.get("Name", "")
                return {
                    "system": event.get("StarSystem", ""),
                    "faction": _clean_str(faction),
                    "government": _clean_str(event.get("SystemGovernment", "")),
                    "economy": _clean_str(event.get("SystemEconomy", "")),
                    "security": _clean_str(event.get("SystemSecurity", "")),
                    "population": event.get("Population", 0),
                    "allegiance": _clean_str(event.get("SystemAllegiance", "")),
                    "body": event.get("Body", ""),
                    "body_type": event.get("BodyType", ""),
                    "station": event.get("StationName", ""),
                    "distance_ls": event.get("DistFromStarLs"),
                }
        return {}

    def get_ship_type(self) -> str | None:
        event = self.get_latest_event("Loadout")
        if event:
            return resolve_ship_type(event.get("Ship", ""))
        event = self.get_latest_event("LoadGame")
        if event:
            return resolve_ship_type(event.get("Ship", ""))
        return None

    def get_ship_name(self) -> str | None:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("ShipName")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("ShipName")
        return None

    def get_ship_ident(self) -> str | None:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("ShipIdent")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("ShipIdent")
        return None

    def get_credits(self) -> int | None:
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("Credits")
        return None

    def get_squadron(self) -> str | None:
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("SquadronName")
        return None

    def get_powerplay(self) -> dict | None:
        """Merge data from all Powerplay-related events into one dict.

        Returns {"power": str, "rank": int, "merits": int} or None if
        no powerplay data exists.
        """
        power = ""
        rank = None
        merits = None

        event = self.get_latest_event("Powerplay")
        if event:
            power = event.get("Power", "")
            rank = event.get("Rank", 0)
            merits = event.get("Merits", 0)

        join_event = self.get_latest_event("PowerplayJoin")
        if join_event:
            if not power:
                power = join_event.get("Power", "")
            if rank is None:
                rank = join_event.get("Rank", 0)
            if merits is None:
                merits = join_event.get("Merits", 0)

        defect_event = self.get_latest_event("PowerplayDefect")
        if defect_event:
            if not power:
                power = defect_event.get("ToPower", "")

        salary_event = self.get_latest_event("PowerplaySalary")
        if salary_event:
            if not power:
                power = salary_event.get("Power", "")

        merits_event = self.get_latest_event("PowerplayMerits")
        if merits_event:
            merits = max(merits or 0, merits_event.get("TotalMerits", 0))

        if power or rank or merits:
            return {"power": power, "rank": rank or 0, "merits": merits or 0}
        return None

    # --- Ranks ---

    _RANK_CATEGORIES = [
        "Combat", "Trade", "Explore", "CQC",
        "Empire", "Federation", "Soldier", "Exobiologist",
    ]

    def get_rank_levels(self) -> dict[str, int]:
        """Return {category: level} from the Rank event (0-based integer)."""
        event = self.get_latest_event("Rank")
        if event:
            return {
                cat: event.get(cat, 0)
                for cat in self._RANK_CATEGORIES
            }
        return {}

    def get_rank_progress(self) -> dict[str, int]:
        """Return {category: progress_pct} from the Progress event (0-100)."""
        event = self.get_latest_event("Progress")
        if event:
            return {
                cat: event.get(cat, 0)
                for cat in self._RANK_CATEGORIES
            }
        return {}

    # Rank name tables — index 0 is the lowest rank
    _RANK_NAMES: dict[str, list[str]] = {
        "Combat": ["Harmless", "Mostly Harmless", "Novice", "Competent", "Expert",
                   "Master", "Dangerous", "Deadly", "Elite"],
        "Trade": ["Penniless", "Mostly Penniless", "Peddler", "Dealer", "Merchant",
                  "Broker", "Entrepreneur", "Tycoon", "Elite"],
        "Explore": ["Aimless", "Mostly Aimless", "Explorer", "Pathfinder", "Surveyor",
                    "Trailblazer", "Strider", "Pioneer", "Elite"],
        "CQC": ["Helpless", "Mostly Helpless", "Amateur", "Semi-Professional",
                "Professional", "Champion", "Hero", "Legend", "Elite"],
        "Empire": ["None", "Outsider", "Serf", "Master", "Squire", "Knight", "Lord",
                   "Baron", "Viscount", "Count", "Earl", "Duke", "Prince", "King"],
        "Federation": ["None", "Recruit", "Midshipman", "Petty Officer",
                       "Chief Petty Officer", "Warrant Officer", "Ensign",
                       "Lieutenant", "Lieutenant Commander", "Post Commander",
                       "Post Captain", "Rear Admiral", "Vice Admiral", "Admiral"],
        "Soldier": ["Defenceless", "Unskilled", "Skilled", "Capable", "Proficient",
                    "Competent", "Expert", "Veteran", "Elite"],
        "Exobiologist": ["Directionless", "Mostly Directionless", "Explorer",
                         "Pathfinder", "Surveyor", "Trailblazer", "Strider",
                         "Pioneer", "Elite"],
    }

    def get_rank_name(self, category: str, level: int) -> str:
        """Return the human-readable rank name for *category* at *level*.

        e.g. get_rank_name("Combat", 8) -> "Elite"
        """
        names = self._RANK_NAMES.get(category, [])
        if 0 <= level < len(names):
            return names[level]
        return str(level)

    def get_rebuy(self) -> int | None:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("Rebuy")
        return None

    def get_notoriety(self) -> int:
        event = self.get_latest_event("Notoriety")
        if event:
            return event.get("Notoriety", 0)
        return 0

    # --- Exobiology / Organic data ---

    def get_organic_scans(self) -> dict:
        """Aggregate all ScanOrganic events, grouped by (species, variant, body, system).

        Each group has a "count" — number of samples taken (usually 1-3).
        """
        scans = []
        for event in self.read_all_events():
            if event.event == "ScanOrganic":
                scans.append({
                    "system": event.get("System") or event.get("StarSystem", ""),
                    "body": event.get("Body", ""),
                    "species": event.get("Species_Localised") or event.get("Species", ""),
                    "variant": event.get("Variant_Localised") or event.get("Variant", ""),
                    "genus": event.get("Genus_Localised") or event.get("Genus", ""),
                    "scan_type": event.get("ScanType", "Sample"),
                    "timestamp": event.timestamp,
                })

        groups: dict = {}
        for s in scans:
            key = (s["species"], s["variant"], s["body"], s["system"])
            if key not in groups:
                groups[key] = {**s, "count": 0}
            groups[key]["count"] += 1

        return groups

    def get_organic_sold(self) -> dict:
        """Aggregate all SellOrganicData events, grouped by (species, variant).

        Each group tracks total_value (value + bonus) and count of sales.
        """
        sold_map: dict = {}
        for event in self.read_all_events():
            if event.event == "SellOrganicData":
                for entry in event.get("BioData", []):
                    species = entry.get("Species_Localised") or entry.get("Species", "")
                    variant = entry.get("Variant_Localised") or entry.get("Variant", "")
                    val = entry.get("Value", 0) + entry.get("Bonus", 0)
                    key = (species, variant)
                    if key not in sold_map:
                        sold_map[key] = {"species": species, "variant": variant,
                                         "total_value": 0, "count": 0}
                    sold_map[key]["total_value"] += val
                    sold_map[key]["count"] += 1
        return sold_map

    def get_organic_summary(self) -> dict:
        """Compute the full exobiology summary in a single pass over all events.

        Returns a dict:
          total_sellable  — number of complete sets (3 samples each) available
          total_value     — predicted total CR from selling all complete sets
          pending         — list of pending set details, sorted by value descending
          sold_history    — dict of previously sold species (from get_organic_sold)

        The value prediction uses the species database (spectr/data/species.py).
        """
        scans: dict = {}
        sold_map: dict = {}

        for event in self.read_all_events():
            if event.event == "ScanOrganic":
                s = {
                    "system": event.get("System") or event.get("StarSystem", ""),
                    "body": event.get("Body", ""),
                    "species": event.get("Species_Localised") or event.get("Species", ""),
                    "variant": event.get("Variant_Localised") or event.get("Variant", ""),
                    "genus": event.get("Genus_Localised") or event.get("Genus", ""),
                    "scan_type": event.get("ScanType", "Sample"),
                    "timestamp": event.timestamp,
                }
                key = (s["species"], s["variant"], s["body"], s["system"])
                if key not in scans:
                    scans[key] = {**s, "count": 0}
                scans[key]["count"] += 1

            elif event.event == "SellOrganicData":
                for entry in event.get("BioData", []):
                    species = entry.get("Species_Localised") or entry.get("Species", "")
                    variant = entry.get("Variant_Localised") or entry.get("Variant", "")
                    val = entry.get("Value", 0) + entry.get("Bonus", 0)
                    key = (species, variant)
                    if key not in sold_map:
                        sold_map[key] = {"species": species, "variant": variant,
                                         "total_value": 0, "count": 0}
                    sold_map[key]["total_value"] += val
                    sold_map[key]["count"] += 1

        pending = []
        total_sellable = 0
        total_value = 0

        for info in scans.values():
            # Each complete set = 3 samples of the same species/variant/body
            sellable = info["count"] // 3
            if sellable > 0:
                total_sellable += sellable
                base = predict_organic_value(info["species"], info["variant"])
                val = base * sellable
                total_value += val
                pending.append({**info, "sellable": sellable, "predicted_value": val})

        pending.sort(key=lambda x: -x["predicted_value"])

        return {
            "total_sellable": total_sellable,
            "total_value": total_value,
            "pending": pending,
            "sold_history": sold_map,
        }


# ---------------------------------------------------------------------------
# Value prediction
# Delegates to the species database in spectr/data/species.py
# ---------------------------------------------------------------------------

def predict_organic_value(species: str, variant: str = "") -> int:
    """Return the base CR value for a complete set (3 samples) of *species*.

    Uses the species database for base value. The *variant* parameter is
    accepted for future use but currently not used for value differentiation.
    """
    return data_base_value(species)
