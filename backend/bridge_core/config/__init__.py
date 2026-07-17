"""Configuration management for Elite Bridge Core.

Loads settings from ~/.config/elite-bridge/config.json with defaults.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "elite-bridge"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "journal_path": "",
    "api_host": "127.0.0.1",
    "api_port": 8420,
    "log_level": "INFO",
    "database_path": str(CONFIG_DIR / "bridge.db"),
}


class Settings:
    """Application settings loaded from config file with defaults."""

    def __init__(self, data: dict | None = None):
        self._data = {**DEFAULTS, **(data or {})}

    @classmethod
    def load(cls) -> Settings:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                return cls(data)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Corrupted config, using defaults: %s", exc)
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self._data, indent=2))

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key: str):
        return self._data[key]

    @property
    def journal_path(self) -> str:
        return self._data["journal_path"]

    @property
    def api_host(self) -> str:
        return self._data["api_host"]

    @property
    def api_port(self) -> int:
        return self._data["api_port"]

    @property
    def database_path(self) -> str:
        return self._data["database_path"]
