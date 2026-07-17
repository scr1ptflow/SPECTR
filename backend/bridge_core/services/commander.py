"""Commander Service — Officer Report for the Commander department.

Follows the SPEC.md department pattern:
    Officer Report → Recommendations → Details → History

The Commander officer answers:
    "What is the commander's current status?"
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.services.report import DepartmentReport, Finding, Recommendation
from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)

RANK_NAMES: dict[str, list[str]] = {
    "combat": [
        "Harmless", "Mostly Harmless", "Novice", "Competent", "Expert",
        "Master", "Dangerous", "Deadly", "Elite",
    ],
    "trade": [
        "Penniless", "Mostly Penniless", "Peddler", "Dealer", "Merchant",
        "Broker", "Entrepreneur", "Tycoon", "Elite",
    ],
    "explore": [
        "Aimless", "Mostly Aimless", "Explorer", "Pathfinder", "Surveyor",
        "Trailblazer", "Strider", "Pioneer", "Elite",
    ],
    "cqc": [
        "Helpless", "Mostly Helpless", "Amateur", "Semi-Professional",
        "Professional", "Champion", "Hero", "Legend", "Elite",
    ],
    "empire": [
        "None", "Outsider", "Serf", "Master", "Squire", "Knight", "Lord",
        "Baron", "Viscount", "Count", "Earl", "Duke", "Prince", "King",
    ],
    "federation": [
        "None", "Recruit", "Midshipman", "Petty Officer",
        "Chief Petty Officer", "Warrant Officer", "Ensign",
        "Lieutenant", "Lieutenant Commander", "Post Commander",
        "Post Captain", "Rear Admiral", "Vice Admiral", "Admiral",
    ],
    "soldier": [
        "Defenceless", "Unskilled", "Skilled", "Capable", "Proficient",
        "Competent", "Expert", "Veteran", "Elite",
    ],
    "exobiologist": [
        "Directionless", "Mostly Directionless", "Explorer",
        "Pathfinder", "Surveyor", "Trailblazer", "Strider",
        "Pioneer", "Elite",
    ],
}


class CommanderService:
    """Generates the Commander Officer Report from the current game state."""

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> DepartmentReport:
        """Generate a full Commander Officer Report."""
        s = self.state.snapshot
        now = datetime.now(UTC).isoformat()

        findings = self._generate_findings(s)
        recommendations = self._generate_recommendations(s)
        status = self._determine_status(s, findings)
        summary = self._generate_summary(s)
        details = self._build_details(s)
        history = self._build_history(s)

        return DepartmentReport(
            department="commander",
            title="Commander Report",
            status=status,
            summary=summary,
            findings=findings,
            recommendations=recommendations,
            details=details,
            history=history,
            generated=now,
        )

    # -- Status determination ------------------------------------------------

    def _determine_status(
        self, state: Any, findings: list[Finding]
    ) -> str:
        """Determine operational status based on current conditions."""
        cmdr = state.commander

        if not cmdr.name:
            return "RED"

        for f in findings:
            if f.severity == "RED":
                return "RED"
            if f.severity == "ORANGE":
                return "ORANGE"
        for f in findings:
            if f.severity == "YELLOW":
                return "YELLOW"

        if cmdr.name:
            return "GREEN"

        return "BLUE"

    # -- Findings ------------------------------------------------------------

    def _generate_findings(self, state: Any) -> list[Finding]:
        """Analyze current state and generate findings."""
        cmdr = state.commander
        findings: list[Finding] = []

        if not cmdr.name:
            findings.append(Finding(
                title="No Commander Data",
                description=(
                    "No commander data available. "
                    "The system has not received LoadGame information."
                ),
                severity="RED",
            ))
            return findings

        # Credits
        if cmdr.credits > 1000000000:
            findings.append(Finding(
                title="Wealthy Commander",
                description=(
                    f"Current balance: {cmdr.credits:,} CR. "
                    "Significant financial resources available."
                ),
                severity="GREEN",
            ))
        elif cmdr.credits < 100000:
            findings.append(Finding(
                title="Low Funds",
                description=(
                    f"Current balance: {cmdr.credits:,} CR. "
                    "Funds may be insufficient for ship rebuy or repairs."
                ),
                severity="ORANGE",
            ))

        # Loan
        if cmdr.loan > 0:
            findings.append(Finding(
                title="Active Loan",
                description=(
                    f"Outstanding loan: {cmdr.loan:,} CR. "
                    "Loan repayment may affect available funds."
                ),
                severity="YELLOW",
            ))

        # Squadron
        if cmdr.squadron:
            findings.append(Finding(
                title="Squadron Affiliation",
                description=f"Affiliated with squadron: {cmdr.squadron}.",
                severity="BLUE",
            ))

        # Powerplay
        if cmdr.powerplay_power:
            findings.append(Finding(
                title="Powerplay Active",
                description=(
                    f"Currently pledged to {cmdr.powerplay_power} "
                    f"(Rank {cmdr.powerplay_rank}, "
                    f"{cmdr.powerplay_merits} merits)."
                ),
                severity="BLUE",
            ))

        # Career rank highlights
        for category in ("combat", "trade", "explore"):
            level = getattr(state.ranks, category, 0)
            if level >= 8:
                names = RANK_NAMES.get(category, [])
                rank_name = names[level] if level < len(names) else str(level)
                findings.append(Finding(
                    title=f"{category.title()} Elite",
                    description=(
                        f"Rank: {rank_name} in {category}."
                    ),
                    severity="GREEN",
                ))

        if not findings:
            findings.append(Finding(
                title="Commander Nominal",
                description=(
                    f"Commander {cmdr.name} operating normally. "
                    "No issues detected."
                ),
                severity="GREEN",
            ))

        return findings

    # -- Recommendations -----------------------------------------------------

    def _generate_recommendations(
        self, state: any
    ) -> list[Recommendation]:
        """Generate actionable recommendations."""
        cmdr = state.commander
        recs: list[Recommendation] = []

        if cmdr.credits < 100000:
            recs.append(Recommendation(
                priority="high",
                message="Increase available funds",
                reason="Current balance may not cover ship rebuy",
                action=(
                    "Complete trade missions or sell exploration data "
                    "to build financial reserves"
                ),
            ))

        if cmdr.loan > 0 and cmdr.credits > cmdr.loan * 2:
            recs.append(Recommendation(
                priority="low",
                message="Consider repaying loan",
                reason="Sufficient funds available to clear debt",
                action="Visit a station and repay outstanding loan",
            ))

        return recs

    # -- Summary -------------------------------------------------------------

    def _generate_summary(self, state: Any) -> str:
        """Generate a natural language officer briefing."""
        cmdr = state.commander

        if not cmdr.name:
            return (
                "Commander database offline. "
                "No commander data available."
            )

        parts = [f"Commander {cmdr.name}."]
        parts.append(f"Balance: {cmdr.credits:,} CR.")

        if cmdr.loan > 0:
            parts.append(f"Loan: {cmdr.loan:,} CR.")

        if cmdr.squadron:
            parts.append(f"Squadron: {cmdr.squadron}.")

        if cmdr.powerplay_power:
            parts.append(
                f"Pledged to {cmdr.powerplay_power}."
            )

        return " ".join(parts)

    # -- Details -------------------------------------------------------------

    def _build_details(self, state: Any) -> dict[str, Any]:
        """Build the detailed commander data."""
        cmdr = state.commander
        ranks = {}

        for category in RANK_NAMES:
            level = getattr(state.ranks, category, 0)
            progress = getattr(
                state.ranks, f"{category}_progress", 0
            )
            names = RANK_NAMES.get(category, [])
            rank_name = (
                names[level] if 0 <= level < len(names) else str(level)
            )
            ranks[category] = {
                "level": level,
                "name": rank_name,
                "progress": progress,
            }

        return {
            "name": cmdr.name,
            "credits": cmdr.credits,
            "loan": cmdr.loan,
            "squadron": cmdr.squadron,
            "powerplay_power": cmdr.powerplay_power,
            "powerplay_rank": cmdr.powerplay_rank,
            "powerplay_merits": cmdr.powerplay_merits,
            "ranks": ranks,
        }

    # -- History -------------------------------------------------------------

    def _build_history(self, state: Any) -> dict[str, Any]:
        """Build session history for the Commander department."""
        elite_count = 0
        for category in ("combat", "trade", "explore", "cqc",
                         "empire", "federation", "soldier",
                         "exobiologist"):
            level = getattr(state.ranks, category, 0)
            if level >= 8:
                elite_count += 1

        return {
            "total_rank": sum(
                getattr(state.ranks, c, 0)
                for c in RANK_NAMES
            ),
            "elite_ranks": elite_count,
        }
