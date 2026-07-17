"""Navigation Service — Officer Report for the Navigation department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Navigation officer answers:
    "Where are we, and what is worth doing here?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class NavigationService:
    """Generates the Navigation Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Navigation Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s, findings)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s, status)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="navigation",
            title="Navigation Report",
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
        """Determine operational status based on current conditions.

        Returns one of: GREEN, BLUE, YELLOW, ORANGE, RED.
        """
        loc = state.location

        # No system data at all
        if not loc.system:
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

        # System data available
        if loc.system:
            return "GREEN"

        return "BLUE"

    # -- Findings ------------------------------------------------------------

    def _generate_findings(self, state: Any) -> list[Finding]:
        """Analyze current state and generate findings."""
        loc = state.location
        ship = state.ship
        findings: list[Finding] = []

        # No system data
        if not loc.system:
            findings.append(Finding(
                title="No Navigation Data",
                description=(
                    "No star system data available. "
                    "The navigation computer has not received location information."
                ),
                severity="RED",
            ))
            return findings

        # Security assessment
        security = loc.security.lower() if loc.security else ""
        if "anarchy" in security:
            findings.append(Finding(
                title="Anarchy System",
                description=(
                    f"Current system ({loc.system}) operates under "
                    "anarchy jurisdiction. No legal protections apply."
                ),
                severity="ORANGE",
            ))
        elif "lawless" in security:
            findings.append(Finding(
                title="Lawless System",
                description=(
                    f"Current system ({loc.system}) has no "
                    "enforced law. Exercise caution."
                ),
                severity="YELLOW",
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
                title="Hull Damage Detected",
                description=(
                    f"Hull integrity at {ship.hull_health:.0f}%. "
                    "Repairs recommended at next station."
                ),
                severity="YELLOW",
            ))

        # Population and economy context
        if loc.population > 1000000000:
            findings.append(Finding(
                title="High Population System",
                description=(
                    f"{loc.system} has a population of "
                    f"{loc.population:,}. Expect significant "
                    "traffic and services."
                ),
                severity="BLUE",
            ))
        elif loc.population == 0 and loc.system:
            findings.append(Finding(
                title="Unpopulated System",
                description=(
                    f"{loc.system} has no recorded population. "
                    "Likely an uninhabited system."
                ),
                severity="BLUE",
            ))

        # Exploration value
        if state.scans.bodies_scanned > 0:
            findings.append(Finding(
                title="Bodies Scanned",
                description=(
                    f"{state.scans.bodies_scanned} body(s) "
                    "scanned this session."
                ),
                severity="BLUE",
            ))

        # Docked status
        if loc.docked and loc.station:
            stype = loc.station_type or "unknown type"
            findings.append(Finding(
                title="Docked at Station",
                description=(
                    f"Currently docked at {loc.station} ({stype})."
                ),
                severity="GREEN",
            ))

        # No findings at all — system is nominal
        if not findings:
            findings.append(Finding(
                title="System Nominal",
                description=(
                    f"Operating normally in {loc.system}. "
                    "No issues detected."
                ),
                severity="GREEN",
            ))

        return findings

    # -- Recommendations -----------------------------------------------------

    def _generate_recommendations(
        self, state: any, findings: list[Finding]
    ) -> list[Recommendation]:
        """Generate actionable recommendations based on findings and state."""
        loc = state.location
        ship = state.ship
        recs: list[Recommendation] = []

        # Fuel recommendation
        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            if fuel_pct < 25:
                recs.append(Recommendation(
                    priority="critical",
                    message="Locate a fuel star immediately",
                    reason="Fuel reserves critically low",
                    action="Plot route to nearest KGBFOOM star or request fuel limpet",
                ))
            elif fuel_pct < 50:
                recs.append(Recommendation(
                    priority="medium",
                    message="Consider fuel scooping",
                    reason="Fuel below half capacity",
                    action="Route through a scoopable star class (K, G, B, F, O, M)",
                ))

        # Hull recommendation
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

        # Security recommendation
        security = loc.security.lower() if loc.security else ""
        if "anarchy" in security or "lawless" in security:
            recs.append(Recommendation(
                priority="high",
                message="Exercise heightened caution",
                reason=f"System security: {loc.security}",
                action="Avoid unnecessary engagements. Be prepared for hostile contacts.",
            ))

        # Exploration recommendation
        if state.scans.bodies_scanned == 0 and loc.system:
            recs.append(Recommendation(
                priority="low",
                message="Consider performing a Full Spectrum Scan",
                reason="No bodies scanned in current system",
                action="Use the FSS to discover and catalog system bodies",
            ))

        return recs

    # -- Summary -------------------------------------------------------------

    def _generate_summary(self, state: Any, status: str) -> str:
        """Generate a natural language officer briefing."""
        loc = state.location
        ship = state.ship

        if not loc.system:
            return "Navigation computer offline. No location data available."

        parts = [f"Currently in {loc.system}."]

        if loc.body:
            parts.append(f"Orbiting {loc.body}.")

        if loc.station and loc.docked:
            parts.append(f"Docked at {loc.station}.")
        elif loc.station:
            parts.append(f"Nearest station: {loc.station}.")

        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            parts.append(f"Fuel at {fuel_pct:.0f}%.")

        if ship.hull_health < 100:
            parts.append(f"Hull at {ship.hull_health:.0f}%.")

        return " ".join(parts)

    # -- Details -------------------------------------------------------------

    def _build_details(self, state: Any) -> dict[str, Any]:
        """Build the detailed location and navigation data."""
        loc = state.location
        nav = state.navigation

        return {
            "system": loc.system,
            "system_address": loc.system_address,
            "body": loc.body,
            "body_type": loc.body_type,
            "distance_from_star_ls": loc.distance_from_star_ls,
            "faction": loc.faction,
            "government": loc.government,
            "economy": loc.economy,
            "security": loc.security,
            "population": loc.population,
            "allegiance": loc.allegiance,
            "station": loc.station,
            "station_type": loc.station_type,
            "docked": loc.docked,
            "near_body": loc.near_body,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "jump_count": nav.jump_count,
            "total_distance_ly": nav.total_distance_ly,
            "target_system": nav.target_system,
            "target_body": nav.target_body,
            "route": nav.route,
        }

    # -- History -------------------------------------------------------------

    def _build_history(self, state: Any) -> dict[str, Any]:
        """Build session history for the Navigation department."""
        nav = state.navigation
        scans = state.scans

        return {
            "jumps": nav.jump_count,
            "total_distance_ly": nav.total_distance_ly,
            "bodies_scanned": scans.bodies_scanned,
            "bodies_detailed": scans.bodies_detailed,
            "organic_scans": len(scans.organic_scans),
        }
