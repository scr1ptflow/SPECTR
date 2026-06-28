import json
import os
import sys

from fastapi import FastAPI, Query as Q
from fastapi.responses import HTMLResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from blackbox.formatter import fmt_date, fmt_time, fmt_captains_log
from webui._utils import resolve_db, get_conn

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Captain's Log")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/captains-log")
def api_captains_log(
    date: str = Q(None, description="Filter by date YYYY-MM-DD"),
    db: str = Q(None, description="DB path override"),
):
    db_path = _resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT timestamp, event, raw_json FROM events ORDER BY timestamp"
        ).fetchall()

        days: dict[str, list] = {}
        all_dates: set[str] = set()
        for ts, event, raw in rows:
            d = fmt_date(ts)
            all_dates.add(d)
            if date and d != date:
                continue
            data = json.loads(raw)
            formatted = fmt_captains_log(data)
            if formatted is None:
                continue
            if d not in days:
                days[d] = []
            days[d].append({
                "time": fmt_time(ts),
                "event": event,
                "formatted": formatted,
            })

        return {
            "ok": True,
            "days": [{"date": d, "events": days[d]} for d in sorted(days, reverse=True)],
            "all_dates": sorted(all_dates, reverse=True),
        }
    finally:
        conn.close()
