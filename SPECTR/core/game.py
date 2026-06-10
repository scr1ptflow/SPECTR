import os
import json
import logging

logger = logging.getLogger(__name__)


class Game:
    def __init__(self, event_bus, journal_dir):
        self.event_bus = event_bus
        self.journal_dir = journal_dir

        self.commander = ""
        self.system_name = ""
        self.system_address = 0
        self.star_pos = None
        self.body_name = ""
        self.body_type = ""
        self.planet_class = ""
        self.landing_lat = None
        self.landing_lon = None

        self.cargo_carried = []
        self.nav_route = []
        self.body_data_cache = {}
        self._navroute_mtime = 0

    def handle_journal_event(self, event, data):
        handler = getattr(self, f"_on_{event}", None)
        if handler:
            handler(data)
        if "Commander" in data:
            self.commander = data["Commander"]

    def _on_Location(self, data):
        self._update_location(data)

    def _on_FSDJump(self, data):
        self._update_location(data)
        self.body_name = ""
        self.planet_class = ""

    def _update_location(self, data):
        self.system_name = data.get("StarSystem", "")
        self.system_address = data.get("SystemAddress", 0)
        self.star_pos = data.get("StarPos", self.star_pos)

    def _on_SupercruiseExit(self, data):
        self.body_name = data.get("Body", "")
        self.body_type = data.get("BodyType", "")

    def _on_SupercruiseEntry(self, data):
        self.body_name = ""
        self.body_type = ""

    def _on_ApproachBody(self, data):
        self.body_name = data.get("Body", "")

    def _on_LeaveBody(self, data):
        self.body_name = ""

    def _on_Touchdown(self, data):
        self.landing_lat = data.get("Latitude", self.landing_lat)
        self.landing_lon = data.get("Longitude", self.landing_lon)
        if data.get("PlayerControlled", True):
            self.body_name = data.get("BodyName", self.body_name)

    def _on_Liftoff(self, data):
        self.landing_lat = None
        self.landing_lon = None

    def _on_Scan(self, data):
        body_name = data.get("BodyName", "")
        if not body_name:
            return
        raw_materials = data.get("Materials", [])
        if isinstance(raw_materials, list):
            materials = {
                m["Name"].lower(): m["Percent"]
                for m in raw_materials if "Name" in m
            }
        elif isinstance(raw_materials, dict):
            materials = {k.lower(): v for k, v in raw_materials.items()}
        else:
            materials = {}
        self.body_data_cache[body_name] = {
            "planet_class": data.get("PlanetClass", ""),
            "temperature": data.get("SurfaceTemperature"),
            "atmosphere": data.get("AtmosphereType", ""),
            "gravity": data.get("SurfaceGravity"),
            "volcanism": data.get("Volcanism", ""),
            "radius": data.get("Radius"),
            "materials": materials,
            "surface_pressure": data.get("SurfacePressure"),
            "landable": data.get("Landable", False),
            "terraform_state": data.get("TerraformState", ""),
            "atmosphere_composition": data.get("AtmosphereComposition", []),
            "mass_em": data.get("MassEM"),
        }

    def _on_NavRoute(self, data):
        self.nav_route = []
        for entry in data.get("Route", []):
            name = entry.get("StarSystem", "")
            if name:
                self.nav_route.append({
                    "name": name,
                    "address": entry.get("SystemAddress", 0),
                    "star_class": entry.get("StarClass", ""),
                    "pos": entry.get("StarPos", None),
                })
        self.event_bus.publish("navroute_updated", {"route": self.nav_route})

    def _on_NavRouteClear(self, data):
        self.nav_route = []

    def _on_LoadGame(self, data):
        self.commander = data.get("Commander", self.commander)

    def _on_Commander(self, data):
        self.commander = data.get("Name", self.commander)

    def _on_Docked(self, data):
        self.body_name = data.get("StationName", "")
        self.body_type = "Station"

    def _on_Cargo(self, data):
        self.cargo_carried = data.get("Inventory", [])

    def read_navroute(self):
        if not os.path.isdir(self.journal_dir):
            return
        path = os.path.join(self.journal_dir, "NavRoute.json")
        if not os.path.exists(path):
            return
        try:
            mtime = os.path.getmtime(path)
            if mtime <= self._navroute_mtime:
                return
            self._navroute_mtime = mtime
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._on_NavRoute(data)
        except (OSError, json.JSONDecodeError):
            pass

    def body_data(self, body_name):
        return self.body_data_cache.get(body_name)

    def route_next(self):
        if not self.nav_route or not self.system_name:
            return None
        for i, entry in enumerate(self.nav_route):
            if entry["name"] == self.system_name:
                idx = i + 1
                if idx < len(self.nav_route):
                    return self.nav_route[idx]
                return None
        return self.nav_route[0] if len(self.nav_route) > 0 else None

    def route_remaining(self):
        if not self.nav_route or not self.system_name:
            return len(self.nav_route) - 1 if self.nav_route else 0
        for i, entry in enumerate(self.nav_route):
            if entry["name"] == self.system_name:
                return max(0, len(self.nav_route) - i - 1)
        return len(self.nav_route) - 1

    def route_destination(self):
        return self.nav_route[-1] if self.nav_route else None
