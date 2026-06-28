import json
import os
import glob
import re
from datetime import datetime, timezone


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
    # Kill missions
    kt = m.get("KillTarget")
    if kt:
        return {"current": m.get("KillCount") or 0, "target": kt, "type": "Kills"}
    # Passenger missions
    pt = m.get("PassengerTarget")
    if pt:
        return {"current": m.get("PassengerCount") or 0, "target": pt, "type": "Passengers"}
    # Delivery/mining missions with a Count
    ct = m.get("Count")
    if ct:
        name = (m.get("Name_Localised") or m.get("Name", "")).lower()
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


def _read_journal_dir(config_path: str | None = None) -> str | None:
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


def _iter_journal_events(journal_dir: str):
    pattern = os.path.join(journal_dir, "Journal.*.log")
    for fpath in sorted(glob.glob(pattern)):
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def get_missions(journal_dir: str) -> dict:
    result = {
        "active": [],
        "failed": [],
        "complete": [],
    }

    snapshot_ts = None
    kill_lookup = {}  # MissionID -> latest kill count from MissionKill events

    for ev in _iter_journal_events(journal_dir):
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
    for ev in _iter_journal_events(journal_dir):
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

    # apply any MissionKill updates to active missions
    for m in result["active"]:
        mid = m["id"]
        if mid in kill_lookup:
            m["kill_count"] = kill_lookup[mid]

    return result
