"""Archive Service — Officer Report for the Archive department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Archive officer answers:
    "What have we accomplished?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class ArchiveService:
    """Generates the Archive Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Archive Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations: list[Recommendation] = []
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="archive",
            title="Archive Report",
            status=status,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            details=details,
            history=history,
            generated=now,
        )

    def _determine_status(
        self, state: Any, findings: list[Finding]
    ) -> str:
        nav = state.navigation
        if nav.jump_count > 0:
            return "GREEN"
        return "BLUE"

    def _generate_findings(self, state: Any) -> list[Finding]:
        nav = state.navigation
        scans = state.scans
        missions = state.missions
        findings: list[Finding] = []

        if nav.jump_count > 0:
            findings.append(Finding(
                title="Journey Progress",
                description=(
                    f"{nav.jump_count} jump(s) made, "
                    f"covering {nav.total_distance_ly:.1f} LY."
                ),
                severity="GREEN",
            ))

        if scans.bodies_scanned > 0:
            findings.append(Finding(
                title="Exploration Record",
                description=(
                    f"{scans.bodies_scanned} body(s) scanned, "
                    f"{scans.bodies_detailed} detailed."
                ),
                severity="BLUE",
            ))

        if missions.complete:
            findings.append(Finding(
                title="Mission Record",
                description=(
                    f"{len(missions.complete)} mission(s) completed."
                ),
                severity="BLUE",
            ))

        if missions.failed:
            findings.append(Finding(
                title="Failed Missions",
                description=(
                    f"{len(missions.failed)} mission(s) failed."
                ),
                severity="YELLOW",
            ))

        if not findings:
            findings.append(Finding(
                title="No Session Data",
                description="No activity recorded this session.",
                severity="BLUE",
            ))

        return findings

    def _generate_summary(self, state: Any) -> str:
        nav = state.navigation
        parts = []

        if nav.jump_count > 0:
            parts.append(
                f"{nav.jump_count} jumps over "
                f"{nav.total_distance_ly:.1f} LY"
            )

        scans = state.scans
        if scans.bodies_scanned > 0:
            parts.append(f"{scans.bodies_scanned} bodies scanned")

        missions = state.missions
        if missions.complete:
            parts.append(
                f"{len(missions.complete)} missions completed"
            )

        if not parts:
            return "No session activity recorded yet."

        return "Session summary: " + ", ".join(parts) + "."

    def _build_details(self, state: Any) -> dict[str, Any]:
        nav = state.navigation
        scans = state.scans
        missions = state.missions
        return {
            "jumps": nav.jump_count,
            "total_distance_ly": nav.total_distance_ly,
            "bodies_scanned": scans.bodies_scanned,
            "bodies_detailed": scans.bodies_detailed,
            "organic_scans": len(scans.organic_scans),
            "missions_completed": len(missions.complete),
            "missions_failed": len(missions.failed),
            "missions_active": len(missions.active),
        }

    def _build_history(self, state: Any) -> dict[str, Any]:
        return {
            "jumps": state.navigation.jump_count,
            "distance": state.navigation.total_distance_ly,
            "scans": state.scans.bodies_scanned,
            "missions_done": len(state.missions.complete),
        }
