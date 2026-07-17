"""Tests for the services layer."""

import asyncio
import pytest
from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine
from bridge_core.services.commander import CommanderService
from bridge_core.services.navigation import NavigationService
from bridge_core.services.engineering import EngineeringService
from bridge_core.services.operations import OperationsService
from bridge_core.services.laboratory import LaboratoryService
from bridge_core.services.archive import ArchiveService
from bridge_core.services.bridge import BridgeService
from bridge_core.services.statistics import StatisticsService


@pytest.fixture
def populated_state():
    bus = EventBus()
    state = StateEngine(bus)

    async def _populate():
        events = [
            Event(topic="journal.loadgame", data={
                "Commander": "TestCmdr", "Credits": 5000000, "Ship": "python",
            }, source="journal"),
            Event(topic="journal.rank", data={
                "Combat": 5, "Trade": 3, "Explore": 8,
            }, source="journal"),
            Event(topic="journal.location", data={
                "StarSystem": "Sol", "Body": "Earth", "StationName": "Galileo",
            }, source="journal"),
            Event(topic="journal.fsdjump", data={
                "StarSystem": "Alpha Centauri", "DistFromStarLs": 4.5,
            }, source="journal"),
            Event(topic="journal.missionaccepted", data={
                "MissionID": 1, "Type": "Delivery",
            }, source="journal"),
            Event(topic="journal.missioncompleted", data={
                "MissionID": 2, "Type": "Courier",
            }, source="journal"),
            Event(topic="journal.scanorganic", data={
                "Species": "Stratum Tectonicas", "Body": "Earth",
            }, source="journal"),
        ]
        for event in events:
            await bus.publish(event)

        bus._running = True
        task = asyncio.create_task(bus.run())
        await asyncio.sleep(0.1)
        bus.stop()
        await task

    asyncio.run(_populate())
    return state


def test_commander_report(populated_state):
    svc = CommanderService(populated_state)
    report = svc.get_report()
    assert report.department == "commander"
    assert report.title == "Commander Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["name"] == "TestCmdr"
    assert report.details["credits"] == 5000000
    assert "combat" in report.details["ranks"]
    assert report.details["ranks"]["combat"]["level"] == 5
    assert report.details["ranks"]["combat"]["name"] == "Master"
    assert report.details["ranks"]["explore"]["level"] == 8
    assert report.details["ranks"]["explore"]["name"] == "Elite"


def test_navigation_report(populated_state):
    svc = NavigationService(populated_state)
    report = svc.get_report()
    assert report.department == "navigation"
    assert report.title == "Navigation Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["system"] == "Alpha Centauri"
    assert report.history["jumps"] == 1


def test_navigation_report_empty_state():
    bus = EventBus()
    state = StateEngine(bus)
    svc = NavigationService(state)
    report = svc.get_report()
    assert report.status == "RED"
    assert "No Navigation Data" in report.summary or "offline" in report.summary.lower()
    assert len(report.findings) >= 1
    assert report.findings[0].severity == "RED"


def test_engineering_report(populated_state):
    svc = EngineeringService(populated_state)
    report = svc.get_report()
    assert report.department == "engineering"
    assert report.title == "Engineering Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["ship_type"] == "python"


def test_operations_report(populated_state):
    svc = OperationsService(populated_state)
    report = svc.get_report()
    assert report.department == "operations"
    assert report.title == "Operations Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["active_count"] >= 1
    assert report.details["complete_count"] >= 1


def test_laboratory_report(populated_state):
    svc = LaboratoryService(populated_state)
    report = svc.get_report()
    assert report.department == "laboratory"
    assert report.title == "Laboratory Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["organic_scan_count"] >= 1


def test_archive_report(populated_state):
    svc = ArchiveService(populated_state)
    report = svc.get_report()
    assert report.department == "archive"
    assert report.title == "Archive Report"
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert report.summary
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert report.details["jumps"] >= 1
    assert report.history["jumps"] >= 1


def test_archive_report_empty_state():
    bus = EventBus()
    state = StateEngine(bus)
    svc = ArchiveService(state)
    report = svc.get_report()
    assert report.status == "BLUE"
    assert report.details["jumps"] == 0


def test_statistics_report(populated_state):
    svc = StatisticsService(populated_state)
    report = svc.get_report()
    assert report.jumps_this_session == 1
    assert report.credits == 5000000


def test_bridge_report(populated_state):
    svc = BridgeService(populated_state)
    report = svc.get_report()

    # All 9 sections present
    assert "captain_briefing" in report
    assert "ship_status" in report
    assert "current_mission" in report
    assert "department_status" in report
    assert "current_location" in report
    assert "alerts" in report
    assert "recommendations" in report
    assert "expedition_summary" in report
    assert "captains_log" in report
    assert "generated" in report

    # Captain's briefing
    briefing = report["captain_briefing"]
    assert briefing["status"] in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")
    assert "TestCmdr" in briefing["summary"]
    assert "Alpha Centauri" in briefing["summary"]

    # Ship status
    ship = report["ship_status"]
    assert ship["ship_type"] == "python"
    assert ship["hull_health"] == 100.0

    # Current mission
    assert report["current_mission"] is not None
    assert report["current_mission"]["title"] == "Delivery"

    # Department status
    depts = report["department_status"]
    assert len(depts) == 9
    dept_names = [d["department"] for d in depts]
    assert "navigation" in dept_names
    assert "engineering" in dept_names
    assert "tactical" in dept_names

    # Location
    loc = report["current_location"]
    assert loc["system"] == "Alpha Centauri"

    # Expedition summary
    exp = report["expedition_summary"]
    assert exp["jumps"] == 1

    # Captain's log
    log = report["captains_log"]
    assert len(log) >= 1


def test_bridge_report_empty_state():
    bus = EventBus()
    state = StateEngine(bus)
    svc = BridgeService(state)
    report = svc.get_report()

    assert report["captain_briefing"]["status"] in ("BLUE", "GREEN")
    assert report["current_mission"] is None
    assert len(report["captains_log"]) >= 1
