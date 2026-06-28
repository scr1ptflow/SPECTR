import json
import os
import sys

from fastapi import FastAPI, HTTPException, Query as Q
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from blackbox.formatter import fmt_date, fmt_time, fmt_event
from webui._utils import read_config, resolve_db, get_conn

SHIP_EVENTS = frozenset({
    "FSDJump", "StartJump", "SupercruiseEntry", "SupercruiseExit",
    "Docked", "Undocked", "DockingGranted",
    "Touchdown", "Liftoff", "ApproachBody", "LeaveBody",
    "Bounty", "Died", "Resurrect", "RedeemVoucher",
    "MarketBuy", "MarketSell", "BuyTradeData",
    "MaterialCollected", "MaterialDiscarded", "MaterialDiscovered",
    "MaterialTrade", "MiningRefined",
    "ModuleBuy", "ModuleSell", "ModuleStore",
    "Repair", "Refuel", "BuyAmmo", "FuelScoop",
    "VehicleSwitch",
    "Scan", "SAAScanComplete", "CodexEntry",
    "CollectCargo", "EjectCargo", "LaunchDrone",
    "EngineerCraft",
})

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Blackbox")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/stats")
def api_stats(db: str = Q(None, description="DB path override")):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        status_count = conn.execute("SELECT COUNT(*) FROM status").fetchone()[0]
        event_types = conn.execute("SELECT COUNT(DISTINCT event) FROM events").fetchone()[0]
        types = conn.execute(
            "SELECT event, COUNT(*) as cnt FROM events GROUP BY event ORDER BY cnt DESC"
        ).fetchall()
        return {
            "ok": True,
            "events": events,
            "status": status_count,
            "event_types": event_types,
            "types": [{"event": r["event"], "count": r["cnt"]} for r in types],
        }
    finally:
        conn.close()


@sub_app.get("/api/log")
def api_log(
    limit: int = Q(100, ge=1, le=1000, description="Max entries"),
    offset: int = Q(0, ge=0, description="Offset"),
    db: str = Q(None, description="DB path override"),
):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT timestamp, event, raw_json FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        entries = []
        for ts, event, raw in rows:
            if event not in SHIP_EVENTS:
                continue
            data = json.loads(raw)
            formatted = fmt_event(data)
            entries.append({
                "timestamp": ts,
                "date": fmt_date(ts),
                "time": fmt_time(ts),
                "event": event,
                "formatted": formatted,
            })
        return {"ok": True, "total": len(entries), "entries": entries}
    finally:
        conn.close()


@sub_app.get("/api/events")
def api_events(
    type: str = Q(None, alias="event", description="Filter by event type"),
    limit: int = Q(100, ge=1, le=1000, description="Max rows"),
    offset: int = Q(0, ge=0, description="Offset"),
    db: str = Q(None, description="DB path override"),
):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        if type:
            total = conn.execute(
                "SELECT COUNT(*) FROM events WHERE event = ?", (type,)
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM events WHERE event = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (type, limit, offset),
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return {
            "ok": True,
            "total": total,
            "events": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@sub_app.get("/api/event-types")
def api_event_types(db: str = Q(None, description="DB path override")):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        types = conn.execute(
            "SELECT event, COUNT(*) as cnt FROM events GROUP BY event ORDER BY cnt DESC"
        ).fetchall()
        return {"ok": True, "types": [{"event": r["event"], "count": r["cnt"]} for r in types]}
    finally:
        conn.close()


@sub_app.get("/api/status/latest")
def api_status_latest(db: str = Q(None, description="DB path override")):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT timestamp, raw_json FROM status ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no status snapshots"}
        return {
            "ok": True,
            "timestamp": row["timestamp"],
            "data": json.loads(row["raw_json"]),
        }
    finally:
        conn.close()


@sub_app.post("/api/query")
def api_query(body: dict, db: str = Q(None, description="DB path override")):
    sql = body.get("sql", "").strip()
    if not sql:
        raise HTTPException(400, detail="sql is required")
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return {
            "ok": True,
            "columns": columns,
            "rows": [[None if v is None else v for v in row] for row in rows],
            "total": len(rows),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()
