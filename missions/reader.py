import json
import glob
import os
import re
import sqlite3
from datetime import datetime, timezone

from blackbox import _PROJECT_DIR


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _remaining_seconds(expiry: str | None) -> float | None:
    if not expiry:
        return None
    try:
        exp = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        delta = exp - datetime.now(timezone.utc)
        return max(0.0, delta.total_seconds())
    except (ValueError, AttributeError):
        return None


def _mission_progress(m: dict) -> dict:
    """Detect progress from mission fields."""
    kt = m.get("kill_target")
    if kt:
        return {"current": m.get("kill_count") or 0, "target": kt, "type": "Kills"}
    pt = m.get("passenger_target")
    if pt:
        return {"current": m.get("passenger_count") or 0, "target": pt, "type": "Passengers"}
    ct = m.get("count")
    if ct:
        name = (m.get("name") or "").lower()
        if "mining" in name or "mine " in name:
            return {"current": 0, "target": ct, "type": "Tons Mined"}
        return {"current": 0, "target": ct, "type": "Delivered"}
    return {}


def _kill_target(name: str) -> int | None:
    m = re.search(r"\d+", name or "")
    return int(m.group()) if m else None


def _ensure_kill_data(m: dict, ev: dict):
    kc = ev.get("KillCount")
    if kc is not None:
        m["kill_count"] = kc
    kt = ev.get("KillTarget")
    if kt is not None:
        m["kill_target"] = kt
    elif kc is not None:
        target = _kill_target(m.get("name", ""))
        if target:
            m["kill_target"] = target


def _iter_journal_events(journal_dir: str):
    files = sorted(glob.glob(os.path.join(journal_dir, "Journal.*.log")))
    for fpath in files:
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _iter_db_events(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        for row in conn.execute("SELECT raw_json FROM events ORDER BY timestamp"):
            try:
                yield json.loads(row["raw_json"])
            except json.JSONDecodeError:
                continue
    finally:
        conn.close()


def _normalize_db_path(db_path: str | None) -> str | None:
    if db_path:
        return db_path
    default = str(_PROJECT_DIR / "blackbox" / "blackbox.db")
    return default if os.path.isfile(default) else None


def get_missions(journal_dir: str, db_path: str | None = None) -> dict:
    result = {
        "active": [],
        "failed": [],
        "complete": [],
    }

    resolved = _normalize_db_path(db_path)
    if resolved:
        all_events = list(_iter_db_events(resolved))
    else:
        all_events = list(_iter_journal_events(journal_dir))

    snapshot_ts = None
    kill_lookup = {}

    for ev in all_events:
        if ev.get("event") == "MissionKill":
            mid = ev.get("MissionID")
            kc = ev.get("KillCount")
            if mid is not None and kc is not None:
                kill_lookup[mid] = kc

        elif ev.get("event") == "Missions":
            snapshot_ts = _parse_ts(ev.get("timestamp", ""))
            result["active"] = []
            for m in ev.get("Active", []):
                entry = {
                    "id": m.get("MissionID"),
                    "name": m.get("Name_Localised") or m.get("Name", "?"),
                    "expires": m.get("Expiry"),
                    "remaining": _remaining_seconds(m.get("Expiry")),
                    "destination_system": m.get("DestinationSystem"),
                    "destination_station": m.get("DestinationStation"),
                    "reward": m.get("Reward"),
                    "kill_count": m.get("KillCount"),
                    "kill_target": m.get("KillTarget"),
                    "passenger_count": m.get("PassengerCount"),
                    "passenger_target": m.get("PassengerTarget"),
                    "count": m.get("Count"),
                }
                _ensure_kill_data(entry, m)
                entry["progress"] = _mission_progress(entry)
                result["active"].append(entry)
            result["failed"] = [
                {"id": m.get("MissionID"), "name": m.get("Name_Localised") or m.get("Name", "?")}
                for m in ev.get("Failed", [])
            ]
            result["complete"] = [
                {"id": m.get("MissionID"), "name": m.get("Name_Localised") or m.get("Name", "?")}
                for m in ev.get("Complete", [])
            ]

    if snapshot_ts is None:
        return result

    # apply lifecycle events after the snapshot
    for ev in all_events:
        ts = _parse_ts(ev.get("timestamp", ""))
        if ts <= snapshot_ts:
            continue
        mid = ev.get("MissionID")
        name = ev.get("Name_Localised") or ev.get("Name", "?")
        e = ev.get("event")
        if e == "MissionAccepted":
            entry = {
                "id": mid,
                "name": name,
                "expires": ev.get("Expiry"),
                "remaining": _remaining_seconds(ev.get("Expiry")),
                "destination_system": ev.get("DestinationSystem"),
                "destination_station": ev.get("DestinationStation"),
                "reward": ev.get("Reward"),
                "kill_count": None,
                "kill_target": ev.get("KillTarget"),
                "passenger_count": ev.get("PassengerCount"),
                "passenger_target": ev.get("PassengerTarget"),
                "count": ev.get("Count"),
            }
            _ensure_kill_data(entry, ev)
            entry["progress"] = _mission_progress(entry)
            result["active"].append(entry)
        elif e == "MissionCompleted":
            result["active"] = [m for m in result["active"] if m["id"] != mid]
            result["complete"].append({"id": mid, "name": name})
        elif e in ("MissionFailed", "MissionAbandoned"):
            result["active"] = [m for m in result["active"] if m["id"] != mid]
            result["failed"].append({"id": mid, "name": name})
        elif e == "MissionRedirected":
            for m in result["active"]:
                if m["id"] == mid:
                    m["destination_system"] = ev.get("NewDestinationSystem", m.get("destination_system"))
                    m["destination_station"] = ev.get("NewDestinationStation", m.get("destination_station"))

    for m in result["active"]:
        mid = m["id"]
        if mid in kill_lookup:
            m["kill_count"] = kill_lookup[mid]

    return result
