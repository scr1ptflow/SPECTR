import logging
import os
import sys

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(DIR))

from webui.cockpit.server import sub_app as cockpit_app
from webui.blackbox.server import sub_app as blackbox_app
from webui.ship_status.server import sub_app as ship_status_app
from webui.missions.server import sub_app as missions_app
from webui.lrs.server import sub_app as lrs_app
from webui.captains_log.server import sub_app as captains_log_app

app = FastAPI(title="SPECTR")
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
app.mount("/cockpit", cockpit_app)
app.mount("/blackbox", blackbox_app)
app.mount("/ship", ship_status_app)
app.mount("/missions", missions_app)
app.mount("/lrs", lrs_app)
app.mount("/captains-log", captains_log_app)


@app.get("/")
def root():
    return RedirectResponse(url="/cockpit/")
