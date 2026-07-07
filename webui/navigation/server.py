import csv
import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse

from blackbox import _PROJECT_DIR
from long_range_sensor import journal as lrs_journal
from long_range_sensor.edsm import EdsmClient, EdsmError
from webui._utils import read_config, find_journal_dir, get_latest_journal

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
CACHE_DIR = os.path.join(str(_PROJECT_DIR), "navigation_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "route.csv")
PLANNED_CACHE_FILE = os.path.join(CACHE_DIR, "route_planned.csv")
COMPARE_CACHE_DIR = os.path.join(CACHE_DIR, "compare")

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


_SPANSH_UA = "SPECTR-Navigation/0.1.0"


def _spansh_get(url: str, params: dict | None = None) -> dict:
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": _SPANSH_UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


@sub_app.post("/api/route/plan")
def api_route_plan(
    from_system: str = Form(...),
    to_system: str = Form(...),
    jump_range: float = Form(...),
    efficiency: int = Form(60),
):
    if jump_range < 1:
        return {"ok": False, "error": "Jump range must be at least 1 LY"}
    try:
        data = _spansh_get("https://spansh.co.uk/api/route", {
            "from": from_system,
            "to": to_system,
            "range": str(jump_range),
            "efficiency": str(efficiency),
        })
    except urllib.error.HTTPError as e:
        return _edsm_route_plan(from_system, to_system, jump_range) if e.code == 400 else \
            {"ok": False, "error": f"Spansh HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return _edsm_route_plan(from_system, to_system, jump_range)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    job_id = data.get("job")
    if not job_id:
        return _edsm_route_plan(from_system, to_system, jump_range)

    deadline = time.time() + 90
    result = None
    spansh_error = None
    while time.time() < deadline:
        time.sleep(3)
        try:
            poll = _spansh_get(f"https://spansh.co.uk/api/results/{job_id}")
        except Exception:
            continue
        if poll.get("status") == "ok" and "result" in poll:
            result = poll["result"]
            break
        if poll.get("state") == "error":
            spansh_error = "Spansh route planning failed"
            break
        if poll.get("status") == "not found":
            spansh_error = "Spansh job not found"
            break

    if not result:
        if spansh_error and "found" in spansh_error.lower():
            return {"ok": False, "error": spansh_error}
        return _edsm_route_plan(from_system, to_system, jump_range)

    jumps = result.get("system_jumps", [])
    if not jumps:
        return _edsm_route_plan(from_system, to_system, jump_range)

    rows = []
    for j in jumps:
        rows.append({
            "System": j.get("system", ""),
            "X": str(j.get("x", "")),
            "Y": str(j.get("y", "")),
            "Z": str(j.get("z", "")),
            "Distance": f'{j.get("distance_jumped", 0):.2f}',
            "Remaining": f'{j.get("distance_left", 0):.2f}',
            "Neutron Star": "yes" if j.get("neutron_star") else "",
        })

    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(PLANNED_CACHE_FILE, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=_PLAN_FIELDS)
            w.writeheader()
            w.writerows(rows)
    except Exception:
        pass

    return {
        "ok": True,
        "file": f"{from_system} \u2192 {to_system} ({result.get('total_jumps', len(jumps))} jumps)",
        "total": len(rows),
        "columns": _PLAN_FIELDS,
        "rows": rows,
    }


_PLAN_FIELDS = ["System", "X", "Y", "Z", "Distance", "Remaining", "Neutron Star"]


def _plan_single(from_system: str, to_system: str, jump_range: float, efficiency: int) -> dict:
    try:
        data = _spansh_get("https://spansh.co.uk/api/route", {
            "from": from_system, "to": to_system,
            "range": str(jump_range), "efficiency": str(efficiency),
        })
    except Exception:
        return _edsm_route_plan(from_system, to_system, jump_range)

    job_id = data.get("job")
    if not job_id:
        return _edsm_route_plan(from_system, to_system, jump_range)

    deadline = time.time() + 90
    result = None
    spansh_error = None
    while time.time() < deadline:
        time.sleep(3)
        try:
            poll = _spansh_get(f"https://spansh.co.uk/api/results/{job_id}")
        except Exception:
            continue
        if poll.get("status") == "ok" and "result" in poll:
            result = poll["result"]
            break
        if poll.get("state") == "error":
            spansh_error = poll.get("state")
            break
        if poll.get("status") == "not found":
            spansh_error = poll.get("status")
            break

    if not result:
        return _edsm_route_plan(from_system, to_system, jump_range)

    jumps = result.get("system_jumps", [])
    if not jumps:
        return _edsm_route_plan(from_system, to_system, jump_range)

    total_dist = sum(j.get("distance_jumped", 0) for j in jumps)
    neutron_count = sum(1 for j in jumps if j.get("neutron_star"))
    avg_jump = total_dist / len(jumps) if jumps else 0

    rows = []
    for j in jumps:
        rows.append({
            "System": j.get("system", ""),
            "X": str(j.get("x", "")),
            "Y": str(j.get("y", "")),
            "Z": str(j.get("z", "")),
            "Distance": f'{j.get("distance_jumped", 0):.2f}',
            "Remaining": f'{j.get("distance_left", 0):.2f}',
            "Neutron Star": "yes" if j.get("neutron_star") else "",
        })

    return {
        "ok": True,
        "jumps": len(jumps),
        "total_distance_ly": round(total_dist, 2),
        "neutron_jumps": neutron_count,
        "avg_jump_ly": round(avg_jump, 2),
        "columns": _PLAN_FIELDS,
        "rows": rows,
    }


def _dist_3d(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def _edsm_route_plan(from_system: str, to_system: str, jump_range: float) -> dict:
    config = read_config()
    api_key = config.get("edsm", {}).get("api_key", "")
    client = EdsmClient(api_key=api_key)

    try:
        origin = client.system_info(from_system)
        dest = client.system_info(to_system)
    except EdsmError as e:
        return {"ok": False, "error": str(e)}
    if not origin or not dest:
        return {"ok": False, "error": "EDSM could not resolve origin or destination system"}
    co = origin.get("coords", {})
    cd = dest.get("coords", {})
    if not co or not cd:
        return {"ok": False, "error": "EDSM returned no coordinates for origin/destination"}
    ox, oy, oz = co["x"], co["y"], co["z"]
    dx, dy, dz = cd["x"], cd["y"], cd["z"]

    if _dist_3d(ox, oy, oz, dx, dy, dz) <= jump_range:
        rows = [{"System": to_system, "X": str(dx), "Y": str(dy), "Z": str(dz),
                 "Distance": f"{_dist_3d(ox, oy, oz, dx, dy, dz):.2f}", "Remaining": "0.00", "Neutron Star": ""}]
        return {"ok": True, "jumps": 1, "total_distance_ly": round(_dist_3d(ox, oy, oz, dx, dy, dz), 2),
                "neutron_jumps": 0, "avg_jump_ly": round(_dist_3d(ox, oy, oz, dx, dy, dz), 2),
                "columns": _PLAN_FIELDS, "rows": rows}

    visited = {from_system.lower()}
    route = []
    cx, cy, cz = ox, oy, oz
    cur_name = from_system

    for _ in range(500):
        remaining = _dist_3d(cx, cy, cz, dx, dy, dz)
        if remaining <= jump_range:
            route.append({"System": to_system, "X": str(dx), "Y": str(dy), "Z": str(dz),
                          "Distance": f"{remaining:.2f}", "Remaining": "0.00"})
            break

        try:
            sphere = client.sphere_systems(cur_name, min(jump_range, 100))
        except Exception:
            return {"ok": False, "error": f"EDSM sphere-systems query failed near {cur_name}"}
        if not sphere:
            return {"ok": False, "error": f"No EDSM systems found within {jump_range} LY of {cur_name}"}

        best = None
        best_dest_dist = float("inf")
        for sys in sphere:
            name = sys.get("name", "")
            if not name or name.lower() in visited:
                continue
            sc = sys.get("coords", {})
            sx, sy, sz = sc.get("x", 0), sc.get("y", 0), sc.get("z", 0)
            step_d = _dist_3d(cx, cy, cz, sx, sy, sz)
            if step_d > jump_range + 0.05:
                continue
            dd = _dist_3d(sx, sy, sz, dx, dy, dz)
            if dd < best_dest_dist:
                best_dest_dist = dd
                best = (name, sx, sy, sz, step_d)

        if not best:
            return {"ok": False, "error": f"No reachable system within {jump_range} LY of {cur_name}"}

        visited.add(best[0].lower())
        route.append({"System": best[0], "X": str(best[1]), "Y": str(best[2]), "Z": str(best[3]),
                      "Distance": f"{best[4]:.2f}", "Remaining": f"{best_dest_dist:.2f}"})
        cur_name, cx, cy, cz = best[0], best[1], best[2], best[3]
    else:
        return {"ok": False, "error": "Route too long — exceeded 500 step limit"}

    total_dist = sum(float(r["Distance"]) for r in route)
    rows = [{**r, "Neutron Star": ""} for r in route]
    return {"ok": True, "jumps": len(rows), "total_distance_ly": round(total_dist, 2),
            "neutron_jumps": 0, "avg_jump_ly": round(total_dist / len(rows), 2) if rows else 0,
            "columns": _PLAN_FIELDS, "rows": rows, "source": "edsm"}


def _cache_key(from_system: str, to_system: str, configs: list) -> str:
    raw = f"{from_system}|{to_system}|{json.dumps(configs, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@sub_app.post("/api/route/compare")
def api_route_compare(
    from_system: str = Form(...),
    to_system: str = Form(...),
    configs: str = Form(...),  # JSON array of {range, efficiency, label}
):
    try:
        config_list = json.loads(configs)
    except (json.JSONDecodeError, TypeError):
        return {"ok": False, "error": "configs must be a JSON array"}

    if not isinstance(config_list, list) or not config_list:
        return {"ok": False, "error": "configs must be a non-empty array"}

    if from_system.lower() == to_system.lower():
        return {"ok": False, "error": "From and To systems must be different"}

    for cfg in config_list:
        if cfg.get("range", 0) < 1:
            return {"ok": False, "error": "Each range must be at least 1 LY"}

    # Check cache
    ck = _cache_key(from_system, to_system, config_list)
    cache_path = os.path.join(COMPARE_CACHE_DIR, f"{ck}.json")
    if os.path.isfile(cache_path):
        try:
            with open(cache_path) as f:
                cached = json.load(f)
            cached["cached"] = True
            return cached
        except Exception:
            pass

    os.makedirs(COMPARE_CACHE_DIR, exist_ok=True)

    results: list[dict] = []
    errors: list[dict] = []

    def plan_one(cfg):
        label = cfg.get("label", "")
        rng = cfg["range"]
        eff = cfg.get("efficiency", 60)
        out = _plan_single(from_system, to_system, rng, eff)
        out["label"] = label
        out["range"] = rng
        out["efficiency"] = eff
        return out

    with ThreadPoolExecutor(max_workers=min(len(config_list), 5)) as pool:
        fut_map = {pool.submit(plan_one, cfg): cfg for cfg in config_list}
        for fut in as_completed(fut_map):
            cfg = fut_map[fut]
            try:
                res = fut.result()
                if res.get("ok"):
                    results.append(res)
                else:
                    errors.append({"label": cfg.get("label", ""), "error": res.get("error", "Unknown error")})
            except Exception as e:
                errors.append({"label": cfg.get("label", ""), "error": str(e)})

    # Sort results by range asc, then efficiency desc
    results.sort(key=lambda r: (r["range"], -r["efficiency"]))

    payload = {
        "ok": True,
        "from": from_system,
        "to": to_system,
        "results": results,
        "errors": errors,
        "cached": False,
    }

    try:
        with open(cache_path, "w") as f:
            json.dump(payload, f)
    except Exception:
        pass

    return payload



