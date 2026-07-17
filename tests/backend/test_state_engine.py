"""Tests for the state engine."""

import asyncio
import pytest
from bridge_core.events.bus import Event, EventBus
from bridge_core.state.engine import StateEngine


@pytest.fixture
def bus_and_state():
    bus = EventBus()
    state = StateEngine(bus)
    return bus, state


@pytest.mark.asyncio
async def test_load_game_updates_state(bus_and_state):
    bus, state = bus_and_state
    await bus.publish(Event(
        topic="journal.loadgame",
        data={
            "Commander": "TestCmdr",
            "Credits": 1000000,
            "Ship": "python",
            "FuelCapacity": 32.0,
        },
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert state.snapshot.commander.name == "TestCmdr"
    assert state.snapshot.commander.credits == 1000000
    assert state.snapshot.ship.ship_type == "python"


@pytest.mark.asyncio
async def test_location_update(bus_and_state):
    bus, state = bus_and_state
    await bus.publish(Event(
        topic="journal.location",
        data={
            "StarSystem": "Sol",
            "Body": "Earth",
            "BodyType": "Planet",
            "StationName": "Galileo",
        },
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert state.snapshot.location.system == "Sol"
    assert state.snapshot.location.body == "Earth"
    assert state.snapshot.location.station == "Galileo"


@pytest.mark.asyncio
async def test_fsd_jump_increments_count(bus_and_state):
    bus, state = bus_and_state
    await bus.publish(Event(
        topic="journal.fsdjump",
        data={"StarSystem": "Alpha Centauri", "DistFromStarLs": 4.2},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert state.snapshot.navigation.jump_count == 1
    assert state.snapshot.location.system == "Alpha Centauri"


@pytest.mark.asyncio
async def test_rank_update(bus_and_state):
    bus, state = bus_and_state
    await bus.publish(Event(
        topic="journal.rank",
        data={"Combat": 5, "Trade": 3, "Explore": 8},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert state.snapshot.ranks.combat == 5
    assert state.snapshot.ranks.explore == 8


@pytest.mark.asyncio
async def test_non_journal_events_ignored(bus_and_state):
    bus, state = bus_and_state
    state._state.commander.name = "Original"
    await bus.publish(Event(
        topic="journal.commander",
        data={"Name": "ShouldNotUpdate"},
        source="api",  # not "journal"
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    assert state.snapshot.commander.name == "Original"


@pytest.mark.asyncio
async def test_snapshot_dict_serializable(bus_and_state):
    bus, state = bus_and_state
    await bus.publish(Event(
        topic="journal.loadgame",
        data={"Commander": "TestCmdr", "Credits": 500},
        source="journal",
    ))

    bus._running = True
    task = asyncio.create_task(bus.run())
    await asyncio.sleep(0.05)
    bus.stop()
    await task

    d = state.snapshot_dict()
    assert isinstance(d, dict)
    assert d["commander"]["name"] == "TestCmdr"
    assert "timestamp" in d
