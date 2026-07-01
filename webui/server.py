import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from blackbox.recorder import Recorder
from blackbox.store import Store
from webui._utils import read_config, find_journal_dir, resolve_db

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

DIR = os.path.dirname(os.path.abspath(__file__))

from webui.cockpit.server import sub_app as cockpit_app
from webui.blackbox.server import sub_app as blackbox_app
from webui.ship_status.server import sub_app as ship_status_app
from webui.missions.server import sub_app as missions_app
from webui.lrs.server import sub_app as lrs_app
from webui.captains_log.server import sub_app as captains_log_app
from webui.system_map.server import sub_app as system_map_app
from webui.navigation.server import sub_app as navigation_app

app = FastAPI(title="SPECTR")
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
app.mount("/cockpit", cockpit_app)
app.mount("/blackbox", blackbox_app)
app.mount("/ship", ship_status_app)
app.mount("/missions", missions_app)
app.mount("/lrs", lrs_app)
app.mount("/captains-log", captains_log_app)
app.mount("/system-map", system_map_app)
app.mount("/navigation", navigation_app)

_recorder: Recorder | None = None


@app.on_event("startup")
def start_recorder():
    global _recorder
    config = read_config()
    jdir = find_journal_dir() or config.get("journal_path", "")
    if not jdir or not os.path.isdir(jdir):
        return
    db_path = resolve_db()
    store = Store(db_path)
    _recorder = Recorder(store, Path(jdir))
    _recorder.catch_up()
    _recorder.watch()


@app.on_event("shutdown")
def stop_recorder():
    global _recorder
    if _recorder is not None:
        _recorder.stop()
        _recorder = None


@app.get("/")
def root():
    return RedirectResponse(url="/cockpit/")
