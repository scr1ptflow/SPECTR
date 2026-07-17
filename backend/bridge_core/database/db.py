"""Database layer for Elite Bridge Core.

SQLite-based storage for sessions, history, and persistent state.
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_seconds INTEGER DEFAULT 0,
    commander_name TEXT DEFAULT '',
    ship_type TEXT DEFAULT '',
    starting_system TEXT DEFAULT '',
    ending_system TEXT DEFAULT '',
    credits_start INTEGER DEFAULT 0,
    credits_end INTEGER DEFAULT 0,
    jumps INTEGER DEFAULT 0,
    distance_ly REAL DEFAULT 0.0,
    bodies_scanned INTEGER DEFAULT 0,
    organic_scans INTEGER DEFAULT 0,
    missions_completed INTEGER DEFAULT 0,
    missions_failed INTEGER DEFAULT 0,
    events_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS visited_systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    system_name TEXT NOT NULL,
    system_address INTEGER,
    faction TEXT DEFAULT '',
    government TEXT DEFAULT '',
    economy TEXT DEFAULT '',
    security TEXT DEFAULT '',
    population INTEGER DEFAULT 0,
    arrived_at TEXT NOT NULL,
    departed_at TEXT
);

CREATE TABLE IF NOT EXISTS exploration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    system_name TEXT NOT NULL,
    body_name TEXT NOT NULL,
    body_class TEXT DEFAULT '',
    scanned_at TEXT NOT NULL,
    estimated_value INTEGER DEFAULT 0,
    mapped INTEGER DEFAULT 0,
    first_discovery INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS organic_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    system_name TEXT NOT NULL,
    body_name TEXT NOT NULL,
    species TEXT NOT NULL,
    variant TEXT DEFAULT '',
    genus TEXT DEFAULT '',
    scanned_at TEXT NOT NULL,
    scan_type TEXT DEFAULT 'Sample'
);

CREATE TABLE IF NOT EXISTS mission_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    mission_id INTEGER,
    mission_type TEXT DEFAULT '',
    expiry TEXT DEFAULT '',
    accepted_at TEXT NOT NULL,
    completed_at TEXT,
    abandoned_at TEXT,
    failed_at TEXT,
    outcome TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


class Database:
    """Async SQLite database for persistent storage."""

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the database connection and create tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        log.info("Database connected: %s", self.db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def create_session(self, commander: str, ship: str, system: str, credits: int) -> int:
        """Create a new session record and return its ID."""
        cursor = await self._db.execute(
            """INSERT INTO sessions (started_at, commander_name, ship_type,
               starting_system, credits_start)
               VALUES (datetime('now'), ?, ?, ?, ?)""",
            (commander, ship, system, credits),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def end_session(self, session_id: int, **kwargs) -> None:
        """Update a session with ending data."""
        sets = ["ended_at = datetime('now')"]
        params = []
        for key, value in kwargs.items():
            sets.append(f"{key} = ?")
            params.append(value)
        params.append(session_id)
        await self._db.execute(
            f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?",
            params,
        )
        await self._db.commit()

    async def add_visited_system(
        self, session_id: int, system: str, address: int, **kwargs
    ) -> int:
        cursor = await self._db.execute(
            """INSERT INTO visited_systems (session_id, system_name, system_address,
               arrived_at, faction, government, economy, security, population)
               VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, ?)""",
            (
                session_id, system, address,
                kwargs.get("faction", ""),
                kwargs.get("government", ""),
                kwargs.get("economy", ""),
                kwargs.get("security", ""),
                kwargs.get("population", 0),
            ),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def add_exploration_entry(
        self, session_id: int, system: str, body: str, body_class: str, value: int
    ) -> int:
        cursor = await self._db.execute(
            """INSERT INTO exploration_log (session_id, system_name, body_name,
               body_class, scanned_at, estimated_value)
               VALUES (?, ?, ?, ?, datetime('now'), ?)""",
            (session_id, system, body, body_class, value),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def add_organic_entry(
        self, session_id: int, system: str, body: str,
        species: str, variant: str, genus: str, scan_type: str = "Sample"
    ) -> int:
        cursor = await self._db.execute(
            """INSERT INTO organic_log (session_id, system_name, body_name,
               species, variant, genus, scanned_at, scan_type)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)""",
            (session_id, system, body, species, variant, genus, scan_type),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_sessions(self, limit: int = 50) -> list[dict]:
        """Get recent sessions."""
        cursor = await self._db.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_session(self, session_id: int) -> dict | None:
        """Get a single session by ID."""
        cursor = await self._db.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_visited_systems(self, session_id: int) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM visited_systems WHERE session_id = ? ORDER BY arrived_at",
            (session_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def get_exploration_log(self, session_id: int) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT * FROM exploration_log WHERE session_id = ? ORDER BY scanned_at",
            (session_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def get_setting(self, key: str, default: str = "") -> str:
        cursor = await self._db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        await self._db.execute(
            """INSERT INTO settings (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET value = excluded.value,
               updated_at = excluded.updated_at""",
            (key, value),
        )
        await self._db.commit()
