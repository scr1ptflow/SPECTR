from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from spectr.data.species import base_value as data_base_value

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


class JournalEvent:
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


class JournalReader:
    def __init__(self, journal_path: str = ""):
        self.journal_path = Path(journal_path).expanduser() if journal_path else None
        self._current_file: Optional[Path] = None

    def set_path(self, path: str) -> None:
        self.journal_path = Path(path).expanduser() if path else None

    def find_journal_files(self) -> list[Path]:
        if not self.journal_path or not self.journal_path.exists():
            return []
        return sorted(
            self.journal_path.glob("Journal.*.log"), reverse=True
        )

    def latest_journal(self) -> Optional[Path]:
        files = self.find_journal_files()
        return files[0] if files else None

    def read_events(self, filepath: Optional[Path] = None) -> Iterator[JournalEvent]:
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
        for path in self.find_journal_files():
            yield from self.read_events(path)

    def get_latest_event(self, event_type: str) -> Optional[JournalEvent]:
        for path in self.find_journal_files():
            result = None
            for event in self.read_events(path):
                if event.event == event_type:
                    result = event
            if result is not None:
                return result
        return None

    def get_all_events(self, event_type: str) -> list[JournalEvent]:
        result: list[JournalEvent] = []
        for path in self.find_journal_files():
            for event in self.read_events(path):
                if event.event == event_type:
                    result.append(event)
        return result

    def get_commander(self) -> Optional[str]:
        event = self.get_latest_event("Commander")
        if event:
            return event.get("Name")
        return None

    def get_current_system(self) -> Optional[str]:
        event = self.get_latest_event("Location")
        if event:
            return event.get("StarSystem")
        event = self.get_latest_event("FSDJump")
        if event:
            return event.get("StarSystem")
        return None

    def get_ship_type(self) -> Optional[str]:
        event = self.get_latest_event("Loadout")
        if event:
            return resolve_ship_type(event.get("Ship", ""))
        event = self.get_latest_event("LoadGame")
        if event:
            return resolve_ship_type(event.get("Ship", ""))
        return None

    def get_ship_name(self) -> Optional[str]:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("ShipName")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("ShipName")
        return None

    def get_ship_ident(self) -> Optional[str]:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("ShipIdent")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("ShipIdent")
        return None

    def get_credits(self) -> Optional[int]:
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("Credits")
        return None

    def get_squadron(self) -> Optional[str]:
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("SquadronName")
        return None

    def get_powerplay(self) -> Optional[dict]:
        event = self.get_latest_event("Powerplay")
        if event:
            return {
                "power": event.get("Power", ""),
                "rank": event.get("Rank", 0),
                "merits": event.get("Merits", 0),
            }
        event = self.get_latest_event("PowerplayMerits")
        if event:
            return {
                "power": "",
                "rank": 0,
                "merits": event.get("TotalMerits", 0),
            }
        return None

    _RANK_CATEGORIES = ["Combat", "Trade", "Explore", "CQC", "Empire", "Federation", "Soldier", "Exobiologist"]

    def get_rank_levels(self) -> dict[str, int]:
        event = self.get_latest_event("Rank")
        if event:
            return {
                cat: event.get(cat, 0)
                for cat in self._RANK_CATEGORIES
            }
        return {}

    def get_rank_progress(self) -> dict[str, int]:
        event = self.get_latest_event("Progress")
        if event:
            return {
                cat: event.get(cat, 0)
                for cat in self._RANK_CATEGORIES
            }
        return {}

    def get_cargo_count(self) -> Optional[int]:
        event = self.get_latest_event("Cargo")
        if event:
            return event.get("Count")
        return None

    _RANK_NAMES: dict[str, list[str]] = {
        "Combat": ["Harmless", "Mostly Harmless", "Novice", "Competent", "Expert", "Master", "Dangerous", "Deadly", "Elite"],
        "Trade": ["Penniless", "Mostly Penniless", "Peddler", "Dealer", "Merchant", "Broker", "Entrepreneur", "Tycoon", "Elite"],
        "Explore": ["Aimless", "Mostly Aimless", "Explorer", "Pathfinder", "Surveyor", "Trailblazer", "Strider", "Pioneer", "Elite"],
        "CQC": ["Helpless", "Mostly Helpless", "Amateur", "Semi-Professional", "Professional", "Champion", "Hero", "Legend", "Elite"],
        "Empire": ["None", "Outsider", "Serf", "Master", "Squire", "Knight", "Lord", "Baron", "Viscount", "Count", "Earl", "Duke", "Prince", "King"],
        "Federation": ["None", "Recruit", "Midshipman", "Petty Officer", "Chief Petty Officer", "Warrant Officer", "Ensign", "Lieutenant", "Lieutenant Commander", "Post Commander", "Post Captain", "Rear Admiral", "Vice Admiral", "Admiral"],
        "Soldier": ["Defenceless", "Unskilled", "Skilled", "Capable", "Proficient", "Competent", "Expert", "Veteran", "Elite"],
        "Exobiologist": ["Directionless", "Mostly Directionless", "Explorer", "Pathfinder", "Surveyor", "Trailblazer", "Strider", "Pioneer", "Elite"],
    }

    def get_rank_name(self, category: str, level: int) -> str:
        names = self._RANK_NAMES.get(category, [])
        if 0 <= level < len(names):
            return names[level]
        return str(level)

    def get_rebuy(self) -> Optional[int]:
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
        sold_map: dict = {}
        for event in self.read_all_events():
            if event.event == "SellOrganicData":
                for entry in event.get("BioData", []):
                    species = entry.get("Species_Localised") or entry.get("Species", "")
                    variant = entry.get("Variant_Localised") or entry.get("Variant", "")
                    val = entry.get("Value", 0) + entry.get("Bonus", 0)
                    key = (species, variant)
                    if key not in sold_map:
                        sold_map[key] = {"species": species, "variant": variant, "total_value": 0, "count": 0}
                    sold_map[key]["total_value"] += val
                    sold_map[key]["count"] += 1
        return sold_map

    def get_organic_summary(self) -> dict:
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
                        sold_map[key] = {"species": species, "variant": variant, "total_value": 0, "count": 0}
                    sold_map[key]["total_value"] += val
                    sold_map[key]["count"] += 1

        pending = []
        total_sellable = 0
        total_value = 0

        for info in scans.values():
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


def predict_organic_value(species: str, variant: str = "") -> int:
    return data_base_value(species)
