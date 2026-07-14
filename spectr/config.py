# Configuration persistence — reads/writes ~/.config/spectr/config.json
# Stores journal path, API keys, and commander name.
# Used by MainWindow (load on startup) and SettingsPanel (read + save).

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# Config file location: ~/.config/spectr/config.json
CONFIG_DIR = Path.home() / ".config" / "spectr"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default values — merged with whatever the user has saved so that missing
# keys are always filled in with sensible defaults.
DEFAULT_CONFIG = {
    "journal_path": "",
    "inara_api_key": "",
    "inara_cmdr_name": "SPECTR",
    "edsm_api_key": "",
    "edsm_cmdr_name": "SPECTR",
    "commander_name": "",
    "font_size": "11",
}


def load_config() -> dict:
    """Load saved config, merging with DEFAULT_CONFIG.

    Falls back to defaults if the file is missing or corrupted.
    """
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Corrupted config file, using defaults: %s", exc)
            return dict(DEFAULT_CONFIG)
        return {**DEFAULT_CONFIG, **data}
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Write config to disk, merging with defaults first."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**DEFAULT_CONFIG, **config}
    CONFIG_FILE.write_text(json.dumps(merged, indent=2))


def validate_config(config: dict) -> list[str]:
    """Validate config values. Returns a list of warning messages."""
    warnings = []
    jp = config.get("journal_path", "")
    if jp:
        p = Path(jp).expanduser()
        if not p.exists():
            warnings.append(f"Journal path does not exist: {jp}")
        elif not any(p.glob("Journal.*.log")):
            warnings.append(f"No journal files found in: {jp}")
    return warnings
