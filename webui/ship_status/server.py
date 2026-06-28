import os
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, DIR)

from ship_status.reader import get_ship_data, read_journal_dir

CONFIG_PATH = os.path.join(DIR, "config.json")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sub_app = FastAPI(title="SPECTR Ship Status")


@sub_app.get("/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        return HTMLResponse(f.read())


@sub_app.get("/api/ship")
def api_ship():
    journal_dir = read_journal_dir(CONFIG_PATH)
    if not journal_dir:
        return {"ok": False, "error": "journal directory not found"}
    data = get_ship_data(journal_dir)
    return {"ok": True, **data}
