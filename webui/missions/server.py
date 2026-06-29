import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from missions.reader import get_missions
from webui._utils import read_config, find_journal_dir

DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Missions")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/missions")
def api_missions():
    config = read_config()
    journal_dir = config.get("journal_path", "") or find_journal_dir()
    if not journal_dir:
        return {"ok": False, "error": "journal directory not found"}
    data = get_missions(journal_dir)
    return {"ok": True, **data}
