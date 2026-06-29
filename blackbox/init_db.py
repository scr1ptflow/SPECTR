#!/usr/bin/env python3
"""Initialize blackbox.db if it doesn't exist."""

import sys
from pathlib import Path

from blackbox.store import Store

DB_PATH = "blackbox.db"


def init():
    db_path = str(Path(__file__).parent / DB_PATH)

    if not Path(db_path).exists():
        print(f"Creating {db_path}...")
        store = Store(db_path)
        store._init_schema()
        store.close()
        print(f"✓ Database initialized at {db_path}")
    else:
        print(f"✓ {db_path} already exists")
    return True


if __name__ == "__main__":
    sys.exit(0 if init() else 1)
