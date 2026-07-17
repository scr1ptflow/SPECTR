"""Statistics Service — session and career statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


@dataclass
class StatisticsReport:
    jumps_this_session: int
    total_distance_ly: float
    bodies_scanned: int
    missions_completed: int
    missions_failed: int
    organic_scans: int
    credits: int
    notoriety: int


class StatisticsService:
    """Provides session statistics."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> StatisticsReport:
        s = self.state.snapshot
        return StatisticsReport(
            jumps_this_session=s.navigation.jump_count,
            total_distance_ly=s.navigation.total_distance_ly,
            bodies_scanned=s.scans.bodies_scanned,
            missions_completed=len(s.missions.complete),
            missions_failed=len(s.missions.failed),
            organic_scans=len(s.scans.organic_scans),
            credits=s.commander.credits,
            notoriety=s.notoriety,
        )
