import tkinter as tk
import os
import json
from core.plugin_base import Plugin
from core.journal import default_journal_path
from .route_view import RouteView
from .follow_route import FollowRoute

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class JumpTracker(Plugin):
    name = "Jump Tracker"
    version = "1.0.0"
    description = "Route-only display: next jump destination and progress bar"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event
        self.pcfg = config.plugin_config(self.name)

        win_w = self.pcfg.get("window_width", 400)
        win_h = self.pcfg.get("window_height", 120)
        win_pos = self.pcfg.get("window_position", "top")

        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=win_w, height=win_h
        )
        parent = self.win.container

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        accent = config.get("overlay", "accent_color", default="#6B8E23")

        self.journal_dir = default_journal_path(config.get("journal_path"))

        self.current_system = ""
        self.current_pos = None
        self.route = []
        self.route_idx = -1
        self.fsd_charging = False
        self._navroute_mtime = 0
        self._follow = FollowRoute(DATA_DIR)

        self.stats = self._load_json("stats.json", {"jumps": 0, "distance_ly": 0.0})
        self._navroute_polling = False

        # === Route line: Dest / Next / progress ===
        self.route_line = tk.Label(
            parent, text="", font=font, bg=bg, fg=accent, anchor=tk.W,
        )
        self.route_line.pack(fill=tk.X, pady=0)

        # === Route bar ===
        self.route_bar = RouteView(parent, bg=bg, scale_factor=self.overlay._scale_factor)
        self.route_bar.pack(fill=tk.X, pady=(0, 2))

        # === Warnings (neutron / refuel / fuel) ===
        self.warn_label = tk.Label(
            parent, text="", font=font, bg=bg, fg="#ffaa00", anchor=tk.W,
        )
        self.warn_label.pack(fill=tk.X, pady=0)

        event_bus.subscribe("journal:FSDJump", self._handler)
        event_bus.subscribe("journal:Location", self._handler)
        event_bus.subscribe("journal:NavRoute", self._handler)
        event_bus.subscribe("journal:Route", self._handler)
        event_bus.subscribe("journal:NavRouteClear", self._handler)
        event_bus.subscribe("journal:StartJump", self._handler)

        self._restore_state_from_journal()

        self._read_navroute()
        parent.update_idletasks()
        self._update_display()
        self._navroute_polling = True
        self._poll_navroute()

    def on_unload(self):
        self._navroute_polling = False
        self._save_json("stats.json", self.stats)
        for ev in (
            "journal:FSDJump", "journal:Location", "journal:NavRoute",
            "journal:Route", "journal:NavRouteClear", "journal:StartJump",
        ):
            self.event_bus.unsubscribe(ev, self._handler)
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass

    def _load_json(self, name, default):
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return default

    def _save_json(self, name, data):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def _read_navroute(self):
        nav_path = os.path.join(self.journal_dir, "NavRoute.json")
        try:
            mtime = os.path.getmtime(nav_path)
        except OSError:
            return
        if mtime <= self._navroute_mtime:
            return
        self._navroute_mtime = mtime
        try:
            with open(nav_path, encoding="utf-8") as f:
                data = json.load(f)
            self._set_route(data.get("Route", []))
        except (OSError, json.JSONDecodeError):
            pass

    def _restore_state_from_journal(self):
        from core.journal import read_last_journal_event
        last_location = read_last_journal_event(self.journal_dir, ("Location", "FSDJump"))
        if last_location:
            self.current_system = last_location.get("StarSystem", "")
            self.current_pos = last_location.get("StarPos", self.current_pos)
            self._follow.set_next(self.current_system)
            self._follow.rescan()

    def _poll_navroute(self):
        if not self._navroute_polling:
            return
        self._read_navroute()
        self._update_display()
        self.overlay.schedule(2000, self._poll_navroute)

    def _set_route(self, entries):
        self.route = []
        for e in entries:
            name = e.get("StarSystem", "")
            if not name:
                continue
            self.route.append({
                "name": name,
                "address": e.get("SystemAddress", 0),
                "star_class": e.get("StarClass", ""),
                "pos": e.get("StarPos", None),
            })
        self._update_route_idx()

    def _update_route_idx(self):
        if not self.route or not self.current_system:
            self.route_idx = -1
            return
        self.route_idx = -1
        for i, entry in enumerate(self.route):
            if entry["name"] == self.current_system:
                self.route_idx = i
                return

    def _route_remaining(self):
        if self.route_idx < 0:
            return len(self.route) - 1 if self.route else 0
        return max(0, len(self.route) - self.route_idx - 1)

    def _route_next(self):
        if self.route_idx < 0:
            return self.route[0] if self.route else None
        idx = self.route_idx + 1
        return self.route[idx] if idx < len(self.route) else None

    def _route_total_dist(self):
        total = 0.0
        prev = None
        for entry in self.route:
            pos = entry.get("pos")
            if pos and prev:
                dx = pos[0] - prev[0]
                dy = pos[1] - prev[1]
                dz = pos[2] - prev[2]
                total += (dx * dx + dy * dy + dz * dz) ** 0.5
            prev = pos
        return total

    def on_event(self, event, data):
        if event == "journal:FSDJump":
            self.current_system = data.get("StarSystem", "")
            self.current_pos = data.get("StarPos", self.current_pos)
            self.fsd_charging = False
            jd = data.get("JumpDist", 0)
            self.stats["jumps"] += 1
            self.stats["distance_ly"] += jd
            self._save_json("stats.json", self.stats)
            self._update_route_idx()
            self._follow.set_next(self.current_system)
            self._follow.rescan()

        elif event == "journal:Location":
            self.current_system = data.get("StarSystem", "")
            self.current_pos = data.get("StarPos", self.current_pos)
            self._read_navroute()
            self._update_route_idx()
            self._follow.set_next(self.current_system)

        elif event in ("journal:NavRoute", "journal:Route"):
            self._set_route(data.get("Route", []))

        elif event == "journal:NavRouteClear":
            self.route = []
            self.route_idx = -1
            self._navroute_mtime = 0

        elif event == "journal:StartJump":
            if data.get("JumpType") == "Hyperspace":
                self.fsd_charging = True

        self._update_display()

    def _effective_route(self):
        if self.route and len(self.route) >= 1:
            return self.route
        if self._follow.active and len(self._follow.hops) >= 1:
            return self._follow.hops
        return []

    def _effective_idx(self):
        if self.route and len(self.route) >= 1:
            return self.route_idx
        if self._follow.active:
            return self._follow.last_idx
        return -1

    def _effective_next(self):
        if self.route and len(self.route) >= 1:
            return self._route_next()
        if self._follow.active:
            return self._follow.next_hop()
        return None

    def _effective_remaining(self):
        if self.route and len(self.route) >= 1:
            return self._route_remaining()
        if self._follow.active:
            return self._follow.remaining()
        return 0

    def _effective_dest(self):
        if self.route and len(self.route) >= 1:
            return self.route[-1]
        if self._follow.active and self._follow.hops:
            return self._follow.hops[-1]
        return None

    def _effective_total_dist(self):
        if self.route and len(self.route) >= 2:
            return self._route_total_dist()
        if self._follow.active and len(self._follow.hops) >= 2:
            total = 0.0
            prev = None
            for h in self._follow.hops:
                pos = h.get("pos")
                if pos and prev:
                    dx = pos[0] - prev[0]
                    dy = pos[1] - prev[1]
                    dz = pos[2] - prev[2]
                    total += (dx * dx + dy * dy + dz * dz) ** 0.5
                prev = pos
            return total
        return 0.0

    def _jump_color(self, remaining):
        if remaining <= 3:
            return "#ff4444"
        if remaining <= 10:
            return "#ffaa00"
        return "#00d4aa"

    def _update_display(self):
        route = self._effective_route()
        idx = self._effective_idx()
        nxt = self._effective_next()
        dest = self._effective_dest()
        has_route = bool(route and len(route) >= 1)
        charging = self.fsd_charging

        if has_route:
            dest_name = dest["name"] if dest else "?"
            nxt_name = nxt["name"] if nxt else "?"
            nxt_class = nxt.get("star_class", "") if nxt else ""
            cs = f" ({nxt_class})" if nxt_class else ""
            pos_str = f"#{idx + 1}" if idx >= 0 else "?"
            total_count = len(route)
            dist = self._effective_total_dist()
            dist_str = f"  |  {dist:.0f} LY" if dist > 0 else ""

            if dest and self.current_system == dest["name"]:
                self.route_line.config(text=f"Arrived!{dist_str}", fg=self._jump_color(0))
            else:
                nxt_text = f"Next: {nxt_name}{cs}" if nxt_name else "Next: --"
                self.route_line.config(
                    text=f"Dest: {dest_name}  |  {nxt_text}  {pos_str} of {total_count}{dist_str}"
                )
            self.route_bar.pack(fill=tk.X, pady=(0, 2))
            self.route_bar.set_route(route, idx, total_dist=dist)
        else:
            if charging:
                self.route_line.config(text="Jumping...", fg="#ffaa00")
            else:
                self.route_line.config(text="")
            self.route_bar.set_route([], -1)
            self.route_bar.pack_forget()

        # Warnings from FollowRoute
        warn_parts = []
        if has_route and self._follow.active:
            warns = self._follow.warnings()
            for wtype in (w for w, _ in warns):
                if wtype == "neutron":
                    warn_parts.append("* Neutron")
                elif wtype == "refuel":
                    warn_parts.append("* Refuel")
                elif wtype == "fuel":
                    warn_parts.append("* Fuel check")
        self.warn_label.config(text="  ".join(warn_parts) if warn_parts else "")

        # Dynamic visibility
        dynamic = self.pcfg.get("dynamic", False)
        if dynamic:
            self.win.attributes("-alpha", 1.0 if has_route else 0.0)
        else:
            self.win.attributes("-alpha", 1.0)
        self.overlay.resize_plugin(self.name)
