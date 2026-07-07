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
            line_number INTEGER NOT NULL,
            UNIQUE(timestamp)
        )"""
    )

    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event ON events(event)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    conn.commit()


class Store:
    _schema_initialized: set[str] = set()

    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        _ensure_db(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        if db_path not in Store._schema_initialized:
            _init_schema(self.conn)
            Store._schema_initialized.add(db_path)

    def insert_event(self, ts, event, system, raw_json, fname, line_num):
        self.conn.execute(
            "INSERT OR IGNORE INTO events (event, system, raw_json, timestamp, journal_file, line_number) VALUES (?, ?, ?, ?, ?, ?)",
            (event, system, raw_json, ts, fname, line_num),
        )

    def insert_status(self, ts, system, raw_json):
        self.conn.execute(
            "INSERT OR IGNORE INTO status (timestamp, system, raw_json, journal_file, line_number) VALUES (?, ?, ?, 'Status.json', 0)",
            (ts, system, raw_json),
        )

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
