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

from bridge_core.calculations.exploration import predict_scan_value
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

        if not loc.system:
            return "RED"

        for f in findings:
            if f.severity == "RED":
                return "RED"
            if f.severity == "ORANGE":
                return "ORANGE"

        for f in findings:
            if f.severity == "YELLOW":
                return "YELLOW"

        if loc.system:
            return "GREEN"

        return "BLUE"

    # -- Findings ------------------------------------------------------------

    def _generate_findings(self, state: Any) -> list[Finding]:
        """Analyze current state and generate findings."""
        loc = state.location
        ship = state.ship
        nav = state.navigation
        sb = state.system_bodies
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

        # Notoriety
        if state.notoriety > 0:
            findings.append(Finding(
                title="Notoriety Detected",
                description=(
                    f"Notoriety level {state.notoriety}/10. "
                    "System authority will be hostile."
                ),
                severity="ORANGE" if state.notoriety >= 5 else "YELLOW",
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
        if loc.population > 1_000_000_000:
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

        # Body discovery
        total_bodies = len(sb.bodies)
        if total_bodies > 0:
            high_value = (
                sb.earthlike_count + sb.water_world_count
                + sb.ammonia_count + sb.terraformable_count
            )
            if high_value > 0:
                names = []
                if sb.earthlike_count:
                    names.append(f"{sb.earthlike_count} Earth-like")
                if sb.water_world_count:
                    names.append(f"{sb.water_world_count} Water World(s)")
                if sb.ammonia_count:
                    names.append(f"{sb.ammonia_count} Ammonia")
                if sb.terraformable_count:
                    names.append(f"{sb.terraformable_count} terraformable")
                findings.append(Finding(
                    title="High-Value Bodies Detected",
                    description=(
                        f"{total_bodies} bodies cataloged. "
                        f"Notable: {', '.join(names)}."
                    ),
                    severity="GREEN",
                ))
            elif total_bodies > 5:
                findings.append(Finding(
                    title="Rich System",
                    description=(
                        f"{total_bodies} bodies detected in {loc.system}."
                    ),
                    severity="BLUE",
                ))

        # Scanning progress
        if total_bodies > 0:
            scanned = sum(1 for b in sb.bodies if b.scanned)
            if scanned < total_bodies:
                remaining = total_bodies - scanned
                findings.append(Finding(
                    title="Bodies Remaining",
                    description=(
                        f"{remaining} of {total_bodies} bodies not yet scanned."
                    ),
                    severity="BLUE",
                ))

        # Session exploration summary
        if state.scans.bodies_scanned > 0:
            findings.append(Finding(
                title="Session Exploration",
                description=(
                    f"{state.scans.bodies_scanned} body(s) scanned "
                    "this session. "
                    f"Estimated value: {state.scans.total_scan_value:,} CR."
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

        # Route information
        if nav.target_system:
            findings.append(Finding(
                title="Route Plotted",
                description=(
                    f"Target: {nav.target_system}. "
                    f"{nav.jump_count} jump(s) completed this session."
                ),
                severity="BLUE",
            ))

        # No findings at all
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
        self, state: Any, findings: list[Finding]
    ) -> list[Recommendation]:
        """Generate actionable recommendations based on findings and state."""
        loc = state.location
        ship = state.ship
        sb = state.system_bodies
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

        # Exploration recommendations
        total_bodies = len(sb.bodies)
        if total_bodies > 0:
            scanned = sum(1 for b in sb.bodies if b.scanned)
            unmapped_high_value = sum(
                1 for b in sb.bodies
                if not b.mapped and b.scanned and (
                    "earthlike" in b.body_class.lower()
                    or ("water" in b.body_class.lower()
                        and "giant" not in b.body_class.lower())
                    or "ammonia" in b.body_class.lower()
                    or b.terraformable
                )
            )
            if unmapped_high_value > 0:
                recs.append(Recommendation(
                    priority="high",
                    message=f"Map {unmapped_high_value} high-value body(s)",
                    reason="Unmapped high-value bodies detected",
                    action=(
                        "Use Detailed Surface Scanner on "
                        "Earth-like, Water, Ammonia, or terraformable worlds"
                    ),
                ))
            if scanned < total_bodies:
                recs.append(Recommendation(
                    priority="medium",
                    message=f"Scan remaining {total_bodies - scanned} body(s)",
                    reason="Unexplored bodies remain in this system",
                    action="Use Full Spectrum Scanner to complete system survey",
                ))
        elif loc.system and state.scans.bodies_scanned == 0:
            recs.append(Recommendation(
                priority="low",
                message="Perform a Full Spectrum Scan",
                reason="No bodies scanned in current system",
                action="Use the FSS to discover and catalog system bodies",
            ))

        # Cartographic value recommendation
        estimated = self._estimate_system_value(state)
        if estimated > 1_000_000:
            recs.append(Recommendation(
                priority="medium",
                message=f"System estimated at {estimated:,} CR",
                reason="Significant cartographic value detected",
                action="Complete all scans and sell data at the next station",
            ))

        return recs

    # -- Summary -------------------------------------------------------------

    def _generate_summary(self, state: Any, status: str) -> str:
        """Generate a natural language officer briefing."""
        loc = state.location
        ship = state.ship
        nav = state.navigation
        sb = state.system_bodies

        if not loc.system:
            return "Navigation computer offline. No location data available."

        parts = [f"Currently in {loc.system}."]

        if loc.body:
            parts.append(f"Orbiting {loc.body}.")

        if loc.station and loc.docked:
            parts.append(f"Docked at {loc.station}.")
        elif loc.station:
            parts.append(f"Nearest station: {loc.station}.")

        # System context
        if loc.security:
            parts.append(f"Security: {loc.security}.")
        if loc.economy:
            parts.append(f"Economy: {loc.economy}.")

        # Body summary
        total = len(sb.bodies)
        if total > 0:
            scanned = sum(1 for b in sb.bodies if b.scanned)
            parts.append(f"{total} bodies detected, {scanned} scanned.")

        # Fuel and hull
        if ship.fuel_capacity > 0:
            fuel_pct = (ship.fuel_current / ship.fuel_capacity) * 100
            parts.append(f"Fuel at {fuel_pct:.0f}%.")

        if ship.hull_health < 100:
            parts.append(f"Hull at {ship.hull_health:.0f}%.")

        # Route
        if nav.target_system:
            parts.append(f"Route plotted to {nav.target_system}.")

        # Cartographic estimate
        estimated = self._estimate_system_value(state)
        if estimated > 0:
            parts.append(f"Estimated cartographic value: {estimated:,} CR.")

        return " ".join(parts)

    # -- Details -------------------------------------------------------------

    def _build_details(self, state: Any) -> dict[str, Any]:
        """Build the detailed location, system, and navigation data."""
        loc = state.location
        nav = state.navigation
        sb = state.system_bodies

        # Build body list for the frontend
        bodies = []
        for b in sb.bodies:
            bodies.append({
                "name": b.name,
                "body_class": b.body_class,
                "star_type": b.star_type,
                "distance_ls": b.distance_ls,
                "landable": b.landable,
                "terraformable": b.terraformable,
                "atmosphere": b.atmosphere,
                "volcanicism": b.volcanicism,
                "surface_temp_k": b.surface_temp_k,
                "scanned": b.scanned,
                "mapped": b.mapped,
            })

        # Sort bodies: stars first, then by distance
        bodies.sort(key=lambda x: (0 if x["star_type"] else 1, x["distance_ls"]))

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
            "bodies": bodies,
            "body_counts": {
                "total": len(sb.bodies),
                "stars": sb.star_count,
                "planets": sb.planet_count,
                "moons": sb.moon_count,
                "landable": sb.landable_count,
                "terraformable": sb.terraformable_count,
                "water_worlds": sb.water_world_count,
                "earth_like": sb.earthlike_count,
                "ammonia": sb.ammonia_count,
                "gas_giants": sb.gas_giant_count,
            },
            "cartographic_estimate": self._estimate_system_value(state),
            "threat_assessment": self._assess_threat(state),
        }

    # -- History -------------------------------------------------------------

    def _build_history(self, state: Any) -> dict[str, Any]:
        """Build session history for the Navigation department."""
        nav = state.navigation
        scans = state.scans
        sb = state.system_bodies

        return {
            "jumps": nav.jump_count,
            "total_distance_ly": nav.total_distance_ly,
            "bodies_scanned": scans.bodies_scanned,
            "bodies_detailed": scans.bodies_detailed,
            "organic_scans": len(scans.organic_scans),
            "system_bodies": len(sb.bodies),
            "route": nav.route,
        }

    # -- Helpers -------------------------------------------------------------

    def _estimate_system_value(self, state: Any) -> int:
        """Estimate the total cartographic value of the current system.

        Sums predicted scan values for all known bodies that haven't
        been scanned yet, plus a rough estimate for undiscovered bodies
        based on the system body count.
        """
        sb = state.system_bodies
        total = 0

        for body in sb.bodies:
            if not body.scanned:
                total += predict_scan_value(
                    body.body_class, body.distance_ls, is_mapped=False
                )
            elif not body.mapped:
                total += predict_scan_value(
                    body.body_class, body.distance_ls, is_mapped=True
                )

        return total

    def _assess_threat(self, state: Any) -> dict[str, Any]:
        """Assess the threat level of the current location."""
        loc = state.location
        security = (loc.security or "").lower()
        notoriety = state.notoriety

        level = "LOW"
        factors: list[str] = []

        if "anarchy" in security:
            level = "HIGH"
            factors.append("Anarchy jurisdiction")
        elif "lawless" in security:
            level = "MEDIUM"
            factors.append("Lawless system")
        elif "low" in security:
            level = "LOW"
        elif "medium" in security:
            level = "LOW"
        elif "high" in security:
            level = "LOW"
            factors.append("High security — authority present")

        if notoriety >= 5:
            level = "HIGH"
            factors.append(f"Notoriety {notoriety}/10")
        elif notoriety > 0:
            if level == "LOW":
                level = "MEDIUM"
            factors.append(f"Notoriety {notoriety}/10")

        return {
            "level": level,
            "factors": factors,
            "security": loc.security or "Unknown",
            "notoriety": notoriety,
        }
