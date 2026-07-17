"""Mission Service — business logic for mission state."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


@dataclass
class MissionReport:
    active_count: int
    complete_count: int
    failed_count: int
    active: list[dict]
    complete: list[dict]
    failed: list[dict]


class MissionService:
    """Provides business logic for mission queries."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> MissionReport:
        s = self.state.snapshot
        return MissionReport(
            active_count=len(s.missions.active),
            complete_count=len(s.missions.complete),
            failed_count=len(s.missions.failed),
            active=s.missions.active,
            complete=s.missions.complete,
            failed=s.missions.failed,
        )
