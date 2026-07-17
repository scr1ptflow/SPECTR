"""Tests for the Session Manager."""

import asyncio
import tempfile
import pytest
import pytest_asyncio
from pathlib import Path

from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine
from bridge_core.database.db import Database
from bridge_core.services.session_manager import SessionManager


@pytest_asyncio.fixture
async def session_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    await db.connect()
    bus = EventBus()
    state = StateEngine(bus)
    sm = SessionManager(bus, db)
    yield bus, state, sm, db

    await db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_session_starts_on_loadgame(session_env):
    bus, state, sm, db = session_env

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 1000000, "Ship": "python"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    assert sm.is_active
    assert sm.session.commander == "TestCmdr"
    assert sm.session.ship == "python"
    assert sm.session.credits_start == 1000000
    assert sm.session.session_id > 0


@pytest.mark.asyncio
async def test_session_tracks_jumps(session_env):
    bus, state, sm, db = session_env

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 1000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.fsdjump",
        data={"StarSystem": "Alpha Centauri", "DistFromStarLs": 4.5},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.fsdjump",
        data={"StarSystem": "Proxima Centauri", "DistFromStarLs": 1.5},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.15)
    bus.stop()
    await task

    assert sm.session.jumps == 2
    assert sm.session.distance_ly == 6.0
    assert "Alpha Centauri" in sm.session.systems_visited


@pytest.mark.asyncio
async def test_session_tracks_scans(session_env):
    bus, state, sm, db = session_env

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 1000000, "Ship": "python"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.scan",
        data={"BodyName": "Earth"},
        source="journal",
    ))
    await bus.publish(Event(
        topic="journal.scanorganic",
        data={"Species": "Stratum Tectonicas", "Body": "Earth"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.15)
    bus.stop()
    await task

    assert sm.session.bodies_scanned == 1
    assert sm.session.organic_scans == 1


@pytest.mark.asyncio
async def test_session_ends_on_new_loadgame(session_env):
    bus, state, sm, db = session_env

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 1000000, "Ship": "python"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    assert sm.is_active

    # New loadgame should end old session and start new one
    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 1100000, "Ship": "anaconda"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    assert sm.is_active
    assert sm.session.ship == "anaconda"
    assert sm.session.credits_start == 1100000


@pytest.mark.asyncio
async def test_session_snapshot_dict(session_env):
    bus, state, sm, db = session_env

    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 500, "Ship": "sidewinder"},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.1)
    bus.stop()
    await task

    data = sm.snapshot_dict()
    assert data["active"] is True
    assert data["commander"] == "TestCmdr"
    assert data["credits_start"] == 500
    assert "session_id" in data
