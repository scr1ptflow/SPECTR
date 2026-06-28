import json
import os
import sqlite3

from long_range_sensor import journal

DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(DIR, "config.json")


def read_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def resolve_db(db_path: str | None = None) -> str:
    if db_path:
        return db_path
    config = read_config()
    cfg_db = config.get("blackbox", {}).get("db_path")
    if cfg_db:
        return cfg_db
    return os.path.join(DIR, "blackbox.db")


def get_conn(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_system():
    config = read_config()
    jdir = config.get("journal_path", "")
    jfile = journal.get_latest_journal(jdir)
    if not jfile:
        return None
    return journal.read_current_system(jfile)
