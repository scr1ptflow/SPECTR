import json
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from webui._utils import resolve_db, get_conn
from webui.engineering.materials import JOURNAL_LOOKUP, MATERIAL_REF, NAME_LOOKUP, MATERIAL_TOTALS

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Engineering")

_MATERIAL_CATEGORIES = {"Raw", "Manufactured", "Encoded"}


def _enrich(materials):
    for m in materials:
        key = m.get("name", "").lower()
        ref = JOURNAL_LOOKUP.get(key) or NAME_LOOKUP.get(key)
        if ref:
            m["section"] = ref["section"]
            m["grade"] = ref["grade"]
            if not m.get("localised"):
                m["localised"] = ref["localised"]
        else:
            m["section"] = None
            m["grade"] = None


def _aggregate_materials(conn):
    rows = conn.execute(
        "SELECT raw_json, timestamp FROM events WHERE event IN ('Materials','MaterialCollected','MaterialDiscarded','MaterialTrade','MaterialDiscovered') ORDER BY timestamp"
    ).fetchall()

    inv: dict[str, dict] = {}  # name -> {name, category, count, localised}

    for raw_json, _ in rows:
        d = json.loads(raw_json)
        event = d["event"]

        if event == "Materials":
            for cat in ("Raw", "Manufactured", "Encoded"):
                for item in d.get(cat, []):
                    name = item.get("Name", "")
                    cnt = item.get("Count", 0)
                    loc = item.get("Name_Localised", "")
                    key = name.lower()
                    inv[key] = {"name": name, "category": cat, "count": cnt, "localised": loc}

        elif event == "MaterialCollected":
            name = d.get("Name", "")
            cat = d.get("Category", "Unknown")
            cnt = d.get("Count", 1)
            loc = d.get("Name_Localised", "")
            key = name.lower()
            if key not in inv:
                inv[key] = {"name": name, "category": cat, "count": 0, "localised": loc}
            inv[key]["count"] += cnt

        elif event == "MaterialDiscarded":
            name = d.get("Name", "")
            cnt = d.get("Count", 1)
            key = name.lower()
            if key in inv:
                inv[key]["count"] = max(0, inv[key]["count"] - cnt)

        elif event == "MaterialDiscovered":
            name = d.get("Name", "")
            cat = d.get("Category", "Unknown")
            loc = d.get("Name_Localised", "")
            key = name.lower()
            if key not in inv:
                inv[key] = {"name": name, "category": cat, "count": 0, "localised": loc}
            inv[key]["count"] += 1

        elif event == "MaterialTrade":
            paid = d.get("Paid", {})
            recv = d.get("Received", {})
            for side, mult in [(paid, -1), (recv, 1)]:
                mname = side.get("Material", "")
                mqty = side.get("Quantity", 0)
                mcat = side.get("Category", "Unknown")
                mkey = mname.lower()
                if mkey not in inv:
                    inv[mkey] = {"name": mname, "category": mcat, "count": 0, "localised": ""}
                inv[mkey]["count"] = max(0, inv[mkey]["count"] + mqty * mult)

    materials = list(inv.values())
    _enrich(materials)
    return materials


def _get_engineers(conn):
    rows = conn.execute(
        "SELECT raw_json FROM events WHERE event = 'EngineerProgress' ORDER BY timestamp"
    ).fetchall()

    engineers: dict[str, dict] = {}
    for (raw_json,) in rows:
        d = json.loads(raw_json)
        for eng in d.get("Engineers", []):
            name = eng.get("Engineer", "")
            if not name:
                continue
            rank = eng.get("Rank", 0)
            stage = eng.get("Stage", eng.get("Progress", ""))
            progress = eng.get("RankProgress", 0)
            engineers[name] = {
                "name": name,
                "rank": rank,
                "stage": stage,
                "progress": progress,
            }

    return list(engineers.values())


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


def _sectioned(materials):
    result = {}
    for cat in _MATERIAL_CATEGORIES:
        cat_mats = [m for m in materials if m.get("section") and m["category"] == cat]
        sections = {}
        for m in cat_mats:
            sec = m["section"]
            if sec not in sections:
                sections[sec] = {"section": sec, "materials": {}}
            sections[sec]["materials"][m["grade"]] = m
        ordered = []
        if cat in MATERIAL_REF:
            for sec_name in MATERIAL_REF[cat]:
                if sec_name in sections:
                    ordered.append(sections.pop(sec_name))
        for sec in sections.values():
            ordered.append(sec)
        result[cat] = ordered
    return result


@sub_app.get("/api/materials")
def api_materials(db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        materials = _aggregate_materials(conn)
        grouped = {c: [] for c in _MATERIAL_CATEGORIES}
        grouped["Other"] = []
        for m in materials:
            cat = m["category"] if m["category"] in _MATERIAL_CATEGORIES else "Other"
            grouped[cat].append(m)
        for cat in grouped:
            grouped[cat].sort(key=lambda x: x["count"], reverse=True)
        return {
            "ok": True,
            "materials": materials,
            "grouped": grouped,
            "sectioned": _sectioned(materials),
            "totals": dict(MATERIAL_TOTALS),
        }
    finally:
        conn.close()


@sub_app.get("/api/engineers")
def api_engineers(db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        engineers = _get_engineers(conn)
        return {"ok": True, "engineers": engineers}
    finally:
        conn.close()
