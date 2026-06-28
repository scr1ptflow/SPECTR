"""Simple persistent storage for blackbox journal events."""

import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def close(self):
        self.conn.close()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                event        TEXT NOT NULL,
                raw_json     TEXT NOT NULL,
                journal_file TEXT,
                line_number  INTEGER,
                ingested_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                UNIQUE(journal_file, line_number)
            );
            CREATE INDEX IF NOT EXISTS idx_events_event     ON events(event);
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);

            CREATE TABLE IF NOT EXISTS status (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                raw_json     TEXT NOT NULL,
                ingested_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
        """)
        self.conn.commit()

    def insert_event(self, timestamp: str, event: str, raw_json: str,
                     journal_file: str | None = None, line_number: int | None = None) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO events (timestamp, event, raw_json, journal_file, line_number) VALUES (?, ?, ?, ?, ?)",
            (timestamp, event, raw_json, journal_file, line_number),
        )
        self.conn.commit()
        return cur.lastrowid

    def insert_status(self, timestamp: str, raw_json: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO status (timestamp, raw_json) VALUES (?, ?)",
            (timestamp, raw_json),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_stats(self) -> dict:
        return {
            "events": self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "status": self.conn.execute("SELECT COUNT(*) FROM status").fetchone()[0],
            "event_types": self.conn.execute("SELECT COUNT(DISTINCT event) FROM events").fetchone()[0],
        }

    def get_event_types(self) -> list[tuple[str, int]]:
        cur = self.conn.execute(
            "SELECT event, COUNT(*) as cnt FROM events GROUP BY event ORDER BY cnt DESC",
        )
        return cur.fetchall()
