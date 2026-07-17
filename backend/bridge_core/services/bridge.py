"""Bridge Service — Aggregates all department reports into a single overview.

The Bridge is the application's landing page. It represents the command
bridge of the player's ship. Its purpose is to provide immediate
situational awareness — the user should understand the current state
of the ship within approximately five seconds.

The Bridge Department owns NO Elite Dangerous data.
It never parses journal files.
It never performs gameplay calculations.
It never contains business logic.
All displayed information comes from other departments through their services.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bridge_core.state.engine import StateEngine

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# All departments in display order
# ---------------------------------------------------------------------------

ALL_DEPARTMENTS = [
    "navigation",
    "engineering",
    "laboratory",
    "operations",
    "tactical",
    "communications",
    "commander",
    "archive",
    "intelligence",
]


class BridgeService:
    """Aggregates all department reports into a Bridge overview.

    This service owns no data. It calls each department service,
    extracts the information relevant to the Bridge view, and
    returns a structured response.
    """

    def __init__(self, state: StateEngine) -> None:
        self.state = state

    def get_report(self) -> dict[str, Any]:
        """Generate the full Bridge overview."""
        reports = self._collect_reports()

        return {
            "captain_briefing": self._build_briefing(reports),
            "ship_status": self._build_ship_status(reports),
            "current_mission": self._build_current_mission(reports),
            "department_status": self._build_department_status(reports),
            "current_location": self._build_current_location(reports),
            "alerts": self._build_alerts(reports),
            "recommendations": self._build_recommendations(reports),
            "expedition_summary": self._build_expedition_summary(reports),
            "captains_log": self._build_captains_log(reports),
            "generated": datetime.now(UTC).isoformat(),
        }

    # -- Report collection ---------------------------------------------------

    def _collect_reports(self) -> dict[str, Any]:
        """Collect reports from all available department services."""
        from bridge_core.services.archive import ArchiveService
        from bridge_core.services.commander import CommanderService
        from bridge_core.services.engineering import EngineeringService
        from bridge_core.services.intelligence import IntelligenceService
        from bridge_core.services.laboratory import LaboratoryService
        from bridge_core.services.navigation import NavigationService
        from bridge_core.services.operations import OperationsService

        reports: dict[str, Any] = {}

        services = {
            "navigation": NavigationService,
            "engineering": EngineeringService,
            "operations": OperationsService,
            "intelligence": IntelligenceService,
            "commander": CommanderService,
            "laboratory": LaboratoryService,
            "archive": ArchiveService,
        }

        for name, svc_cls in services.items():
            try:
                svc = svc_cls(self.state)
                reports[name] = svc.get_report()
            except Exception:
                log.warning("Failed to get report from %s", name, exc_info=True)
                reports[name] = None

        # Tactical and Communications have no implementation yet
        reports["tactical"] = None
        reports["communications"] = None

        return reports

    # -- 1. Captain's Briefing -----------------------------------------------

    def _build_briefing(self, reports: dict[str, Any]) -> dict[str, Any]:
        """Build the captain's situational briefing."""
        s = self.state.snapshot
        parts: list[str] = []

        # Commander context
        if s.commander.name:
            parts.append(f"Cmdr {s.commander.name}")

        if s.ship.ship_type:
            parts.append(f"flying a {s.ship.ship_type}")

        # Location context
        if s.location.system:
            loc = f"in {s.location.system}"
            if s.location.station and s.location.docked:
                loc += f" at {s.location.station}"
            elif s.location.body:
                loc += f" near {s.location.body}"
            parts.append(loc)

        # Ship health summary
        health_items: list[str] = []
        if s.ship.hull_health < 100:
            health_items.append(f"hull at {s.ship.hull_health:.0f}%")
        if s.ship.fuel_capacity > 0:
            fuel_pct = (s.ship.fuel_current / s.ship.fuel_capacity) * 100
            if fuel_pct < 100:
                health_items.append(f"fuel at {fuel_pct:.0f}%")
        if health_items:
            parts.append("Conditions: " + ", ".join(health_items))

        # Activity summary
        if s.navigation.jump_count > 0:
            parts.append(
                f"{s.navigation.jump_count} jumps, "
                f"{s.navigation.total_distance_ly:.1f} LY traveled"
            )

        active = len(s.missions.active)
        if active > 0:
            parts.append(f"{active} active mission{'s' if active > 1 else ''}")

        # Overall status
        intel_report = reports.get("intelligence")
        if intel_report:
            status = intel_report.status
        else:
            status = "BLUE"

        summary = ". ".join(parts) + "." if parts else "No data available."

        return {
            "summary": summary,
            "status": status,
        }

    # -- 2. Ship Status ------------------------------------------------------

    def _build_ship_status(self, reports: dict[str, Any]) -> dict[str, Any]:
        """Build the ship status section from Engineering report."""
        s = self.state.snapshot

        ship_type = s.ship.ship_type
        ship_name = s.ship.ship_name
        hull_health = s.ship.hull_health
        fuel_capacity = s.ship.fuel_capacity
        fuel_current = s.ship.fuel_current
        cargo_capacity = s.ship.cargo_capacity
        cargo_count = s.ship.cargo_count
        rebuy = s.ship.rebuy

        # Calculate fuel percentage
        fuel_pct = 0.0
        if fuel_capacity > 0:
            fuel_pct = (fuel_current / fuel_capacity) * 100

        # Calculate cargo percentage
        cargo_pct = 0.0
        if cargo_capacity > 0:
            cargo_pct = (cargo_count / cargo_capacity) * 100

        return {
            "ship_type": ship_type,
            "ship_name": ship_name,
            "ship_ident": s.ship.ship_ident,
            "hull_health": hull_health,
            "fuel_capacity": fuel_capacity,
            "fuel_current": fuel_current,
            "fuel_percent": fuel_pct,
            "cargo_capacity": cargo_capacity,
            "cargo_count": cargo_count,
            "cargo_percent": cargo_pct,
            "rebuy": rebuy,
            "jump_range": None,  # Not available in current state
            "power_margin": None,  # Not available in current state
        }

    # -- 3. Current Mission --------------------------------------------------

    def _build_current_mission(self, reports: dict[str, Any]) -> dict[str, Any] | None:
        """Build the current mission section from Operations report."""
        s = self.state.snapshot
        active = s.missions.active

        if not active:
            return None

        # Show the most urgent mission (earliest expiry)
        best: dict[str, Any] | None = None
        best_expiry: datetime | None = None

        for mission in active:
            expiry_str = mission.get("Expiry")
            if expiry_str:
                try:
                    exp_dt = datetime.fromisoformat(
                        expiry_str.replace("Z", "+00:00")
                    )
                    if best_expiry is None or exp_dt < best_expiry:
                        best_expiry = exp_dt
                        best = mission
                except (ValueError, TypeError):
                    pass

        # If no expiry found, just pick the first
        if best is None:
            best = active[0]

        return {
            "id": best.get("MissionID"),
            "title": best.get("Type_Localised") or best.get("Type", "Unknown"),
            "destination": best.get("DestinationSystem") or best.get("DestinationStation", ""),
            "reward": best.get("Reward", 0),
            "expiration": best.get("Expiry", ""),
            "remaining_jumps": None,  # Not available in current state
        }

    # -- 4. Department Status ------------------------------------------------

    def _build_department_status(self, reports: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the department status grid from all reports."""
        departments = []

        for dept_name in ALL_DEPARTMENTS:
            report = reports.get(dept_name)

            if report is None:
                departments.append({
                    "department": dept_name,
                    "status": "OFFLINE",
                    "summary": "No data available",
                })
                continue

            # Extract summary from the report
            summary = ""
            if hasattr(report, "summary"):
                summary = report.summary
            elif isinstance(report, dict):
                summary = report.get("summary", "")

            # Extract status
            status = "BLUE"
            if hasattr(report, "status"):
                status = report.status
            elif isinstance(report, dict):
                status = report.get("status", "BLUE")

            departments.append({
                "department": dept_name,
                "status": status,
                "summary": summary[:120] + "..." if len(summary) > 120 else summary,
            })

        return departments

    # -- 5. Current Location -------------------------------------------------

    def _build_current_location(self, reports: dict[str, Any]) -> dict[str, Any]:
        """Build the current location section from Navigation report."""
        s = self.state.snapshot
        loc = s.location

        return {
            "system": loc.system,
            "body": loc.body,
            "primary_star": loc.body if loc.body_type == "Star" else "",
            "bodies_count": s.scans.bodies_scanned,
            "stations": [loc.station] if loc.station else [],
            "fleet_carriers": [],  # Not available in current state
            "security": loc.security,
            "economy": loc.economy,
            "population": loc.population,
            "faction": loc.faction,
            "government": loc.government,
            "allegiance": loc.allegiance,
            "docked": loc.docked,
            "near_body": loc.near_body,
        }

    # -- 6. Alerts -----------------------------------------------------------

    def _build_alerts(self, reports: dict[str, Any]) -> list[dict[str, Any]]:
        """Aggregate alerts from all department reports.

        Alerts are findings with RED, ORANGE, or YELLOW severity.
        Each department may produce findings that warrant attention.
        """
        alerts: list[dict[str, Any]] = []

        for dept_name, report in reports.items():
            if report is None:
                continue

            findings = []
            if hasattr(report, "findings"):
                findings = report.findings
            elif isinstance(report, dict):
                findings = report.get("findings", [])

            for finding in findings:
                severity = getattr(finding, "severity", "BLUE")
                if isinstance(finding, dict):
                    severity = finding.get("severity", "BLUE")

                if severity in ("RED", "ORANGE", "YELLOW"):
                    title = getattr(finding, "title", "")
                    description = getattr(finding, "description", "")
                    if isinstance(finding, dict):
                        title = finding.get("title", "")
                        description = finding.get("description", "")

                    alerts.append({
                        "title": title,
                        "description": description,
                        "severity": severity,
                        "department": dept_name,
                    })

        # Sort by severity: RED first, then ORANGE, then YELLOW
        severity_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2}
        alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))

        return alerts

    # -- 7. Recommendations --------------------------------------------------

    def _build_recommendations(self, reports: dict[str, Any]) -> list[dict[str, Any]]:
        """Pass through recommendations from the Intelligence department.

        Per SPEC.md, recommendations are generated exclusively by Intelligence.
        """
        intel = reports.get("intelligence")
        if intel is None:
            return []

        recs = []
        if hasattr(intel, "recommendations"):
            recs = intel.recommendations
        elif isinstance(intel, dict):
            recs = intel.get("recommendations", [])

        result = []
        for rec in recs:
            if hasattr(rec, "priority"):
                result.append({
                    "priority": rec.priority,
                    "message": rec.message,
                    "reason": rec.reason,
                    "action": rec.action,
                })
            elif isinstance(rec, dict):
                result.append({
                    "priority": rec.get("priority", "low"),
                    "message": rec.get("message", ""),
                    "reason": rec.get("reason", ""),
                    "action": rec.get("action", ""),
                })

        return result

    # -- 8. Expedition Summary -----------------------------------------------

    def _build_expedition_summary(self, reports: dict[str, Any]) -> dict[str, Any]:
        """Build expedition summary from Archive and session data."""
        s = self.state.snapshot
        nav = s.navigation
        scans = s.scans
        missions = s.missions

        return {
            "jumps": nav.jump_count,
            "distance_ly": nav.total_distance_ly,
            "bodies_scanned": scans.bodies_scanned,
            "bodies_detailed": scans.bodies_detailed,
            "organic_scans": len(scans.organic_scans),
            "missions_completed": len(missions.complete),
            "missions_failed": len(missions.failed),
            "missions_active": len(missions.active),
        }

    # -- 9. Captain's Log ----------------------------------------------------

    def _build_captains_log(self, reports: dict[str, Any]) -> list[dict[str, Any]]:
        """Build a chronological log of significant session events.

        Derived from the current session state since persistent
        event logging is not yet implemented.
        """
        s = self.state.snapshot
        log_entries: list[dict[str, Any]] = []

        # Session started
        if s.commander.name:
            log_entries.append({
                "event": f"Session started — Cmdr {s.commander.name}",
                "department": "commander",
            })

        # Ship loaded
        if s.ship.ship_type:
            log_entries.append({
                "event": f"Ship loaded: {s.ship.ship_type}",
                "department": "engineering",
            })

        # Current location
        if s.location.system:
            location_event = f"Location: {s.location.system}"
            if s.location.station:
                location_event += f" at {s.location.station}"
            log_entries.append({
                "event": location_event,
                "department": "navigation",
            })

        # Jump history
        if s.navigation.jump_count > 0:
            log_entries.append({
                "event": (
                    f"{s.navigation.jump_count} jump(s) made, "
                    f"covering {s.navigation.total_distance_ly:.1f} LY"
                ),
                "department": "navigation",
            })

        # Scans
        if s.scans.bodies_scanned > 0:
            log_entries.append({
                "event": f"{s.scans.bodies_scanned} body(s) scanned",
                "department": "laboratory",
            })

        # Organic scans
        if s.scans.organic_scans:
            log_entries.append({
                "event": (
                    f"{len(s.scans.organic_scans)} organic sample(s) collected"
                ),
                "department": "laboratory",
            })

        # Missions completed
        if s.missions.complete:
            log_entries.append({
                "event": f"{len(s.missions.complete)} mission(s) completed",
                "department": "operations",
            })

        # Missions failed
        if s.missions.failed:
            log_entries.append({
                "event": f"{len(s.missions.failed)} mission(s) failed",
                "department": "operations",
            })

        # Notoriety
        if s.notoriety > 0:
            log_entries.append({
                "event": f"Notoriety level: {s.notoriety}",
                "department": "tactical",
            })

        if not log_entries:
            log_entries.append({
                "event": "No session activity recorded",
                "department": "bridge",
            })

        return log_entries
