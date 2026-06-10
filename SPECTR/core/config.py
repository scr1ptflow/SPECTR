import copy
import json
import os

DEFAULT_CONFIG = {
    "journal_path": None,
    "overlay": {
        "opacity": 0.8,
        "position": "top-right",
        "width": 320,
        "height": 600,
        "offset_x": 10,
        "offset_y": 10,
        "font_family": "Consolas",
        "font_size": 11,
        "bg_color": "#0d0d1a",
        "fg_color": "#e0e0e0",
        "accent_color": "#00d4aa",
        "hide_on_unfocus": True
    },
    "journal": {
        "poll_interval": 0.5
    },
    "api_keys": {
        "edsm_key": "",
        "inara_key": ""
    },
    "plugins": {}
}


class Config:
    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        self.path = os.path.abspath(path)
        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    user_config = json.load(f)
                self._merge(self.data, user_config)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load config: {e}")

    def _merge(self, base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def save(self):
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            os.replace(tmp, self.path)
        except OSError as e:
            print(f"Warning: Could not save config to {self.path}: {e}")

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
        return self.data.get("plugins", {}).get(name, {})
