"""Tests for the Intelligence Service."""

import asyncio
import pytest
from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine
from bridge_core.services.intelligence import IntelligenceService


@pytest.fixture
def bus_and_state():
    bus = EventBus()
    state = StateEngine(bus)
    return bus, state


@pytest.mark.asyncio
async def test_intelligence_generates_report(bus_and_state):
    bus, state = bus_and_state

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 5000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.location",
        data={"StarSystem": "Sol", "Security": "High"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    svc = IntelligenceService(state)
    report = svc.get_report()

    assert report.department == "intelligence"
    assert report.generated != ""
    assert isinstance(report.findings, list)
    assert isinstance(report.recommendations, list)
    assert isinstance(report.summary, str)
    assert report.status in ("GREEN", "BLUE", "YELLOW", "ORANGE", "RED")


@pytest.mark.asyncio
async def test_intelligence_anarchy_alert(bus_and_state):
    bus, state = bus_and_state

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 5000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.location",
        data={"StarSystem": "Anarchy", "SystemSecurity": "Anarchy"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    svc = IntelligenceService(state)
    report = svc.get_report()

    anarchy_findings = [f for f in report.findings if "Anarchy" in f.title]
    assert len(anarchy_findings) > 0
    assert report.status in ("YELLOW", "ORANGE", "RED")


@pytest.mark.asyncio
async def test_intelligence_notoriety_alert(bus_and_state):
    bus, state = bus_and_state

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 5000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.notoriety",
        data={"Notoriety": 3},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    svc = IntelligenceService(state)
    report = svc.get_report()

    notor_findings = [f for f in report.findings if "Notoriety" in f.title]
    assert len(notor_findings) > 0


@pytest.mark.asyncio
async def test_intelligence_summary(bus_and_state):
    bus, state = bus_and_state

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "EliteCmdr", "Credits": 5000000, "Ship": "anaconda"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.location",
        data={"StarSystem": "Sol"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    svc = IntelligenceService(state)
    report = svc.get_report()

    assert "EliteCmdr" in report.summary
    assert "anaconda" in report.summary
    assert "Sol" in report.summary


@pytest.mark.asyncio
async def test_intelligence_recommendations_on_body(bus_and_state):
    bus, state = bus_and_state

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 5000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.approachbody",
        data={"Body": "Earth", "StarSystem": "Sol"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    svc = IntelligenceService(state)
    report = svc.get_report()

    scan_recs = [r for r in report.recommendations if "Scan" in r.message]
    assert len(scan_recs) > 0


def test_intelligence_report_to_dict(bus_and_state):
    bus, state = bus_and_state
    svc = IntelligenceService(state)
    report = svc.get_report()
    d = report.to_dict()
    assert isinstance(d, dict)
    assert "findings" in d
    assert "recommendations" in d
    assert "summary" in d
    assert "details" in d
    assert "risk_level" in d["details"]
