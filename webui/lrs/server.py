import os
import sys

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from long_range_sensor import edsm, checkers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from webui._utils import get_system, read_config

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR LRS")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/system")
def api_system():
    system = get_system()
    if not system:
        return {"ok": False, "error": "no journal file or no system detected"}
    return {"ok": True, "system": system}


@sub_app.get("/api/check")
def api_check(
    radius: int = Query(100, ge=1, le=200),
    ship_size: str = Query("L", pattern="^[SML]$"),
    check_name: str = Query("exobiology", description="Check to run"),
):
    system = get_system()
    if not system:
        return {"ok": False, "error": "no system detected"}

    config = read_config()
    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    try:
        results = checkers.run_check(check_name, system, client, radius=radius, ship_size=ship_size)
        return {"ok": True, "system": system, "results": results}
    except edsm.EdsmError as e:
        return {"ok": False, "error": str(e)}
