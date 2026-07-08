from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional


_SPECIES_BASE_VALUES: dict[str, int] = {
    "Stratum Tectonicas": 19010800,
    "Stratum Paleotis": 19010800,
    "Stratum Laminamus": 19010800,
    "Clypeus Margaritus": 11873200,
    "Clypeus Lacrimam": 8418000,
    "Osseus Discus": 12934900,
    "Osseus Pellebam": 12934900,
    "Osseus Spiralis": 12934900,
    "Cactoida Vermis": 16202800,
    "Cactoida Pullulanta": 16202800,
    "Cactoida Cortex": 16202800,
    "Cactoida Lapis": 16202800,
    "Cactoida Peperatis": 16202800,
    "Tussock Virgam": 14313700,
    "Tussock Serrati": 4447100,
    "Tussock Pennata": 4447100,
    "Tussock Divisa": 1766600,
    "Tussock Culto": 1766600,
    "Tussock Ignis": 1766600,
    "Tussock Albata": 1766600,
    "Tussock Capillum": 1766600,
    "Concha Renibus": 4572400,
    "Concha Labiata": 4572400,
    "Concha Biconcavia": 4572400,
    "Concha Aureola": 4572400,
    "Fungoida Gelata": 3330300,
    "Fungoida Setisis": 1670100,
    "Fungoida Stabitis": 1670100,
    "Fungoida Bullarum": 1670100,
    "Tubus Sororibus": 5727600,
    "Tubus Conifer": 5727600,
    "Tubus Cavas": 5727600,
    "Frutexa Sponsae": 5988000,
    "Frutexa Metallicum": 1632500,
    "Frutexa Flabellum": 1808900,
    "Frutexa Acicularis": 1808900,
    "Frutexa Fera": 1808900,
    "Bacterium Cerbrus": 1689800,
    "Bacterium Alcyoneum": 1658500,
    "Bacterium Informem": 1658500,
    "Bacterium Omentum": 1658500,
    "Bacterium Tela": 1658500,
    "Bacterium Vesicula": 1658500,
    "Bacterium Scopellum": 1658500,
    "Bacterium Aurasius": 1658500,
    "Bacterium Volu": 1658500,
    "Bacterium Nebulas": 1658500,
    "Aleoida Gravis": 8000000,
    "Aleoida Laminiae": 8000000,
    "Aleoida Arcus": 8000000,
    "Aleoida Coronamus": 8000000,
    "Aleoida Spica": 8000000,
    "Electricae Radialem": 1500000,
    "Electricae Pluma": 1500000,
    "Recepta Conditivum": 6000000,
    "Recepta Vertiginis": 6000000,
    "Recepta Aetheris": 6000000,
    "Recepta Deltaerni": 6000000,
    "Recepta Umbrux": 6000000,
}


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
        for event in self.read_events():
            if event.event == event_type:
                return event
        return None

    def get_all_events(self, event_type: str) -> list[JournalEvent]:
        result = []
        for event in self.read_events():
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
            return event.get("Ship")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("Ship")
        return None

    def get_ship_name(self) -> Optional[str]:
        event = self.get_latest_event("Loadout")
        if event:
            return event.get("ShipName")
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("ShipName")
        return None

    def get_credits(self) -> Optional[int]:
        event = self.get_latest_event("LoadGame")
        if event:
            return event.get("Credits")
        return None

    def get_cargo_count(self) -> Optional[int]:
        event = self.get_latest_event("Cargo")
        if event:
            return event.get("Count")
        return None

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
        scans = self.get_organic_scans()
        sold = self.get_organic_sold()

        pending = []
        total_sellable = 0
        total_value = 0

        for key, info in scans.items():
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
            "sold_history": sold,
        }


def predict_organic_value(species: str, variant: str = "") -> int:
    return _SPECIES_BASE_VALUES.get(species, 0)
