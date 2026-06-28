import os
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, DIR)

from missions.reader import get_missions, _read_journal_dir

CONFIG_PATH = os.path.join(DIR, "config.json")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Missions")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/missions")
def api_missions():
    journal_dir = _read_journal_dir(CONFIG_PATH)
    if not journal_dir:
        return {"ok": False, "error": "journal directory not found"}
    data = get_missions(journal_dir)
    return {"ok": True, **data}
