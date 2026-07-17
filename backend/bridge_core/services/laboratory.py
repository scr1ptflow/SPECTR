"""Laboratory Service — Officer Report for the Laboratory department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Laboratory officer answers:
    "What scientific opportunities exist?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


class LaboratoryService:
    """Generates the Laboratory Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Laboratory Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="laboratory",
            title="Laboratory Report",
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
            if f.severity == "ORANGE":
                return "ORANGE"
        for f in findings:
            if f.severity == "YELLOW":
                return "YELLOW"
        scans = state.scans
        if scans.organic_scans or scans.bodies_scanned > 0:
            return "GREEN"
        return "BLUE"

    def _generate_findings(self, state: Any) -> list[Finding]:
        scans = state.scans
        findings: list[Finding] = []

        if scans.bodies_scanned > 0:
            findings.append(Finding(
                title="Bodies Scanned",
                description=(
                    f"{scans.bodies_scanned} body(s) scanned this session."
                ),
                severity="GREEN",
            ))

        organic_count = len(scans.organic_scans)
        if organic_count > 0:
            findings.append(Finding(
                title="Organic Samples Collected",
                description=(
                    f"{organic_count} organic sample(s) collected."
                ),
                severity="GREEN",
            ))

        sold_count = len(scans.organic_sold)
        if sold_count > 0:
            total = sum(
                v["value"] for v in scans.organic_sold.values()
            )
            findings.append(Finding(
                title="Scientific Data Sold",
                description=(
                    f"{sold_count} species data sold for "
                    f"{total:,} CR."
                ),
                severity="BLUE",
            ))

        if scans.bodies_scanned == 0 and organic_count == 0:
            findings.append(Finding(
                title="No Scan Data",
                description=(
                    "No bodies scanned and no organic samples "
                    "collected this session."
                ),
                severity="BLUE",
            ))

        return findings

    def _generate_recommendations(
        self, state: any
    ) -> list[Recommendation]:
        loc = state.location
        scans = state.scans
        recs: list[Recommendation] = []

        if loc.near_body and scans.bodies_scanned == 0:
            recs.append(Recommendation(
                priority="medium",
                message="Perform a Full Spectrum Scan",
                reason="Currently near a body with no scan data",
                action="Use the Discovery Scanner to catalog system bodies",
            ))

        if loc.body_type == "Planet" and not loc.docked:
            recs.append(Recommendation(
                priority="low",
                message="Consider exobiology survey",
                reason="Orbiting a planetary body",
                action=(
                    "Land and use the Genetic Sampler "
                    "to scan for biological signatures"
                ),
            ))

        return recs

    def _generate_summary(self, state: Any) -> str:
        scans = state.scans
        parts = []

        if scans.bodies_scanned > 0:
            parts.append(
                f"{scans.bodies_scanned} body(s) scanned"
            )

        organic = len(scans.organic_scans)
        if organic > 0:
            parts.append(
                f"{organic} organic sample(s) collected"
            )

        sold = len(scans.organic_sold)
        if sold > 0:
            total = sum(
                v["value"] for v in scans.organic_sold.values()
            )
            parts.append(
                f"{sold} species sold for {total:,} CR"
            )

        if not parts:
            return (
                "No scientific data collected this session. "
                "Opportunities may be available."
            )

        return "Laboratory status: " + "; ".join(parts) + "."

    def _build_details(self, state: Any) -> dict[str, Any]:
        scans = state.scans

        species_seen: dict[str, dict] = {}
        for scan in scans.organic_scans:
            species = (
                scan.get("Species_Localised")
                or scan.get("Species", "")
            )
            variant = (
                scan.get("Variant_Localised")
                or scan.get("Variant", "")
            )
            key = f"{species}|{variant}"
            if key not in species_seen:
                species_seen[key] = {
                    "species": species,
                    "variant": variant,
                    "body": scan.get("Body", ""),
                    "count": 0,
                }
            species_seen[key]["count"] += 1

        sold = []
        for key, val in scans.organic_sold.items():
            parts = key.split("|")
            sold.append({
                "species": parts[0] if parts else "",
                "variant": parts[1] if len(parts) > 1 else "",
                "value": val["value"],
                "count": val["count"],
            })

        return {
            "bodies_scanned": scans.bodies_scanned,
            "bodies_detailed": scans.bodies_detailed,
            "organic_scan_count": len(scans.organic_scans),
            "unique_species": len(species_seen),
            "species": list(species_seen.values()),
            "sold": sold,
            "total_earned": sum(
                v["value"] for v in scans.organic_sold.values()
            ),
        }

    def _build_history(self, state: Any) -> dict[str, Any]:
        scans = state.scans
        return {
            "bodies_scanned": scans.bodies_scanned,
            "organic_scans": len(scans.organic_scans),
            "species_sold": len(scans.organic_sold),
        }
