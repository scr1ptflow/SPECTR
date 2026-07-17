"""Intelligence Service — Officer Report for the Intelligence department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Intelligence officer answers:
    "What should we do next?"

Intelligence owns no data. It interprets every other department.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class IntelligenceService:
    """Analyzes all departments and generates actionable intelligence."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Intelligence Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="intelligence",
            title="Intelligence Report",
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
        risk = self._assess_risk(state)
        if risk == "critical":
            return "RED"
        if risk == "high":
            return "ORANGE"
        if risk == "medium":
            return "YELLOW"
        return "GREEN"

    def _generate_findings(self, state: Any) -> list[Finding]:
        findings: list[Finding] = []

        # Security findings
        if state.notoriety > 0:
            sev = "RED" if state.notoriety >= 5 else "ORANGE"
            findings.append(Finding(
                title="Notoriety Active",
                description=(
                    f"Notoriety level {state.notoriety}. "
                    "Expect hostility from authorities."
                ),
                severity=sev,
            ))

        if "anarchy" in state.location.security.lower():
            findings.append(Finding(
                title="Anarchy System",
                description="No law enforcement. Exercise caution.",
                severity="ORANGE",
            ))

        # Ship health
        if state.ship.hull_health < 50:
            findings.append(Finding(
                title="Hull Critical",
                description=(
                    f"Hull at {state.ship.hull_health:.0f}%. "
                    "Seek repairs immediately."
                ),
                severity="RED",
            ))
        elif state.ship.hull_health < 80:
            findings.append(Finding(
                title="Hull Damage",
                description=f"Hull at {state.ship.hull_health:.0f}%.",
                severity="YELLOW",
            ))

        # Fuel
        if state.ship.fuel_capacity > 0:
            fuel_pct = (
                (state.ship.fuel_current / state.ship.fuel_capacity)
                * 100
            )
            if fuel_pct < 20:
                findings.append(Finding(
                    title="Fuel Critical",
                    description=f"Fuel at {fuel_pct:.0f}%.",
                    severity="RED",
                ))
            elif fuel_pct < 50:
                findings.append(Finding(
                    title="Fuel Low",
                    description=f"Fuel at {fuel_pct:.0f}%.",
                    severity="YELLOW",
                ))

        # Exploration opportunities
        if state.location.near_body and state.scans.bodies_scanned == 0:
            findings.append(Finding(
                title="Unscanned Body Nearby",
                description=(
                    "Near a body that hasn't been scanned. "
                    "Potential exploration value."
                ),
                severity="BLUE",
            ))

        # Mission expiry
        for mission in state.missions.active:
            expiry = mission.get("Expiry")
            if expiry:
                try:
                    exp_dt = datetime.fromisoformat(
                        expiry.replace("Z", "+00:00")
                    )
                    if exp_dt < datetime.now(UTC):
                        findings.append(Finding(
                            title="Mission Expired",
                            description=(
                                f"Mission '{mission.get('Type', 'Unknown')}' "
                                "has expired."
                            ),
                            severity="YELLOW",
                        ))
                        break
                except (ValueError, TypeError):
                    pass

        # Session highlights
        if state.navigation.jump_count > 10:
            findings.append(Finding(
                title="Long-Range Expedition",
                description=(
                    f"{state.navigation.jump_count} jumps made "
                    f"covering {state.navigation.total_distance_ly:.1f} LY."
                ),
                severity="BLUE",
            ))

        if not findings:
            findings.append(Finding(
                title="All Systems Nominal",
                description="No alerts or concerns detected.",
                severity="GREEN",
            ))

        return findings

    def _generate_recommendations(
        self, state: any
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []

        # Scan recommendation
        if state.location.near_body and state.scans.bodies_scanned == 0:
            recs.append(Recommendation(
                priority="medium",
                message="Scan nearby body",
                reason="Unscanned body detected in proximity",
                action="Use Discovery Scanner and Detailed Surface Scanner",
            ))

        # Exobiology
        if state.location.body_type == "Planet" and not state.location.docked:
            recs.append(Recommendation(
                priority="low",
                message="Survey for biological signatures",
                reason="Orbiting a planetary body",
                action="Land and deploy Genetic Sampler",
            ))

        # Repair
        if state.ship.hull_health < 80 and state.location.docked:
            recs.append(Recommendation(
                priority="high",
                message="Repair ship",
                reason="Hull damaged while docked",
                action="Visit Advanced Maintenance menu",
            ))

        # Fuel
        if state.ship.fuel_capacity > 0:
            fuel_pct = (
                (state.ship.fuel_current / state.ship.fuel_capacity)
                * 100
            )
            if fuel_pct < 25:
                recs.append(Recommendation(
                    priority="critical",
                    message="Find fuel immediately",
                    reason="Fuel reserves critically low",
                    action=(
                        "Route to scoopable star (KGBFOOM) "
                        "or request fuel limpet"
                    ),
                ))

        return recs

    def _generate_summary(self, state: Any) -> str:
        parts = []

        if state.commander.name:
            parts.append(f"Cmdr {state.commander.name}")

        if state.ship.ship_type:
            parts.append(f"flying a {state.ship.ship_type}")

        if state.location.system:
            loc = f"in {state.location.system}"
            if state.location.body:
                loc += f" near {state.location.body}"
            if state.location.station:
                loc += f" at {state.location.station}"
            parts.append(loc)

        if state.navigation.jump_count > 0:
            parts.append(
                f"made {state.navigation.jump_count} jumps "
                f"covering {state.navigation.total_distance_ly:.1f} LY"
            )

        if state.scans.bodies_scanned > 0:
            parts.append(
                f"scanned {state.scans.bodies_scanned} bodies"
            )

        if state.scans.organic_scans:
            parts.append(
                f"collected {len(state.scans.organic_scans)} "
                "organic samples"
            )

        if state.missions.active:
            parts.append(
                f"with {len(state.missions.active)} active missions"
            )

        return ". ".join(parts) + "." if parts else "No data available."

    def _assess_risk(self, state: Any) -> str:
        score = 0

        if "anarchy" in state.location.security.lower():
            score += 30
        if state.notoriety > 0:
            score += min(state.notoriety * 10, 40)
        if state.ship.hull_health < 50:
            score += 25

        if score >= 60:
            return "critical"
        if score >= 35:
            return "high"
        if score >= 15:
            return "medium"
        return "low"

    def _build_details(self, state: Any) -> dict[str, Any]:
        return {
            "risk_level": self._assess_risk(state),
            "alerts": [
                {
                    "title": f.title,
                    "description": f.description,
                    "severity": f.severity,
                }
                for f in self._generate_findings(state)
                if f.severity in ("RED", "ORANGE", "YELLOW")
            ],
            "session_highlights": self._session_highlights(state),
        }

    def _build_history(self, state: Any) -> dict[str, Any]:
        return {
            "risk_level": self._assess_risk(state),
            "highlights": self._session_highlights(state),
        }

    def _session_highlights(self, state: Any) -> list[str]:
        highlights: list[str] = []

        if state.navigation.jump_count > 10:
            highlights.append(
                f"Long-range expedition: "
                f"{state.navigation.jump_count} jumps"
            )
        if state.scans.bodies_scanned > 5:
            highlights.append(
                f"Prolific explorer: "
                f"{state.scans.bodies_scanned} bodies scanned"
            )
        if state.scans.organic_scans:
            highlights.append(
                f"Exobiologist: "
                f"{len(state.scans.organic_scans)} organic samples"
            )
        if state.missions.complete:
            highlights.append(
                f"Mission runner: "
                f"{len(state.missions.complete)} completed"
            )
        if state.commander.credits > 10_000_000:
            highlights.append(
                f"Wealthy: {state.commander.credits:,} CR"
            )

        return highlights
