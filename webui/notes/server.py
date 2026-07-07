import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse

from webui._utils import resolve_db, get_conn

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Notes")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/notes")
def api_list(system: str = Query(""), db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        if system:
            rows = conn.execute(
                "SELECT id, system_name, note_text, tags, created_at, updated_at FROM notes WHERE system_name = ? ORDER BY updated_at DESC",
                (system,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, system_name, note_text, tags, created_at, updated_at FROM notes ORDER BY updated_at DESC"
            ).fetchall()
        return {
            "ok": True,
            "notes": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@sub_app.get("/api/notes/systems")
def api_systems(db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        rows = conn.execute("SELECT DISTINCT system_name FROM notes ORDER BY system_name").fetchall()
        return {"ok": True, "systems": [r[0] for r in rows]}
    finally:
        conn.close()


@sub_app.put("/api/notes")
def api_upsert(db: str | None = None, system: str = Form(...), note_text: str = Form(""), tags: str = Form("")):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    if not system:
        return {"ok": False, "error": "system is required"}
    conn = get_conn(db_path)
    try:
        existing = conn.execute("SELECT id FROM notes WHERE system_name = ?", (system,)).fetchone()
        now = _now()
        if existing:
            conn.execute(
                "UPDATE notes SET note_text = ?, tags = ?, updated_at = ? WHERE id = ?",
                (note_text, tags, now, existing[0]),
            )
            note_id = existing[0]
        else:
            conn.execute(
                "INSERT INTO notes (system_name, note_text, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (system, note_text, tags, now, now),
            )
            note_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        row = conn.execute(
            "SELECT id, system_name, note_text, tags, created_at, updated_at FROM notes WHERE id = ?",
            (note_id,),
        ).fetchone()
        return {"ok": True, "note": dict(row)}
    finally:
        conn.close()


@sub_app.delete("/api/notes")
def api_delete(system: str = Query(...), db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    if not system:
        return {"ok": False, "error": "system is required"}
    conn = get_conn(db_path)
    try:
        conn.execute("DELETE FROM notes WHERE system_name = ?", (system,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()
