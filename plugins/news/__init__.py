"""Example plugin: News Service.

Subscribes to journal events and generates news-style alerts.
Demonstrates how plugins extend the core without modifying it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from bridge_core.events.bus import Event
from bridge_core.plugins.base import BasePlugin

if TYPE_CHECKING:
    from bridge_core.events.bus import EventBus
    from bridge_core.state.engine import StateEngine
    from bridge_core.database.db import Database

log = logging.getLogger(__name__)


@dataclass
class NewsItem:
    headline: str
    summary: str
    category: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class NewsPlugin(BasePlugin):
    """Generates news items from journal events."""

    name = "news"
    version = "0.1.0"
    description = "Generates news items from journal events."

    def __init__(self) -> None:
        super().__init__()
        self._news: list[NewsItem] = []

    async def setup(
        self,
        bus: EventBus,
        state: StateEngine,
        db: Database | None = None,
    ) -> None:
        bus.subscribe("journal.fsdjump", self._on_fsd_jump)
        bus.subscribe("journal.docked", self._on_docked)
        bus.subscribe("journal.missioncompleted", self._on_mission_complete)
        bus.subscribe("journal.scanorganic", self._on_organic_scan)
        self.log_info("News plugin active.")

    async def teardown(self) -> None:
        self._news.clear()
        self.log_info("News plugin stopped.")

    @property
    def recent_news(self) -> list[dict]:
        return [
            {
                "headline": n.headline,
                "summary": n.summary,
                "category": n.category,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in self._news[-20:]
        ]

    def _add_news(self, headline: str, summary: str, category: str) -> None:
        item = NewsItem(headline=headline, summary=summary, category=category)
        self._news.append(item)
        if len(self._news) > 100:
            self._news = self._news[-100:]

    async def _on_fsd_jump(self, event: Event) -> None:
        system = event.data.get("StarSystem", "Unknown")
        self._add_news(
            headline=f"Arrived in {system}",
            summary=f"Frame shift drive jump completed to {system}.",
            category="navigation",
        )

    async def _on_docked(self, event: Event) -> None:
        station = event.data.get("StationName", "Unknown")
        self._add_news(
            headline=f"Docked at {station}",
            summary=f"Successfully docked at {station}.",
            category="navigation",
        )

    async def _on_mission_complete(self, event: Event) -> None:
        mission_type = event.data.get("Type", "Unknown")
        self._add_news(
            headline=f"Mission Completed: {mission_type}",
            summary=f"A {mission_type.lower()} mission has been completed.",
            category="missions",
        )

    async def _on_organic_scan(self, event: Event) -> None:
        species = event.data.get("Species_Localised") or event.data.get("Species", "Unknown")
        body = event.data.get("Body", "Unknown")
        self._add_news(
            headline=f"Organic Scan: {species}",
            summary=f"Scanned {species} on {body}.",
            category="exobiology",
        )


plugin_class = NewsPlugin
