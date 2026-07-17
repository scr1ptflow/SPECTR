"""State Engine for Elite Bridge Core.

Owns the current game state. Subscribes to journal events and maintains
a live snapshot of the commander, ship, location, and all other game state.
The frontend never parses journals — it only requests state from here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from bridge_core.events.bus import Event, EventBus

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State data classes
# ---------------------------------------------------------------------------


@dataclass
class CommanderState:
    name: str = ""
    credits: int = 0
    loan: int = 0
    squadron: str = ""
    powerplay_power: str = ""
    powerplay_rank: int = 0
    powerplay_merits: int = 0


@dataclass
class RankState:
    combat: int = 0
    trade: int = 0
    explore: int = 0
    cqc: int = 0
    empire: int = 0
    federation: int = 0
    soldier: int = 0
    exobiologist: int = 0
    combat_progress: int = 0
    trade_progress: int = 0
    explore_progress: int = 0
    cqc_progress: int = 0
    empire_progress: int = 0
    federation_progress: int = 0
    soldier_progress: int = 0
    exobiologist_progress: int = 0


@dataclass
class ShipState:
    ship_type: str = ""
    ship_name: str = ""
    ship_ident: str = ""
    hull_health: float = 100.0
    fuel_capacity: float = 0.0
    fuel_current: float = 0.0
    cargo_capacity: int = 0
    cargo_count: int = 0
    rebuy: int = 0
    modules: list[dict] = field(default_factory=list)


@dataclass
class LocationState:
    system: str = ""
    system_address: int = 0
    body: str = ""
    body_type: str = ""
    distance_from_star_ls: float = 0.0
    faction: str = ""
    government: str = ""
    economy: str = ""
    security: str = ""
    population: int = 0
    allegiance: str = ""
    station: str = ""
    station_type: str = ""
    market_id: int = 0
    latitude: float | None = None
    longitude: float | None = None
    altitide: float | None = None
    near_body: bool = False
    docked: bool = False


@dataclass
class NavigationState:
    target_system: str = ""
    target_body: str = ""
    route: list[dict] = field(default_factory=list)
    jump_count: int = 0
    total_distance_ly: float = 0.0


@dataclass
class CargoState:
    capacity: int = 0
    count: int = 0
    items: list[dict] = field(default_factory=list)


@dataclass
class MissionState:
    active: list[dict] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    complete: list[dict] = field(default_factory=list)


@dataclass
class EngineeringState:
    current_modification: str = ""
    engineer: str = ""
    grade: float = 0.0
    progress: float = 0.0
    materials: dict[str, int] = field(default_factory=dict)


@dataclass
class BodyInfo:
    """A single scanned body in the current system."""
    name: str = ""
    body_class: str = ""
    star_type: str = ""
    distance_ls: float = 0.0
    radius_km: float = 0.0
    surface_temp_k: float = 0.0
    surface_pressure: float = 0.0
    landable: bool = False
    terraformable: bool = False
    volcanicism: str = ""
    atmosphere: str = ""
    composition: dict = field(default_factory=dict)
    ring_type: str = ""
    reserves: str = ""
    scanned: bool = False
    mapped: bool = False


@dataclass
class SystemBodies:
    """All bodies observed in the current system."""
    bodies: list[BodyInfo] = field(default_factory=list)
    star_count: int = 0
    planet_count: int = 0
    moon_count: int = 0
    landable_count: int = 0
    terraformable_count: int = 0
    water_world_count: int = 0
    earthlike_count: int = 0
    ammonia_count: int = 0
    gas_giant_count: int = 0


@dataclass
class ScanState:
    bodies_scanned: int = 0
    bodies_detailed: int = 0
    organic_scans: list[dict] = field(default_factory=list)
    organic_sold: dict = field(default_factory=dict)
    total_scan_value: int = 0


@dataclass
class FleetState:
    ships: list[dict] = field(default_factory=list)
    active_ship_id: int = 0


@dataclass
class GameState:
    """Complete snapshot of the current game state."""

    commander: CommanderState = field(default_factory=CommanderState)
    ranks: RankState = field(default_factory=RankState)
    ship: ShipState = field(default_factory=ShipState)
    location: LocationState = field(default_factory=LocationState)
    navigation: NavigationState = field(default_factory=NavigationState)
    cargo: CargoState = field(default_factory=CargoState)
    missions: MissionState = field(default_factory=MissionState)
    engineering: EngineeringState = field(default_factory=EngineeringState)
    scans: ScanState = field(default_factory=ScanState)
    system_bodies: SystemBodies = field(default_factory=SystemBodies)
    fleet: FleetState = field(default_factory=FleetState)
    notoriety: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    raw_events: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for API responses."""
        import dataclasses
        result = {}
        for dc_field in dataclasses.fields(self):
            value = getattr(self, dc_field.name)
            if dc_field.name == "timestamp":
                result[dc_field.name] = value.isoformat()
            elif dataclasses.is_dataclass(value) and not isinstance(value, type):
                result[dc_field.name] = dataclasses.asdict(value)
            else:
                result[dc_field.name] = value
        return result


# ---------------------------------------------------------------------------
# State Engine
# ---------------------------------------------------------------------------


class StateEngine:
    """Maintains the live game state by subscribing to journal events.

    Usage:
        bus = EventBus()
        state = StateEngine(bus)
        await bus.run()  # state will update automatically
        snapshot = state.snapshot
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._state = GameState()
        self._lock = __import__("asyncio").Lock()

        # Subscribe to all journal events
        bus.subscribe_all(self._handle_event)

    @property
    def snapshot(self) -> GameState:
        """Return the current state snapshot (thread-safe read)."""
        return self._state

    def snapshot_dict(self) -> dict[str, Any]:
        """Return the current state as a serializable dict."""
        return self._state.to_dict()

    async def _handle_event(self, event: Event) -> None:
        """Route journal events to specific state updaters."""
        if event.source != "journal":
            return

        async with self._lock:
            self._state.timestamp = event.timestamp
            self._state.raw_events += 1

            handler = self._HANDLERS.get(event.topic)
            if handler:
                handler(self, event)

    # -- Event handlers -----------------------------------------------------

    def _on_load_game(self, event: Event) -> None:
        d = event.data
        self._state.commander.name = d.get("Commander", "")
        self._state.commander.credits = d.get("Credits", 0)
        self._state.commander.loan = d.get("Loan", 0)
        self._state.commander.squadron = d.get("SquadronName", "")
        self._state.ship.ship_type = d.get("Ship", "")
        self._state.ship.fuel_capacity = d.get("FuelCapacity", 0.0)
        self._state.ship.cargo_capacity = d.get("CargoCapacity", 0)

    def _on_commander(self, event: Event) -> None:
        self._state.commander.name = event.data.get("Name", "")

    def _on_rank(self, event: Event) -> None:
        d = event.data
        r = self._state.ranks
        r.combat = d.get("Combat", 0)
        r.trade = d.get("Trade", 0)
        r.explore = d.get("Explore", 0)
        r.cqc = d.get("CQC", 0)
        r.empire = d.get("Empire", 0)
        r.federation = d.get("Federation", 0)
        r.soldier = d.get("Soldier", 0)
        r.exobiologist = d.get("Exobiologist", 0)

    def _on_progress(self, event: Event) -> None:
        d = event.data
        r = self._state.ranks
        r.combat_progress = d.get("Combat", 0)
        r.trade_progress = d.get("Trade", 0)
        r.explore_progress = d.get("Explore", 0)
        r.cqc_progress = d.get("CQC", 0)
        r.empire_progress = d.get("Empire", 0)
        r.federation_progress = d.get("Federation", 0)
        r.soldier_progress = d.get("Soldier", 0)
        r.exobiologist_progress = d.get("Exobiologist", 0)

    def _on_loadout(self, event: Event) -> None:
        d = event.data
        s = self._state.ship
        s.ship_type = d.get("Ship", "")
        s.ship_name = d.get("ShipName", "")
        s.ship_ident = d.get("ShipIdent", "")
        s.hull_health = d.get("Health", 100.0)
        s.rebuy = d.get("Rebuy", 0)
        s.modules = d.get("Modules", [])

    def _on_location(self, event: Event) -> None:
        self._apply_location(event.data)

    def _on_fsd_jump(self, event: Event) -> None:
        self._apply_location(event.data)
        self._state.navigation.jump_count += 1
        dist = event.data.get("DistFromStarLs", 0)
        if dist:
            self._state.navigation.total_distance_ly += dist
        # Clear system bodies on entering a new system
        self._state.system_bodies = SystemBodies()

    def _on_carrier_jump(self, event: Event) -> None:
        self._apply_location(event.data)
        self._state.system_bodies = SystemBodies()

    def _apply_location(self, data: dict) -> None:
        loc = self._state.location
        loc.system = data.get("StarSystem", "")
        loc.system_address = data.get("SystemAddress", 0)
        loc.body = data.get("Body", "")
        loc.body_type = data.get("BodyType", "")
        loc.distance_from_star_ls = data.get("DistFromStarLs", 0.0)
        loc.faction = self._clean_faction(data.get("SystemFaction", ""))
        loc.government = data.get("SystemGovernment", "")
        loc.economy = data.get("SystemEconomy", "")
        loc.security = data.get("SystemSecurity", "")
        loc.population = data.get("Population", 0)
        loc.allegiance = data.get("SystemAllegiance", "")
        loc.station = data.get("StationName", "")
        loc.station_type = data.get("StationType", "")
        loc.market_id = data.get("MarketID", 0)
        loc.near_body = data.get("Body") != ""
        loc.docked = data.get("StationName") != ""

    def _clean_faction(self, faction) -> str:
        if isinstance(faction, dict):
            return faction.get("Name", "")
        return faction or ""

    def _on_cargo(self, event: Event) -> None:
        d = event.data
        self._state.cargo.capacity = d.get("Count", 0)
        self._state.cargo.count = d.get("Count", 0)
        self._state.cargo.items = d.get("Inventory", [])

    def _on_mass_carrier_inventory(self, event: Event) -> None:
        pass  # reserved

    def _on_mission_accepted(self, event: Event) -> None:
        self._state.missions.active.append(event.data)

    def _on_mission_completed(self, event: Event) -> None:
        self._state.missions.complete.append(event.data)
        self._state.missions.active = [
            m for m in self._state.missions.active
            if m.get("MissionID") != event.data.get("MissionID")
        ]

    def _on_mission_abandoned(self, event: Event) -> None:
        self._state.missions.failed.append(event.data)
        self._state.missions.active = [
            m for m in self._state.missions.active
            if m.get("MissionID") != event.data.get("MissionID")
        ]

    def _on_mission_failed(self, event: Event) -> None:
        self._state.missions.failed.append(event.data)
        self._state.missions.active = [
            m for m in self._state.missions.active
            if m.get("MissionID") != event.data.get("MissionID")
        ]

    def _on_scan(self, event: Event) -> None:
        self._state.scans.bodies_scanned += 1
        d = event.data

        body = BodyInfo(
            name=d.get("BodyName", ""),
            body_class=d.get("BodyClass", ""),
            star_type=d.get("StarType", ""),
            distance_ls=d.get("DistanceFromArrivalLs", 0.0),
            radius_km=d.get("Radius", 0.0) / 1000.0,
            surface_temp_k=d.get("SurfaceTemperature", 0.0),
            surface_pressure=d.get("SurfacePressure", 0.0),
            landable=d.get("Landable", False),
            terraformable=d.get("TerraformState", "") == "Terraformable",
            volcanicism=d.get("Volcanism", ""),
            atmosphere=d.get("Atmosphere", ""),
            composition=d.get("Composition", {}),
            ring_type=d.get("RingType", ""),
            reserves=d.get("Reserves", ""),
            scanned=True,
        )

        sb = self._state.system_bodies
        # Replace if body already exists, otherwise append
        existing_idx = next(
            (i for i, b in enumerate(sb.bodies) if b.name == body.name), -1
        )
        if existing_idx >= 0:
            sb.bodies[existing_idx] = body
        else:
            sb.bodies.append(body)

        # Update counts
        self._recount_bodies(sb)

    def _recount_bodies(self, sb: SystemBodies) -> None:
        """Recompute body category counts from the bodies list."""
        def _is_star(b: BodyInfo) -> bool:
            return "star" in b.body_class.lower() or bool(b.star_type)

        def _is_planet(b: BodyInfo) -> bool:
            return ("planet" in b.body_class.lower()
                    and "moon" not in b.body_class.lower()
                    and not b.star_type)

        def _is_water(b: BodyInfo) -> bool:
            return ("water" in b.body_class.lower()
                    and "giant" not in b.body_class.lower())

        sb.star_count = sum(1 for b in sb.bodies if _is_star(b))
        sb.planet_count = sum(1 for b in sb.bodies if _is_planet(b))
        sb.moon_count = sum(
            1 for b in sb.bodies if "moon" in b.body_class.lower()
        )
        sb.landable_count = sum(1 for b in sb.bodies if b.landable)
        sb.terraformable_count = sum(
            1 for b in sb.bodies if b.terraformable
        )
        sb.water_world_count = sum(1 for b in sb.bodies if _is_water(b))
        sb.earthlike_count = sum(
            1 for b in sb.bodies if "earthlike" in b.body_class.lower()
        )
        sb.ammonia_count = sum(
            1 for b in sb.bodies if "ammonia" in b.body_class.lower()
        )
        sb.gas_giant_count = sum(
            1 for b in sb.bodies if "gas giant" in b.body_class.lower()
        )

    def _on_scan_organic(self, event: Event) -> None:
        self._state.scans.organic_scans.append(event.data)

    def _on_sell_organic_data(self, event: Event) -> None:
        for entry in event.data.get("BioData", []):
            species = entry.get("Species_Localised") or entry.get("Species", "")
            variant = entry.get("Variant_Localised") or entry.get("Variant", "")
            val = entry.get("Value", 0) + entry.get("Bonus", 0)
            key = f"{species}|{variant}"
            if key not in self._state.scans.organic_sold:
                self._state.scans.organic_sold[key] = {"value": 0, "count": 0}
            self._state.scans.organic_sold[key]["value"] += val
            self._state.scans.organic_sold[key]["count"] += 1

    def _on_notoriety(self, event: Event) -> None:
        self._state.notoriety = event.data.get("Notoriety", 0)

    def _on_powerplay(self, event: Event) -> None:
        d = event.data
        self._state.commander.powerplay_power = d.get("Power", "")
        self._state.commander.powerplay_rank = d.get("Rank", 0)
        self._state.commander.powerplay_merits = d.get("Merits", 0)

    def _on_powerplay_join(self, event: Event) -> None:
        d = event.data
        if not self._state.commander.powerplay_power:
            self._state.commander.powerplay_power = d.get("Power", "")

    def _on_powerplay_merits(self, event: Event) -> None:
        self._state.commander.powerplay_merits = event.data.get("TotalMerits", 0)

    def _on_fuel(self, event: Event) -> None:
        self._state.ship.fuel_current = event.data.get("FuelMain", 0.0)

    def _on_materials(self, event: Event) -> None:
        self._state.engineering.materials = {
            m.get("Name", ""): m.get("Count", 0)
            for m in event.data.get("Materials", [])
        }

    def _on_engineer_craft(self, event: Event) -> None:
        d = event.data
        self._state.engineering.current_modification = d.get("Module", "")
        self._state.engineering.engineer = d.get("Engineer", "")
        self._state.engineering.grade = d.get("Grade", 0)
        self._state.engineering.progress = d.get("Quality", 0)

    def _on_market(self, event: Event) -> None:
        self._state.location.market_id = event.data.get("MarketID", 0)

    def _on_shipyard(self, event: Event) -> None:
        pass  # reserved for fleet state

    def _on_stored_ships(self, event: Event) -> None:
        self._state.fleet.ships = event.data.get("Ships", [])

    def _on_synthesis(self, event: Event) -> None:
        pass  # reserved

    def _on_approach_settlement(self, event: Event) -> None:
        self._state.location.body = event.data.get("Body", "")
        self._state.location.near_body = True

    def _on_touchdown(self, event: Event) -> None:
        self._state.location.latitude = event.data.get("Latitude")
        self._state.location.longitude = event.data.get("Longitude")
        self._state.location.near_body = True

    def _on_liftoff(self, event: Event) -> None:
        self._state.location.latitude = None
        self._state.location.longitude = None

    def _on_approach_body(self, event: Event) -> None:
        self._state.location.body = event.data.get("Body", "")
        self._state.location.near_body = True

    def _on_leave_body(self, event: Event) -> None:
        self._state.location.near_body = False

    def _on_docked(self, event: Event) -> None:
        self._state.location.docked = True
        self._state.location.station = event.data.get("StationName", "")
        self._state.location.station_type = event.data.get("StationType", "")
        self._state.location.market_id = event.data.get("MarketID", 0)

    def _on_undocked(self, event: Event) -> None:
        self._state.location.docked = False

    # -- Handler dispatch table --------------------------------------------

    _HANDLERS: dict[str, callable] = {
        "journal.loadgame": _on_load_game,
        "journal.commander": _on_commander,
        "journal.rank": _on_rank,
        "journal.progress": _on_progress,
        "journal.loadout": _on_loadout,
        "journal.location": _on_location,
        "journal.fsdjump": _on_fsd_jump,
        "journal.carrierjump": _on_carrier_jump,
        "journal.cargo": _on_cargo,
        "journal.missionaccepted": _on_mission_accepted,
        "journal.missioncompleted": _on_mission_completed,
        "journal.missionabandoned": _on_mission_abandoned,
        "journal.missionfailed": _on_mission_failed,
        "journal.scan": _on_scan,
        "journal.scanorganic": _on_scan_organic,
        "journal.sellorganicdata": _on_sell_organic_data,
        "journal.notoriety": _on_notoriety,
        "journal.powerplay": _on_powerplay,
        "journal.powerplayjoin": _on_powerplay_join,
        "journal.powerplaymerits": _on_powerplay_merits,
        "journal.fuel": _on_fuel,
        "journal.materials": _on_materials,
        "journal.engineercraft": _on_engineer_craft,
        "journal.market": _on_market,
        "journal.shipyard": _on_shipyard,
        "journal.storedships": _on_stored_ships,
        "journal.synthesis": _on_synthesis,
        "journal.approachsettlement": _on_approach_settlement,
        "journal.touchdown": _on_touchdown,
        "journal.liftoff": _on_liftoff,
        "journal.approachbody": _on_approach_body,
        "journal.leavebody": _on_leave_body,
        "journal.docked": _on_docked,
        "journal.undocked": _on_undocked,
    }
