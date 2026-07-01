import csv
import io
import json
import os
import shutil
import sqlite3

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse

from long_range_sensor import journal as lrs_journal
from webui._utils import read_config, find_journal_dir, get_latest_journal

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "navigation_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "route.csv")
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blackbox.db")

sub_app = FastAPI(title="SPECTR Navigation")


def _read_csv(path: str) -> tuple:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return fieldnames, rows


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/system")
def api_system():
    jdir = find_journal_dir() or read_config().get("journal_path", "")
    if not jdir:
        return {"ok": False, "error": "no journal directory"}
    jfile = get_latest_journal(jdir)
    if not jfile:
        return {"ok": False, "error": "no journal file"}
    sys_name = lrs_journal.read_current_system(jfile)
    if not sys_name:
        return {"ok": False, "error": "could not determine system"}
    return {"ok": True, "system": sys_name}


@sub_app.get("/api/cached")
def api_cached():
    if not os.path.isfile(CACHE_FILE):
        return {"ok": False, "cached": False}
    try:
        columns, rows = _read_csv(CACHE_FILE)
        return {
            "ok": True,
            "cached": True,
            "file": "route.csv",
            "total": len(rows),
            "columns": columns,
            "rows": rows,
        }
    except Exception as e:
        return {"ok": False, "cached": False, "error": str(e)}


@sub_app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        return {"ok": False, "error": "Only CSV files are accepted"}
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        contents = await file.read()
        with open(CACHE_FILE, "wb") as f:
            f.write(contents)
        columns, rows = _read_csv(CACHE_FILE)
        return {
            "ok": True,
            "file": "route.csv",
            "total": len(rows),
            "columns": columns,
            "rows": rows,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@sub_app.delete("/api/upload")
def api_upload_delete():
    try:
        if os.path.isfile(CACHE_FILE):
            os.remove(CACHE_FILE)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@sub_app.get("/api/route")
def api_route(path: str = Query(None, description="Path to spansh CSV file")):
    if not path:
        config = read_config()
        path = config.get("navigation", {}).get("csv_path", "")

    if not path or not os.path.isfile(path):
        return {"ok": False, "error": "No CSV file specified. Provide a ?path= query param or set navigation.csv_path in config.json"}

    try:
        columns, rows = _read_csv(path)
        info = os.path.basename(path)
        return {
            "ok": True,
            "file": info,
            "total": len(rows),
            "columns": columns,
            "rows": rows,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@sub_app.get("/api/exo-status")
def api_exo_status(keys: str = Query("", description="Comma-separated system||body keys (or just system for system-level)")):
    if not keys:
        return {"ok": False, "error": "no keys specified"}
    key_list = [k.strip() for k in keys.split(",") if k.strip()]
    if not os.path.isfile(_DB_PATH):
        return {"ok": True, "status": {k: "not_visited" for k in key_list}}

    try:
        conn = sqlite3.connect(_DB_PATH)

        # Collect unique system names and body names
        systems = set()
        body_pairs = {}  # body_name -> list of keys
        for k in key_list:
            parts = k.split("||", 1)
            sys_name = parts[0]
            systems.add(sys_name)
            if len(parts) > 1 and parts[1]:
                body_name = parts[1]
                body_pairs.setdefault(body_name, []).append(k)

        # Check FSDJump events — which systems have been visited
        visited_systems = set()
        for sys_name in systems:
            row = conn.execute(
                "SELECT 1 FROM events WHERE event IN ('FSDJump', 'Location', 'CarrierJump') AND system = ? LIMIT 1",
                (sys_name,)
            ).fetchone()
            if row:
                visited_systems.add(sys_name)

        # Check Scan events — which bodies have been scanned
        scanned_bodies = {}
        rows = conn.execute(
            "SELECT raw_json FROM events WHERE event = 'Scan' AND raw_json LIKE '%\"BodyName\":%'"
        ).fetchall()
        for (raw,) in rows:
            for bname, keys_list in body_pairs.items():
                if '"' + bname + '"' in raw:
                    try:
                        data = json.loads(raw)
                        if data.get("BodyName") == bname:
                            scanned_bodies[bname] = True
                    except json.JSONDecodeError:
                        pass

        # Check SAASignalsFound — biological signals per body
        bio_bodies = {}
        rows = conn.execute(
            "SELECT raw_json FROM events WHERE event = 'SAASignalsFound' AND raw_json LIKE '%\"BodyName\":%'"
        ).fetchall()
        for (raw,) in rows:
            for bname, keys_list in body_pairs.items():
                if '"' + bname + '"' in raw:
                    try:
                        data = json.loads(raw)
                        if data.get("BodyName") == bname:
                            bio_count = 0
                            for sig in data.get("Signals", []):
                                if "Biological" in sig.get("Type", ""):
                                    bio_count += sig.get("Count", 0)
                            bio_bodies[bname] = bio_count
                    except json.JSONDecodeError:
                        pass

        conn.close()

        # Compute status for each key
        results = {}
        for k in key_list:
            parts = k.split("||", 1)
            sys_name = parts[0]
            has_body = len(parts) > 1 and parts[1]

            if not has_body:
                # System-level key
                results[k] = "complete" if sys_name in visited_systems else "not_visited"
            else:
                body_name = parts[1]
                scanned = scanned_bodies.get(body_name, False)
                bio_count = bio_bodies.get(body_name, 0)
                sys_visited = sys_name in visited_systems

                if scanned:
                    if bio_count > 0:
                        results[k] = "partial"
                    else:
                        results[k] = "complete"
                elif sys_visited:
                    results[k] = "partial"
                else:
                    results[k] = "not_visited"

        return {"ok": True, "status": results}
    except Exception:
        return {"ok": False, "error": "error querying exo status"}
