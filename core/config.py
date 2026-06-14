import copy
import json
import logging
import os
import sys

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "journal_path": None,
    "overlay": {
        "opacity": 0.8,
        "position": "top-right",
        "width": 320,
        "height": 600,
        "offset_x": 0,
        "offset_y": 0,
        "font_family": "Consolas",
        "font_size": 10,
        "bg_color": "#010101",
        "fg_color": "#e0e0e0",
        "accent_color": "#00d4aa",
        "hide_on_unfocus": True,
        "hide_console": False,
        "settings_start_minimized": False,
    },
    "journal": {
        "poll_interval": 0.5
    },
    "api_keys": {
        "edsm_key": "",
        "inara_key": ""
    },
    "plugins": {},
    "active_profile": "SPECTR",
    "profiles": {
        "SPECTR": {}
    },
}

_SCHEMA = {
    "journal_path": (str, type(None)),
    "overlay.opacity": (int, float),
    "overlay.position": str,
    "overlay.width": int,
    "overlay.height": int,
    "overlay.offset_x": int,
    "overlay.offset_y": int,
    "overlay.font_family": str,
    "overlay.font_size": int,
    "overlay.bg_color": str,
    "overlay.fg_color": str,
    "overlay.accent_color": str,
    "overlay.hide_on_unfocus": bool,
    "overlay.hide_console": bool,
    "overlay.settings_start_minimized": bool,
    "journal.poll_interval": (int, float),
    "api_keys.edsm_key": str,
    "api_keys.inara_key": str,
    "active_profile": str,
}


class Config:
    def __init__(self, path=None):
        if path is None:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(os.path.abspath(sys.executable))
            else:
                base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            path = os.path.join(base_path, "config.json")
        self.path = os.path.abspath(path)
        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    user_config = json.load(f)
                self._merge(self.data, user_config)
                self._validate()
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load config: {e}")
        else:
            self.save()

    def _merge(self, base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def _validate(self):
        """Check config values match expected types. Reset invalid values to defaults."""
        for path, expected in _SCHEMA.items():
            keys = path.split(".")
            # Walk to parent
            d = self.data
            for k in keys[:-1]:
                if isinstance(d, dict):
                    d = d.get(k, {})
                else:
                    d = {}
                    break
            # Check value
            key = keys[-1]
            if not isinstance(d, dict):
                continue
            val = d.get(key)
            if val is not None and not isinstance(val, expected):
                default_val = self._get_default(path)
                logger.warning(f"Invalid config value for {path}: {val!r} (expected {expected}), resetting to {default_val!r}")
                d[key] = default_val

    def _get_default(self, dotted_path):
        """Get the default value for a dotted config path."""
        keys = dotted_path.split(".")
        d = DEFAULT_CONFIG
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
            else:
                return None
        return d

    def save(self):
        try:
            # Backup existing config before overwriting
            if os.path.exists(self.path):
                bak = self.path + ".bak"
                try:
                    with open(self.path, "r", encoding="utf-8") as src:
                        with open(bak, "w", encoding="utf-8") as dst:
                            dst.write(src.read())
                except OSError:
                    pass
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            os.replace(tmp, self.path)
        except OSError as e:
            logger.warning(f"Could not save config to {self.path}: {e}")

    def get(self, *keys, default=None):
        d = self.data
        for key in keys:
            if isinstance(d, dict):
                d = d.get(key)
                if d is None:
                    return default
            else:
                return default
        return d

    def plugin_config(self, name):
        plugins = self.data.setdefault("plugins", {})
        return plugins.setdefault(name, {})
