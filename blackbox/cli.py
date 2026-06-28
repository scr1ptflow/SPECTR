"""CLI for blackbox flight recorder."""

import argparse
import json
import logging
import os
import signal
import sys
from pathlib import Path

from . import __version__
from .formatter import fmt_date, fmt_time, fmt_event
from .store import Store
from .recorder import Recorder

DB_DEFAULT = "blackbox.db"
logger = logging.getLogger("blackbox")


def _find_journal_dir() -> Path | None:
    candidates = [
        Path.home()
        / ".steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser"
        / "Saved Games/Frontier Developments/Elite Dangerous",
        Path.home()
        / ".local/share/Steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser"
        / "Saved Games/Frontier Developments/Elite Dangerous",
    ]
    env_dir = os.environ.get("ED_JOURNAL_DIR", "")
    if env_dir:
        candidates.append(Path(env_dir))
    for p in candidates:
        if p.exists() and list(p.glob("Journal.*.log")):
            return p
    return None


def cmd_record(args):
    journal_dir = args.journal_dir
    if not journal_dir:
        found = _find_journal_dir()
        if not found:
            logger.error(
                "Journal directory not found.\n"
                "  Use --journal-dir or set ED_JOURNAL_DIR env var."
            )
            sys.exit(1)
        journal_dir = found

    store = Store(args.db)
    recorder = Recorder(store, Path(journal_dir), status_interval=args.status_interval)

    logger.info("Recording from %s", journal_dir)
    recorder.catch_up()
    logger.info("Catch-up complete. %d events recorded.", store.get_stats()["events"])

    if not args.once:
        recorder.watch()
        try:
            signal.pause()
        except KeyboardInterrupt:
            logger.info("Stopped.")
        finally:
            recorder.stop()
    store.close()


def cmd_summary(args):
    store = Store(args.db)
    try:
        stats = store.get_stats()
        print(f"Events:       {stats['events']}")
        print(f"Status snaps: {stats['status']}")
        print(f"Event types:  {stats['event_types']}")
        print()
        for evt, cnt in store.get_event_types():
            print(f"  {evt:<30} {cnt}")
    finally:
        store.close()


def cmd_query(args):

    store = Store(args.db)
    try:
        cur = store.conn.execute(args.sql)
        rows = cur.fetchall()
        if not rows:
            print("(no results)")
            return
        headers = [desc[0] for desc in cur.description]
        sep = "-+-".join("-" * len(h) for h in headers)
        print(" | ".join(headers))
        print(sep)
        for row in rows:
            print(" | ".join(str(v) if v is not None else "NULL" for v in row))
        print(f"\n({len(rows)} rows)")
    finally:
        store.close()


def cmd_log(args):
    store = Store(args.db)
    try:
        cur = store.conn.execute(
            "SELECT timestamp, event, raw_json FROM events ORDER BY timestamp"
        )
        rows = cur.fetchall()
        if not rows:
            print("No events recorded.")
            return

        current_date = ""
        for ts, event, raw in rows:
            line = fmt_event(json.loads(raw))
            if line is None:
                continue
            date = fmt_date(ts)
            if date != current_date:
                current_date = date
                print(f"\n=== {date} ===")
            print(f"  {fmt_time(ts)}  {line}")
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser(
        prog="blackbox",
        description="Black Box flight recorder for Elite Dangerous",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")

    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="Record journal events to the database")
    rec.add_argument("--journal-dir", "-j", help="Journal directory (auto-detected if omitted)")
    rec.add_argument("--db", default=DB_DEFAULT, help=f"Database path (default: {DB_DEFAULT})")
    rec.add_argument("--status-interval", type=float, default=5.0, help="Status.json poll interval in seconds")
    rec.add_argument("--once", "-1", action="store_true", help="Read existing files once, then exit")
    rec.set_defaults(func=cmd_record)

    sum_ = sub.add_parser("summary", help="Show recorded data summary")
    sum_.add_argument("--db", default=DB_DEFAULT, help="Database path")
    sum_.set_defaults(func=cmd_summary)

    qry = sub.add_parser("query", help="Run a SQL query against the database")
    qry.add_argument("--db", default=DB_DEFAULT, help="Database path")
    qry.add_argument("--sql", "-q", required=True, help="SQL query to execute")
    qry.set_defaults(func=cmd_query)

    log_ = sub.add_parser("log", help="Show a readable captain's log")
    log_.add_argument("--db", default=DB_DEFAULT, help="Database path")
    log_.set_defaults(func=cmd_log)

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    args.func(args)


if __name__ == "__main__":
    main()
