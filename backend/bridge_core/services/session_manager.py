"""Session Manager for Elite Bridge Core.

Tracks complete play sessions by subscribing to journal events.
Records start/end times, credits, distance, systems, bodies, missions,
and organic scans to the database.

Each session becomes searchable history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from bridge_core.events.bus import Event, EventBus

if TYPE_CHECKING:
    from bridge_core.database.db import Database

log = logging.getLogger(__name__)


@dataclass
class SessionSnapshot:
    """A snapshot of the current session's accumulated stats."""

    session_id: int = 0
    active: bool = False
    started_at: str = ""
    duration_seconds: int = 0
    commander: str = ""
    ship: str = ""
    starting_system: str = ""
    credits_start: int = 0
    credits_current: int = 0
    jumps: int = 0
    distance_ly: float = 0.0
    systems_visited: set[str] = field(default_factory=set)
    bodies_scanned: int = 0
    organic_scans: int = 0
    missions_completed: int = 0
    missions_failed: int = 0
    events_count: int = 0

    @property
    def credits_earned(self) -> int:
        return self.credits_current - self.credits_start

    @property
    def unique_systems(self) -> int:
        return len(self.systems_visited)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "active": self.active,
            "started_at": self.started_at,
            "duration_seconds": self.duration_seconds,
            "commander": self.commander,
            "ship": self.ship,
            "starting_system": self.starting_system,
            "credits_start": self.credits_start,
            "credits_current": self.credits_current,
            "credits_earned": self.credits_earned,
            "jumps": self.jumps,
            "distance_ly": round(self.distance_ly, 2),
            "systems_visited": self.unique_systems,
            "bodies_scanned": self.bodies_scanned,
            "organic_scans": self.organic_scans,
            "missions_completed": self.missions_completed,
            "missions_failed": self.missions_failed,
            "events_count": self.events_count,
        }


class SessionManager:
    """Manages play session tracking.

    Subscribes to journal events and records session data to the database.
    Automatically starts a new session when the game is detected running.
    """

    def __init__(self, bus: EventBus, db: Database | None = None) -> None:
        self.bus = bus
        self.db = db
        self._session = SessionSnapshot()
        self._started = False

        bus.subscribe("journal.loadgame", self._on_load_game)
        bus.subscribe("journal.fsdjump", self._on_fsd_jump)
        bus.subscribe("journal.location", self._on_location)
        bus.subscribe("journal.carrierjump", self._on_carrier_jump)
        bus.subscribe("journal.scan", self._on_scan)
        bus.subscribe("journal.scanorganic", self._on_organic_scan)
        bus.subscribe("journal.missioncompleted", self._on_mission_complete)
        bus.subscribe("journal.missionabandoned", self._on_mission_failed)
        bus.subscribe("journal.missionfailed", self._on_mission_failed)

    @property
    def session(self) -> SessionSnapshot:
        return self._session

    @property
    def is_active(self) -> bool:
        return self._session.active

    def snapshot_dict(self) -> dict:
        """Return the current session as a serializable dict."""
        import time

        data = self._session.to_dict()
        if self._session.active and self._started:
            data["duration_seconds"] = int(time.time() - self._started)
        return data

    async def _on_load_game(self, event: Event) -> None:
        """Start a new session when LoadGame fires."""
        d = event.data
        commander = d.get("Commander", "")
        ship = d.get("Ship", "")
        credits = d.get("Credits", 0)

        # End previous session if active
        if self._session.active:
            await self._end_session()

        # Start new session
        self._session = SessionSnapshot(
            active=True,
            started_at=event.timestamp.isoformat(),
            commander=commander,
            ship=ship,
            credits_start=credits,
            credits_current=credits,
        )

        if self.db:
            session_id = await self.db.create_session(
                commander, ship, "", credits
            )
            self._session.session_id = session_id

        import time
        self._started = time.time()

        log.info(
            "Session started: %s in %s with %d CR",
            commander, ship, credits,
        )

    async def _on_location(self, event: Event) -> None:
        d = event.data
        system = d.get("StarSystem", "")
        if system:
            self._session.starting_system = system
            self._session.systems_visited.add(system)

            if self.db and self._session.session_id:
                await self.db.add_visited_system(
                    self._session.session_id, system,
                    d.get("SystemAddress", 0),
                    faction=d.get("SystemFaction", "")
                    if isinstance(d.get("SystemFaction"), str)
                    else d.get("SystemFaction", {}).get("Name", "")
                    if isinstance(d.get("SystemFaction"), dict)
                    else "",
                    government=d.get("SystemGovernment", ""),
                    economy=d.get("SystemEconomy", ""),
                    security=d.get("SystemSecurity", ""),
                    population=d.get("Population", 0),
                )

    async def _on_fsd_jump(self, event: Event) -> None:
        d = event.data
        self._session.jumps += 1
        dist = d.get("DistFromStarLs", 0)
        self._session.distance_ly += dist

        system = d.get("StarSystem", "")
        if system:
            self._session.systems_visited.add(system)

            if self.db and self._session.session_id:
                await self.db.add_visited_system(
                    self._session.session_id, system,
                    d.get("SystemAddress", 0),
                )

    async def _on_carrier_jump(self, event: Event) -> None:
        d = event.data
        system = d.get("StarSystem", "")
        if system:
            self._session.systems_visited.add(system)

    async def _on_scan(self, event: Event) -> None:
        self._session.bodies_scanned += 1

        if self.db and self._session.session_id:
            await self.db.add_exploration_entry(
                self._session.session_id,
                event.data.get("StarSystem", ""),
                event.data.get("BodyName", ""),
                event.data.get("ScanType", ""),
                0,
            )

    async def _on_organic_scan(self, event: Event) -> None:
        self._session.organic_scans += 1

        if self.db and self._session.session_id:
            d = event.data
            await self.db.add_organic_entry(
                self._session.session_id,
                d.get("System", "") or d.get("StarSystem", ""),
                d.get("Body", ""),
                d.get("Species_Localised", "") or d.get("Species", ""),
                d.get("Variant_Localised", "") or d.get("Variant", ""),
                d.get("Genus_Localised", "") or d.get("Genus", ""),
                d.get("ScanType", "Sample"),
            )

    async def _on_mission_complete(self, event: Event) -> None:
        self._session.missions_completed += 1

    async def _on_mission_failed(self, event: Event) -> None:
        self._session.missions_failed += 1

    async def _end_session(self) -> None:
        """End the current session and persist final stats."""
        if not self._session.active:
            return

        import time
        duration = int(time.time() - self._started) if self._started else 0

        if self.db and self._session.session_id:
            await self.db.end_session(
                self._session.session_id,
                credits_end=self._session.credits_current,
                jumps=self._session.jumps,
                distance_ly=round(self._session.distance_ly, 2),
                bodies_scanned=self._session.bodies_scanned,
                organic_scans=self._session.organic_scans,
                missions_completed=self._session.missions_completed,
                missions_failed=self._session.missions_failed,
                events_count=self._session.events_count,
            )

        log.info(
            "Session ended: %d seconds, %d jumps, %d CR earned",
            duration, self._session.jumps, self._session.credits_earned,
        )

        self._session.active = False
