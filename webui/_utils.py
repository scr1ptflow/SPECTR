import glob
import json
import os
import sqlite3
from functools import lru_cache

from blackbox import _PROJECT_DIR
from long_range_sensor import journal

CONFIG_PATH = os.path.join(str(_PROJECT_DIR), "config.json")


@lru_cache(maxsize=1)
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
    return os.path.join(str(_PROJECT_DIR), "blackbox", "blackbox.db")


def get_conn(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_journal(journal_dir: str) -> str | None:
    """Return the most recent Journal.*.log in the given directory."""
    if not journal_dir or not os.path.isdir(journal_dir):
        return None
    files = sorted(glob.glob(os.path.join(journal_dir, "Journal.*.log")), reverse=True)
    return files[0] if files else None


def find_journal_dir(config_path: str | None = None) -> str | None:
    """Find the Elite Dangerous journal directory.

    Checks (in order): config.json journal_path, ED_JOURNAL_DIR env var,
    default Steam Proton paths.
    """
    cfg = read_config() if not config_path else None
    if cfg:
        path = cfg.get("journal_path", "")
        if path and os.path.isdir(path):
            return path
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        path = cfg.get("journal_path", "")
        if path and os.path.isdir(path):
            return path
    env = os.environ.get("ED_JOURNAL_DIR", "")
    if env and os.path.isdir(env):
        return env
    candidates = [
        os.path.join(os.path.expanduser("~"), ".steam", "steam", "steamapps", "compatdata", "359320", "pfx", "drive_c", "users", "steamuser", "Saved Games", "Frontier Developments", "Elite Dangerous"),
        os.path.join(os.path.expanduser("~"), ".local", "share", "Steam", "steamapps", "compatdata", "359320", "pfx", "drive_c", "users", "steamuser", "Saved Games", "Frontier Developments", "Elite Dangerous"),
    ]
    for c in candidates:
        if os.path.isdir(c) and glob.glob(os.path.join(c, "Journal.*.log")):
            return c
    return None


def get_system():
    config = read_config()
    jdir = find_journal_dir(CONFIG_PATH) or config.get("journal_path", "")
    jfile = get_latest_journal(jdir)
    if not jfile:
        return None
    return journal.read_current_system(jfile)
