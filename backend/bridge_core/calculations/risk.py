"""Risk analysis calculations for Elite Dangerous."""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def assess_system_risk(
    security: str,
    notoriety: int,
    faction_state: str = "",
    powerplay_power: str = "",
) -> dict:
    """Assess the risk level of a system.

    Returns a dict with:
        level: "low", "medium", "high", "critical"
        score: 0-100
        factors: list of risk factor strings
    """
    score = 0
    factors = []

    # Security level
    security_lower = security.lower() if security else ""
    if "anarchy" in security_lower:
        score += 40
        factors.append("Anarchy system")
    elif "lawless" in security_lower:
        score += 30
        factors.append("Lawless system")
    elif "low" in security_lower:
        score += 15
        factors.append("Low security")
    elif "medium" in security_lower:
        score += 5

    # Notoriety
    if notoriety > 0:
        score += min(notoriety * 10, 40)
        factors.append(f"Notoriety level {notoriety}")

    # Faction state
    if faction_state:
        hostile_states = {"War", "Civil War", "Lockdown", "Terrorist Attack"}
        if faction_state in hostile_states:
            score += 15
            factors.append(f"Faction state: {faction_state}")

    # Determine level
    if score >= 70:
        level = "critical"
    elif score >= 45:
        level = "high"
    elif score >= 20:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": min(score, 100),
        "factors": factors,
    }


def assess_docking_risk(
    station_type: str,
    ship_size: str,
    notoriety: int,
) -> dict:
    """Assess risk of docking at a station.

    Returns a dict with:
        level: "low", "medium", "high"
        factors: list of risk factor strings
    """
    score = 0
    factors = []

    # Station type
    if "carrier" in (station_type or "").lower():
        score += 5
        factors.append("Fleet carrier docking")

    # Notoriety increases interdiction chance
    if notoriety > 3:
        score += 25
        factors.append("High notoriety — likely interdiction on departure")
    elif notoriety > 0:
        score += 10
        factors.append("Moderate notoriety")

    if score >= 25:
        level = "high"
    elif score >= 10:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": min(score, 100),
        "factors": factors,
    }
