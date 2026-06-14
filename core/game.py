import os
import json
import logging

logger = logging.getLogger(__name__)


class Game:
    _MAX_BODY_CACHE = 500

    def __init__(self, event_bus, journal_dir):
        self.event_bus = event_bus
        self.journal_dir = journal_dir

        self.system_name = ""
        self.system_address = 0
        self.star_pos = None
        self.body_name = ""

        self.nav_route = []
        self.body_data_cache = {}

    def handle_journal_event(self, event, data):
        handler = getattr(self, f"_on_{event}", None)
        if handler:
            handler(data)

    def _on_Location(self, data):
        self._update_location(data)

    def _on_FSDJump(self, data):
        self._update_location(data)
        self.body_name = ""

    def _update_location(self, data):
        self.system_name = data.get("StarSystem", "")
        self.system_address = data.get("SystemAddress", 0)
        self.star_pos = data.get("StarPos", self.star_pos)

    def _on_SupercruiseExit(self, data):
        self.body_name = data.get("Body", "")

    def _on_SupercruiseEntry(self, data):
        self.body_name = ""

    def _on_ApproachBody(self, data):
        self.body_name = data.get("Body", "")

    def _on_LeaveBody(self, data):
        self.body_name = ""

    def _on_Touchdown(self, data):
        if data.get("PlayerControlled", True):
            self.body_name = data.get("BodyName", self.body_name)

    def _on_Scan(self, data):
        body_name = data.get("BodyName", "")
        if not body_name:
            return
        raw_materials = data.get("Materials", [])
        if isinstance(raw_materials, list):
            materials = {
                m["Name"].lower(): m["Percent"]
                for m in raw_materials if "Name" in m and "Percent" in m
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
        if len(self.body_data_cache) > self._MAX_BODY_CACHE:
            oldest = next(iter(self.body_data_cache))
            del self.body_data_cache[oldest]

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

    def _on_Docked(self, data):
        self.body_name = data.get("StationName", "")
