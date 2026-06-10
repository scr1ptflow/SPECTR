import json
import os
import tkinter as tk
from core.plugin_base import Plugin
from core.journal import default_journal_path
from core.status import HARDPOINTS, IN_DANGER, BEING_INTERDICTED

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_IN_COMBAT_FLAGS = HARDPOINTS | BEING_INTERDICTED | IN_DANGER


class CombatTracker(Plugin):
    name = "Combat Tracker"
    version = "1.0.0"
    description = "Tracks combat stats during the current session"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self._handler = self.on_event
        self.pcfg = config.plugin_config(self.name)
        win_pos = self.pcfg.get("window_position", "top-right")
        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=250, height=150
        )
        parent = self.win.container
        self.win.attributes("-alpha", 1.0)
        self._in_combat = False

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        accent = config.get("overlay", "accent_color", default="#6B8E23")

        self.kills_label = tk.Label(
            parent,
            text="Kills: 0",
            font=font,
            bg=bg,
            fg=accent,
            anchor=tk.W,
        )
        self.kills_label.pack(fill=tk.X, pady=1)

        self.bounty_label = tk.Label(
            parent,
            text="Bounty: 0 CR",
            font=font,
            bg=bg,
            fg="#e0e0e0",
            anchor=tk.W,
        )
        self.bounty_label.pack(fill=tk.X, pady=1)

        self.bonds_label = tk.Label(
            parent,
            text="Bonds: 0 CR",
            font=font,
            bg=bg,
            fg="#e0e0e0",
            anchor=tk.W,
        )
        self.bonds_label.pack(fill=tk.X, pady=1)

        self.weapons_label = tk.Label(
            parent,
            text="Weapons: Stowed",
            font=font,
            bg=bg,
            fg="#888888",
            anchor=tk.W,
        )
        self.weapons_label.pack(fill=tk.X, pady=1)

        self.kills = 0
        self.bounty_total = 0
        self.bonds_total = 0
        self._hardpoints_deployed = False
        self._load_stats()

        # Read current Status.json for accurate initial state
        journal_dir = default_journal_path(config.get("journal_path"))
        try:
            sp = os.path.join(journal_dir, "Status.json")
            if os.path.isfile(sp):
                with open(sp, encoding="utf-8") as f:
                    sd = json.load(f)
                flags = sd.get("Flags", 0)
                self._hardpoints_deployed = bool(flags & HARDPOINTS)
        except Exception:
            pass

        # Apply initial dynamic visibility
        dynamic = self.pcfg.get("dynamic", False)
        if dynamic:
            in_combat = bool(self._hardpoints_deployed)
            self._in_combat = in_combat
            self.win.attributes("-alpha", 1.0 if in_combat else 0.0)

        event_bus.subscribe("status", self._handler)
        event_bus.subscribe("journal:Bounty", self._handler)
        event_bus.subscribe("journal:CombatBond", self._handler)
        event_bus.subscribe("journal:Died", self._handler)

        self._update_display()

    def on_unload(self):
        self._save_stats()
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass
        self.event_bus.unsubscribe("status", self._handler)
        self.event_bus.unsubscribe("journal:Bounty", self._handler)
        self.event_bus.unsubscribe("journal:CombatBond", self._handler)
        self.event_bus.unsubscribe("journal:Died", self._handler)

    def _stats_path(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, "stats.json")

    def _save_stats(self):
        data = {
            "kills": self.kills,
            "bounty_total": self.bounty_total,
            "bonds_total": self.bonds_total,
        }
        try:
            with open(self._stats_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def _load_stats(self):
        path = self._stats_path()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    stats = json.load(f)
                self.kills = stats.get("kills", 0)
                self.bounty_total = stats.get("bounty_total", 0)
                self.bonds_total = stats.get("bonds_total", 0)
                self._update_display()
            except (OSError, json.JSONDecodeError):
                pass

    def on_event(self, event, data):
        if event == "status":
            flags = data.get("Flags", data.get("flags", 0))
            self._hardpoints_deployed = bool(flags & HARDPOINTS)
            in_combat = bool(flags & _IN_COMBAT_FLAGS)
            dynamic = self.pcfg.get("dynamic", False)
            if dynamic:
                if in_combat != self._in_combat:
                    self._in_combat = in_combat
                    self.win.attributes("-alpha", 1.0 if in_combat else 0.0)
            else:
                self._in_combat = in_combat
                self.win.attributes("-alpha", 1.0)
            self._update_display()
        elif event == "journal:Bounty":
            self.kills += 1
            reward = data.get("TotalReward", data.get("Reward", 0))
            self.bounty_total += reward
            self._update_display()
        elif event == "journal:CombatBond":
            reward = data.get("Reward", 0)
            self.bonds_total += reward
            self._update_display()
        elif event == "journal:Died":
            self._in_combat = False
            self.win.attributes("-alpha", 0.0)
            self._update_display()

    def _update_display(self):
        if self._hardpoints_deployed:
            self.weapons_label.config(text="Weapons: Deployed", fg="#ff6b6b")
        else:
            self.weapons_label.config(text="Weapons: Stowed", fg="#888888")
        self.kills_label.config(text=f"Kills: {self.kills}")
        self.bounty_label.config(text=f"Bounty: {self.bounty_total:,} CR")
        self.bonds_label.config(text=f"Bonds: {self.bonds_total:,} CR")
