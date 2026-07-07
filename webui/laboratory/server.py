import json
import os
from collections import defaultdict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from webui._utils import resolve_db, get_conn
from blackbox.exobiology import species_value as table_value

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Laboratory")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


SCANS_PER_SET = 3


def _get_samples(conn):
    row = conn.execute("SELECT MAX(timestamp) FROM events WHERE event = 'Died'").fetchone()
    after_death = row[0] or ""

    if after_death:
        sell_filter = " AND timestamp > ?"
        scan_filter = " AND timestamp > ?"
    else:
        sell_filter = ""
        scan_filter = ""

    # Build SystemAddress → StarSystem and (SystemAddress, BodyID) → BodyName
    sys_map: dict[int, str] = {}
    body_map: dict[tuple[int, int], str] = {}
    for evt in ('FSDJump', 'Location'):
        for (raw_json,) in conn.execute("SELECT raw_json FROM events WHERE event = ?", (evt,)):
            d = json.loads(raw_json)
            sa = d.get("SystemAddress")
            ss = d.get("StarSystem")
            if sa is not None and ss:
                sys_map[sa] = ss
    for (raw_json,) in conn.execute("SELECT raw_json FROM events WHERE event = 'Scan'"):
        d = json.loads(raw_json)
        sa = d.get("SystemAddress")
        bid = d.get("BodyID")
        bn = d.get("BodyName")
        if sa is not None and bid is not None and bn:
            body_map[(sa, bid)] = bn

    sold: dict[str, int] = defaultdict(int)
    prices: dict[str, int] = {}
    for (raw_json,) in conn.execute(
        f"SELECT raw_json FROM events WHERE event = 'SellOrganicData'{sell_filter}",
        (after_death,) if after_death else ()
    ).fetchall():
        d = json.loads(raw_json)
        for item in d.get("BioData") or []:
            species = item.get("Species_Localised") or item.get("Species")
            if not species:
                continue
            # Each BioData entry represents one complete set (3 scans) sold.
            sold[species] += 1
            val = int(item.get("Value") or 0)
            if val:
                prices[species] = val

    scanned: dict[str, dict] = {}
    for (raw_json,) in conn.execute(
        f"SELECT raw_json FROM events WHERE event = 'ScanOrganic'{scan_filter}",
        (after_death,) if after_death else ()
    ).fetchall():
        d = json.loads(raw_json)
        species = d.get("Species_Localised") or d.get("Species")
        if not species:
            continue
        sa = d.get("SystemAddress")
        body_id = d.get("Body")
        system = sys_map.get(sa, "")
        body_name = body_map.get((sa, body_id), body_id) if sa is not None and body_id is not None else body_id
        if species not in scanned:
            scanned[species] = {"count": 0, "genus": d.get("Genus_Localised") or d.get("Genus", ""), "body": body_name, "system": system}
        scanned[species]["count"] += 1

    results = []
    for species, info in scanned.items():
        scan_count = info["count"]
        sold_sets = sold.get(species, 0)
        total_sets = scan_count // SCANS_PER_SET
        available_sets = total_sets - sold_sets
        if available_sets < 1:
            continue
        price = prices.get(species) or table_value(species)
        results.append({
            "species": species,
            "genus": info["genus"],
            "body": info["body"],
            "system": info["system"],
            "count": available_sets,
            "value_per_set": price,
            "total_value": price * available_sets if price else None,
        })

    results.sort(key=lambda r: r["total_value"] if r["total_value"] else 0, reverse=True)
    return results


@sub_app.get("/api/laboratory")
def api_laboratory(db: str | None = None):
    db_path = resolve_db(db)
    if not os.path.exists(db_path):
        return {"ok": False, "error": f"Database not found: {db_path}"}
    conn = get_conn(db_path)
    try:
        samples = _get_samples(conn)
        total_value = sum(r["total_value"] for r in samples if r["total_value"])
        return {
            "ok": True,
            "samples": samples,
            "total_value": total_value,
            "total_count": sum(r["count"] for r in samples),
        }
    finally:
        conn.close()
