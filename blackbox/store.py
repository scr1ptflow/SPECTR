import json
import sqlite3
from pathlib import Path


def _ensure_db(db_path):
    """Ensure the database file exists, creating it if necessary."""
    db_path = Path(db_path)
    if not db_path.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Creating new database: {db_path}")
        return True
    return False


def _init_schema(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            system TEXT NOT NULL DEFAULT '',
            raw_json TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            journal_file TEXT NOT NULL,
            line_number INTEGER NOT NULL,
            UNIQUE(journal_file, line_number)
        )"""
    )

    conn.execute(
        """CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            system TEXT NOT NULL DEFAULT '',
            raw_json TEXT NOT NULL,
            journal_file TEXT NOT NULL,
            line_number INTEGER NOT NULL
        )"""
    )
    conn.commit()


class Store:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        _ensure_db(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        _init_schema(self.conn)

    def _init_schema(self):
        _init_schema(self.conn)

    def insert_event(self, ts, event, line, fname, line_num):
        data = json.loads(line)
        system = data.get("StarSystem") or data.get("System") or ""
        self.conn.execute(
            "INSERT OR IGNORE INTO events (event, system, raw_json, timestamp, journal_file, line_number) VALUES (?, ?, ?, ?, ?, ?)",
            (event, system, line, ts, fname, line_num),
        )
        self.conn.commit()

    def insert_status(self, ts, raw):
        data = json.loads(raw)
        system = data.get("StarSystem") or data.get("System") or ""
        self.conn.execute(
            "INSERT INTO status (timestamp, system, raw_json, journal_file, line_number) VALUES (?, ?, ?, 'Status.json', 0)",
            (ts, system, raw),
        )
        self.conn.commit()

    def get_stats(self):
        events = self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        status = self.conn.execute("SELECT COUNT(*) FROM status").fetchone()[0]
        event_types = self.conn.execute(
            "SELECT COUNT(DISTINCT event) FROM events"
        ).fetchone()[0]
        return {"events": events, "status": status, "event_types": event_types}

    def get_event_types(self):
        return self.conn.execute(
            "SELECT event, COUNT(*) as cnt FROM events GROUP BY event ORDER BY cnt DESC"
        ).fetchall()

    def close(self):
        self.conn.close()


def init_db(db_path):
    if _ensure_db(db_path):
        conn = sqlite3.connect(db_path)
        _init_schema(conn)
        conn.close()
