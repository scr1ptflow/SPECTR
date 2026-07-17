"""Tests for the database layer."""

import tempfile
import pytest_asyncio
import pytest
from pathlib import Path

from bridge_core.database.db import Database


@pytest_asyncio.fixture
async def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    database = Database(db_path)
    await database.connect()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_create_session(db):
    session_id = await db.create_session("TestCmdr", "python", "Sol", 1000000)
    assert session_id > 0

    session = await db.get_session(session_id)
    assert session is not None
    assert session["commander_name"] == "TestCmdr"
    assert session["ship_type"] == "python"
    assert session["starting_system"] == "Sol"
    assert session["credits_start"] == 1000000


@pytest.mark.asyncio
async def test_end_session(db):
    session_id = await db.create_session("TestCmdr", "python", "Sol", 1000000)
    await db.end_session(session_id, credits_end=1100000, jumps=5)

    session = await db.get_session(session_id)
    assert session["ended_at"] is not None
    assert session["credits_end"] == 1100000
    assert session["jumps"] == 5


@pytest.mark.asyncio
async def test_add_visited_system(db):
    session_id = await db.create_session("TestCmdr", "python", "Sol", 1000000)
    sys_id = await db.add_visited_system(
        session_id, "Alpha Centauri", 12345,
        faction="Federation", economy="Industrial",
    )
    assert sys_id > 0

    systems = await db.get_visited_systems(session_id)
    assert len(systems) == 1
    assert systems[0]["system_name"] == "Alpha Centauri"
    assert systems[0]["faction"] == "Federation"


@pytest.mark.asyncio
async def test_add_exploration_entry(db):
    session_id = await db.create_session("TestCmdr", "python", "Sol", 1000000)
    entry_id = await db.add_exploration_entry(
        session_id, "Sol", "Earth", "Earthlike body", 25000,
    )
    assert entry_id > 0

    log = await db.get_exploration_log(session_id)
    assert len(log) == 1
    assert log[0]["body_name"] == "Earth"
    assert log[0]["estimated_value"] == 25000


@pytest.mark.asyncio
async def test_add_organic_entry(db):
    session_id = await db.create_session("TestCmdr", "python", "Sol", 1000000)
    entry_id = await db.add_organic_entry(
        session_id, "Sol", "Earth",
        "Stratum Tectonicas", "Purple", "Stratum",
    )
    assert entry_id > 0


@pytest.mark.asyncio
async def test_settings(db):
    await db.set_setting("journal_path", "/some/path")
    value = await db.get_setting("journal_path")
    assert value == "/some/path"

    await db.set_setting("journal_path", "/new/path")
    value = await db.get_setting("journal_path")
    assert value == "/new/path"

    value = await db.get_setting("nonexistent", "default")
    assert value == "default"


@pytest.mark.asyncio
async def test_get_sessions(db):
    await db.create_session("Cmdr1", "python", "Sol", 1000000)
    await db.create_session("Cmdr2", "anaconda", "Sol", 2000000)

    sessions = await db.get_sessions()
    assert len(sessions) == 2
