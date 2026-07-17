"""Operations Service — Officer Report for the Operations department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Operations officer answers:
    "What are we currently doing?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class OperationsService:
    """Generates the Operations Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Operations Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="operations",
            title="Operations Report",
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
        for f in findings:
            if f.severity == "RED":
                return "RED"
            if f.severity == "ORANGE":
                return "ORANGE"
        for f in findings:
            if f.severity == "YELLOW":
                return "YELLOW"
        if state.missions.active:
            return "GREEN"
        return "BLUE"

    def _generate_findings(self, state: Any) -> list[Finding]:
        missions = state.missions
        cargo = state.cargo
        findings: list[Finding] = []

        active = len(missions.active)
        complete = len(missions.complete)
        failed = len(missions.failed)

        if active > 0:
            findings.append(Finding(
                title="Active Missions",
                description=f"{active} mission(s) currently in progress.",
                severity="GREEN",
            ))

        if complete > 0:
            findings.append(Finding(
                title="Missions Completed",
                description=f"{complete} mission(s) completed this session.",
                severity="BLUE",
            ))

        if failed > 0:
            findings.append(Finding(
                title="Missions Failed",
                description=f"{failed} mission(s) failed this session.",
                severity="YELLOW",
            ))

        if active == 0 and complete == 0:
            findings.append(Finding(
                title="No Active Operations",
                description="No missions currently active or completed.",
                severity="BLUE",
            ))

        if cargo.capacity > 0:
            pct = (cargo.count / cargo.capacity) * 100 if cargo.capacity else 0
            if pct > 90:
                findings.append(Finding(
                    title="Cargo Near Capacity",
                    description=(
                        f"Cargo hold at {cargo.count}/{cargo.capacity} "
                        f"({pct:.0f}%)."
                    ),
                    severity="YELLOW",
                ))
            elif cargo.count > 0:
                findings.append(Finding(
                    title="Cargo Loaded",
                    description=(
                        f"Cargo hold: {cargo.count}/{cargo.capacity}."
                    ),
                    severity="BLUE",
                ))

        return findings

    def _generate_recommendations(
        self, state: any
    ) -> list[Recommendation]:
        missions = state.missions
        recs: list[Recommendation] = []

        for mission in missions.active:
            expiry = mission.get("Expiry")
            if expiry:
                try:
                    exp_dt = datetime.fromisoformat(
                        expiry.replace("Z", "+00:00")
                    )
                    if exp_dt < datetime.now(UTC):
                        recs.append(Recommendation(
                            priority="high",
                            message="Mission has expired",
                            reason=(
                                f"Mission '{mission.get('Type', 'Unknown')}' "
                                "expiry time has passed."
                            ),
                            action="Check mission board for status update.",
                        ))
                        break
                except (ValueError, TypeError):
                    pass

        if state.cargo.capacity > 0:
            pct = (
                (state.cargo.count / state.cargo.capacity) * 100
                if state.cargo.capacity else 0
            )
            if pct > 90:
                recs.append(Recommendation(
                    priority="medium",
                    message="Consider selling or discarding cargo",
                    reason="Cargo hold near capacity",
                    action=(
                        "Visit a station market to free up cargo space "
                        "before accepting new missions"
                    ),
                ))

        return recs

    def _generate_summary(self, state: Any) -> str:
        missions = state.missions
        active = len(missions.active)
        complete = len(missions.complete)
        parts = []

        if active > 0:
            parts.append(f"{active} active mission(s)")
        if complete > 0:
            parts.append(f"{complete} completed")
        if missions.failed:
            parts.append(f"{len(missions.failed)} failed")

        if not parts:
            return "No active operations. Mission board clear."

        return "Current operations: " + ", ".join(parts) + "."

    def _build_details(self, state: Any) -> dict[str, Any]:
        missions = state.missions
        cargo = state.cargo
        return {
            "active": missions.active,
            "complete": missions.complete,
            "failed": missions.failed,
            "active_count": len(missions.active),
            "complete_count": len(missions.complete),
            "failed_count": len(missions.failed),
            "cargo_capacity": cargo.capacity,
            "cargo_count": cargo.count,
            "cargo_items": cargo.items,
        }

    def _build_history(self, state: Any) -> dict[str, Any]:
        return {
            "missions_completed": len(state.missions.complete),
            "missions_failed": len(state.missions.failed),
        }
