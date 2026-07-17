"""Engineering Service — Officer Report for the Engineering department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Engineering officer answers:
    "Can the ship safely continue?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class EngineeringService:
    """Generates the Engineering Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Engineering Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s, findings)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s, status)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="engineering",
            title="Engineering Report",
            status=status,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            details=details,
            history=history,
            generated=now,
        )

    # -- Status determination ------------------------------------------------

    def _determine_status(self, state: Any, findings: list[Finding]) -> str:
        """Determine operational status based on current conditions."""
        ship = state.ship

        # No ship data
        if not ship.ship_type:
            return "RED"

        # Check for danger findings
        for f in findings:
            if f.severity == "RED":
                return "RED"
            if f.severity == "ORANGE":
                return "ORANGE"

        # Check for warnings
        for f in findings:
            if f.severity == "YELLOW":
                return "YELLOW"

        # Ship data available
        if ship.ship_type:
            return "GREEN"

        return "BLUE"

    # -- Findings ------------------------------------------------------------

    def _generate_findings(self, state: Any) -> list[Finding]:
        """Analyze current state and generate findings."""
        ship = state.ship
        eng = state.engineering
        findings: list[Finding] = []

        # No ship data
        if not ship.ship_type:
            findings.append(Finding(
                title="No Ship Data",
                description=(
                    "No ship data available. The engineering "
                    "computer has not received loadout information."
                ),
                severity="RED",
            ))
            return findings

        # Hull integrity
        if ship.hull_health < 50:
            findings.append(Finding(
                title="Hull Critical",
                description=(
                    f"Hull integrity at {ship.hull_health:.0f}%. "
                    "Immediate repairs strongly recommended."
                ),
                severity="RED",
            ))
        elif ship.hull_health < 80:
            findings.append(Finding(
                title="Hull Degraded",
                description=(
                    f"Hull integrity at {ship.hull_health:.0f}%. "
                    "Repairs recommended at next station."
                ),
                severity="YELLOW",
            ))
        elif ship.hull_health >= 100:
            findings.append(Finding(
                title="Hull Integrity Excellent",
                description="Hull is at full integrity. No repairs needed.",
                severity="GREEN",
            ))

        # Fuel status
        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            if fuel_pct < 25:
                findings.append(Finding(
                    title="Low Fuel",
                    description=(
                        f"Fuel reserves at {fuel_pct:.0f}%. "
                        "Locate a fuel star or station soon."
                    ),
                    severity="ORANGE",
                ))
            elif fuel_pct < 50:
                findings.append(Finding(
                    title="Fuel Below Half",
                    description=(
                        f"Fuel at {fuel_pct:.0f}%. "
                        "Consider scooping at the next fuel star."
                    ),
                    severity="YELLOW",
                ))

        # Module count
        module_count = len(ship.modules)
        if module_count > 0:
            findings.append(Finding(
                title="Modules Loaded",
                description=(
                    f"{module_count} module(s) detected in current loadout."
                ),
                severity="BLUE",
            ))

        # Engineering modification active
        if eng.current_modification:
            findings.append(Finding(
                title="Active Modification",
                description=(
                    f"Engineering modification in progress: "
                    f"{eng.current_modification} by {eng.engineer} "
                    f"(Grade {eng.grade})."
                ),
                severity="BLUE",
            ))

        # Materials inventory
        mat_count = sum(eng.materials.values())
        mat_types = len(eng.materials)
        if mat_count > 0:
            findings.append(Finding(
                title="Materials Inventory",
                description=(
                    f"{mat_count} total materials across "
                    f"{mat_types} type(s) in inventory."
                ),
                severity="BLUE",
            ))

        # No findings at all
        if not findings:
            findings.append(Finding(
                title="Ship Nominal",
                description=(
                    f"Operating normally. Hull at "
                    f"{ship.hull_health:.0f}%. No issues detected."
                ),
                severity="GREEN",
            ))

        return findings

    # -- Recommendations -----------------------------------------------------

    def _generate_recommendations(
        self, state: any, findings: list[Finding]
    ) -> list[Recommendation]:
        """Generate actionable recommendations based on findings and state."""
        ship = state.ship
        recs: list[Recommendation] = []

        # Hull recommendations
        if ship.hull_health < 50:
            recs.append(Recommendation(
                priority="critical",
                message="Seek immediate repairs",
                reason="Hull integrity critically low",
                action="Dock at nearest station with repair services",
            ))
        elif ship.hull_health < 80:
            recs.append(Recommendation(
                priority="medium",
                message="Schedule repairs at next station",
                reason="Hull integrity degraded",
                action="Dock at a station and request full repair",
            ))

        # Fuel recommendations
        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            if fuel_pct < 25:
                recs.append(Recommendation(
                    priority="critical",
                    message="Locate a fuel star immediately",
                    reason="Fuel reserves critically low",
                    action=(
                        "Plot route to nearest KGBFOOM star "
                        "or request fuel limpet"
                    ),
                ))
            elif fuel_pct < 50:
                recs.append(Recommendation(
                    priority="medium",
                    message="Consider fuel scooping",
                    reason="Fuel below half capacity",
                    action=(
                        "Route through a scoopable star class "
                        "(K, G, B, F, O, M)"
                    ),
                ))

        # Module recommendations
        if not ship.modules:
            recs.append(Recommendation(
                priority="low",
                message="No modules detected in loadout",
                reason="Module list is empty",
                action="Verify ship loadout via ModuleInfo event",
            ))

        return recs

    # -- Summary -------------------------------------------------------------

    def _generate_summary(self, state: Any, status: str) -> str:
        """Generate a natural language officer briefing."""
        ship = state.ship
        eng = state.engineering

        if not ship.ship_type:
            return (
                "Engineering computer offline. "
                "No ship data available."
            )

        parts = [f"Ship type: {ship.ship_type}."]

        parts.append(f"Hull at {ship.hull_health:.0f}%.")

        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            parts.append(f"Fuel at {fuel_pct:.0f}%.")

        if eng.current_modification:
            parts.append(
                f"Active modification: {eng.current_modification}."
            )

        mat_count = sum(eng.materials.values())
        if mat_count > 0:
            parts.append(f"{mat_count} materials in inventory.")

        return " ".join(parts)

    # -- Details -------------------------------------------------------------

    def _build_details(self, state: Any) -> dict[str, Any]:
        """Build the detailed engineering data."""
        ship = state.ship
        eng = state.engineering

        return {
            "ship_type": ship.ship_type,
            "ship_name": ship.ship_name,
            "ship_ident": ship.ship_ident,
            "hull_health": ship.hull_health,
            "fuel_capacity": ship.fuel_capacity,
            "fuel_current": ship.fuel_current,
            "cargo_capacity": ship.cargo_capacity,
            "cargo_count": ship.cargo_count,
            "rebuy": ship.rebuy,
            "modules": ship.modules,
            "current_modification": eng.current_modification,
            "engineer": eng.engineer,
            "grade": eng.grade,
            "progress": eng.progress,
            "materials": eng.materials,
            "material_count": sum(eng.materials.values()),
            "material_types": len(eng.materials),
        }

    # -- History -------------------------------------------------------------

    def _build_history(self, state: Any) -> dict[str, Any]:
        """Build session history for the Engineering department."""
        eng = state.engineering

        return {
            "modifications_applied": (
                1 if eng.current_modification else 0
            ),
            "material_count": sum(eng.materials.values()),
            "material_types": len(eng.materials),
        }
