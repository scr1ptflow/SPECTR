"""Plugin base class for Elite Bridge Core.

Every plugin inherits from BasePlugin and may:
- subscribe to events on the bus
- expose API endpoints
- create alerts
- register calculations

Plugins never modify the core. They extend it.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bridge_core.database.db import Database
    from bridge_core.events.bus import EventBus
    from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all Elite Bridge plugins.

    Subclass this and implement setup() and teardown().
    """

    name: str = "unnamed"
    version: str = "0.1.0"
    description: str = ""

    def __init__(self) -> None:
        self.bus: EventBus | None = None
        self.state: StateEngine | None = None
        self.db: Database | None = None
        self._logger = logging.getLogger(f"plugin.{self.name}")

    @abstractmethod
    async def setup(
        self,
        bus: EventBus,
        state: StateEngine,
        db: Database | None = None,
    ) -> None:
        """Initialize the plugin. Called once at startup.

        Subscribe to events, register API routes, etc.
        """

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up the plugin. Called before shutdown."""

    def log_info(self, msg: str) -> None:
        self._logger.info(msg)

    def log_warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def log_error(self, msg: str) -> None:
        self._logger.error(msg)
