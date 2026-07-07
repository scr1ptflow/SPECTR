import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ship_status.reader import get_ship_data
from webui._utils import read_config, find_journal_dir, resolve_db

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Ship Status")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/ship")
def api_ship():
    config = read_config()
    journal_dir = config.get("journal_path", "") or find_journal_dir()
    if not journal_dir:
        return {"ok": False, "error": "journal directory not found"}
    db_path = resolve_db()
    data = get_ship_data(journal_dir, db_path=db_path)
    return {"ok": True, **data}
