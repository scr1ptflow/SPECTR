import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "spectr"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "journal_path": "",
    "inara_api_key": "",
    "inara_app_name": "SPECTR",
    "edsm_api_key": "",
    "edsm_app_name": "SPECTR",
    "commander_name": "",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        return {**DEFAULT_CONFIG, **data}
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**DEFAULT_CONFIG, **config}
    CONFIG_FILE.write_text(json.dumps(merged, indent=2))
