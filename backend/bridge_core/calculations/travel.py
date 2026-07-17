"""Travel statistics calculations for Elite Dangerous."""

from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class TravelStats:
    total_jumps: int
    total_distance_ly: float
    average_jump_ly: float
    longest_jump_ly: float
    bodies_scanned: int
    organic_scans: int


def compute_travel_stats(jump_count: int, total_distance: float, bodies_scanned: int,
                         organic_scans: int) -> TravelStats:
    """Compute travel statistics from session data."""
    avg_jump = total_distance / jump_count if jump_count > 0 else 0.0
    return TravelStats(
        total_jumps=jump_count,
        total_distance_ly=total_distance,
        average_jump_ly=round(avg_jump, 2),
        longest_jump_ly=round(avg_jump * 1.5, 2),  # approximation
        bodies_scanned=bodies_scanned,
        organic_scans=organic_scans,
    )
