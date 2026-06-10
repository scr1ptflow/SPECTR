import tkinter as tk
import os
import json
from core.plugin_base import Plugin
from core.journal import default_journal_path

G = 9.80665


class TargetInfo(Plugin):
    name = "System Info"
    version = "1.0.0"
    description = "System info and target/body details"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event
        self.overlay = overlay
        self.pcfg = config.plugin_config(self.name)
        win_pos = self.pcfg.get("window_position", "center-right")
        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=260, height=280,
        )
        parent = self.win.container
        self.win.attributes("-alpha", 1.0)

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        font_bold = (font[0], font[1])
        font_small = (font[0], max(font[1] - 2, 8))
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        accent = config.get("overlay", "accent_color", default="#00d4aa")
        fg = config.get("overlay", "fg_color", default="#e0e0e0")
        dim = "#888888"

        self.journal_dir = default_journal_path(config.get("journal_path"))

        # === System info (always visible at top) ===
        self.sys_frame = tk.Frame(parent, bg=bg)

        self.sys_line = tk.Label(
            self.sys_frame, text="", font=font_bold, bg=bg, fg=accent, anchor=tk.W,
        )
        self.sys_line.pack(fill=tk.X)

        self.detail_line = tk.Label(
            self.sys_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.detail_line.pack(fill=tk.X)

        self.alleg_frame = tk.Frame(self.sys_frame, bg=bg)
        self.alleg_label = tk.Label(
            self.alleg_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.alleg_label.pack(side=tk.LEFT)
        self.alleg_sep = tk.Label(
            self.alleg_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.alleg_sep.pack(side=tk.LEFT)
        self.sec_label = tk.Label(
            self.alleg_frame, text="", font=font_small, bg=bg, anchor=tk.W,
        )
        self.sec_label.pack(side=tk.LEFT)
        self.alleg_frame.pack(fill=tk.X)

        self.sys_frame.pack(fill=tk.X, pady=(0, 6))

        # === Separator (dynamic — shown only with target/body) ===
        self.sep = tk.Frame(parent, bg="#333333", height=max(1, round(1 * self.overlay._scale_factor)))

        # === Target / body info (dynamic) ===
        self.header = tk.Label(
            parent, text="", font=font_bold, bg=bg, fg=accent, anchor=tk.W,
        )
        self.header.pack(fill=tk.X, pady=(0, 2))

        self.ship_frame = tk.Frame(parent, bg=bg)
        self.name_label = tk.Label(
            self.ship_frame, text="", font=font, bg=bg, fg=fg, anchor=tk.W,
        )
        self.name_label.pack(fill=tk.X)
        self.status_label = tk.Label(
            self.ship_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X)
        self.health_label = tk.Label(
            self.ship_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.health_label.pack(fill=tk.X)
        self.subsystem_label = tk.Label(
            self.ship_frame, text="", font=font_small, bg=bg, fg=dim, anchor=tk.W,
        )
        self.subsystem_label.pack(fill=tk.X)

        self.body_frame = tk.Frame(parent, bg=bg)
        self.body_name_label = tk.Label(
            self.body_frame, text="", font=font, bg=bg, fg=fg, anchor=tk.W,
        )
        self.body_name_label.pack(fill=tk.X)
        self.body_type_label = tk.Label(
            self.body_frame, text="", font=font_small, bg=bg, fg=accent, anchor=tk.W,
        )
        self.body_type_label.pack(fill=tk.X)
        self.body_stats_label = tk.Label(
            self.body_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.body_stats_label.pack(fill=tk.X)
        self.body_atmo_label = tk.Label(
            self.body_frame, text="", font=font_small, bg=bg, fg=dim, anchor=tk.W,
        )
        self.body_atmo_label.pack(fill=tk.X)
        self.body_materials_label = tk.Label(
            self.body_frame, text="", font=font_small, bg=bg, fg=fg, anchor=tk.W,
            justify=tk.LEFT,
        )
        self.body_materials_label.pack(fill=tk.X)



        # === State ===
        self._mode = None
        self._current_body = ""
        self._alive = True

        # System / route state
        self.current_system = ""
        self._system_faction = ""
        self._system_allegiance = ""
        self._system_security = ""
        self._system_power = ""
        self.commander_name = ""
        self.route = []
        self.route_idx = -1
        self.stats = {"jumps": 0, "distance_ly": 0.0}
        self._navroute_mtime = 0

        for evt in ("ShipTargeted", "FSDJump",
                     "Location", "LoadGame", "SupercruiseExit",
                     "SupercruiseEntry", "ApproachBody", "LeaveBody",
                     "Touchdown", "Liftoff", "Scan",
                     "NavRoute", "Route", "NavRouteClear", "StartJump"):
            event_bus.subscribe(f"journal:{evt}", self._handler)

        self._read_navroute()
        self._update_sys_display()
        self.overlay.schedule(1000, self._poll_body)

    def _update_dynamic_visibility(self):
        dynamic = self.pcfg.get("dynamic", False)
        if dynamic:
            visible = self._mode in ("ship", "body")
            self.win.attributes("-alpha", 1.0 if visible else 0.0)
        else:
            self.win.attributes("-alpha", 1.0)

    def on_unload(self):
        self._alive = False
        for evt in ("ShipTargeted", "FSDJump",
                     "Location", "LoadGame", "SupercruiseExit",
                     "SupercruiseEntry", "ApproachBody", "LeaveBody",
                     "Touchdown", "Liftoff", "Scan",
                     "NavRoute", "Route", "NavRouteClear", "StartJump"):
            self.event_bus.unsubscribe(f"journal:{evt}", self._handler)
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _clean_security(raw):
        if not raw or not isinstance(raw, str):
            return "--"
        for prefix in ["$GALAXY_MAP_INFO_state_", "$GALAXY_MAP_INFO_",
                        "$SYSTEM_SECURITY_", "$SYSTEM_SECURITY_state_",
                        "$SystemSecurity_"]:
            if raw.startswith(prefix):
                raw = raw[len(prefix):]
                break
        return raw.replace(";", "").replace("_", " ").strip().title()

    def _extract_system_info(self, data):
        faction_info = data.get("SystemFaction", {}) or {}
        self._system_faction = (
            faction_info.get("Name", "") if isinstance(faction_info, dict) else ""
        )
        raw_align = data.get("SystemAllegiance", "")
        self._system_allegiance = (
            self._clean_security(raw_align)
            if isinstance(raw_align, str) and raw_align.startswith("$")
            else raw_align
        )
        self._system_security = self._clean_security(data.get("SystemSecurity", ""))
        self._system_power = data.get("Power", "")

    # ── Route ──────────────────────────────────────────────────

    def _read_navroute(self):
        nav_path = os.path.join(self.journal_dir, "NavRoute.json")
        if not os.path.exists(nav_path):
            return
        try:
            mtime = os.path.getmtime(nav_path)
            if mtime == self._navroute_mtime:
                return
            self._navroute_mtime = mtime
            with open(nav_path, encoding="utf-8") as f:
                data = json.load(f)
            self._set_route(data.get("Route", []))
        except (OSError, json.JSONDecodeError):
            pass

    def _set_route(self, entries):
        self.route = []
        for e in entries:
            name = e.get("StarSystem", "")
            if not name:
                continue
            self.route.append({
                "name": name,
                "star_class": e.get("StarClass", ""),
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

    def _route_next(self):
        if self.route_idx < 0:
            return self.route[0] if self.route else None
        idx = self.route_idx + 1
        return self.route[idx] if idx < len(self.route) else None

    def _route_dest(self):
        return self.route[-1] if self.route else None

    def _route_remaining(self):
        if self.route_idx < 0:
            return len(self.route) - 1 if self.route else 0
        return max(0, len(self.route) - self.route_idx - 1)

    # ── Journal events ─────────────────────────────────────────

    def on_event(self, event, data):
        if event in ("journal:FSDJump", "journal:Location"):
            self.current_system = data.get("StarSystem", "")
            self._extract_system_info(data)
            if event == "journal:FSDJump":
                jd = data.get("JumpDist", 0)
                self.stats["jumps"] += 1
                self.stats["distance_ly"] += jd
            self._update_route_idx()
            self._read_navroute()
            self._update_sys_display()

            if event == "journal:FSDJump":
                self._current_body = ""
                self._mode = None
                self._hide_dynamic()

        elif event == "journal:LoadGame":
            name = data.get("Commander", "")
            if name:
                self.commander_name = name
                self._update_sys_display()

        elif event in ("journal:NavRoute", "journal:Route"):
            self._set_route(data.get("Route", []))
            self._update_sys_display()

        elif event == "journal:NavRouteClear":
            self.route = []
            self.route_idx = -1
            self._navroute_mtime = 0
            self._update_sys_display()

        elif event == "journal:StartJump":
            pass

        elif event == "journal:ShipTargeted":
            if data.get("TargetLocked", False):
                self._show_ship(data)
            else:
                self._try_body()
            return

        elif event == "journal:SupercruiseExit":
            body = data.get("Body", "")
            if body:
                self._current_body = body
            return
        elif event == "journal:SupercruiseEntry":
            self._current_body = ""
            self._try_body()
            return
        elif event == "journal:ApproachBody":
            self._current_body = data.get("Body", "")
            self._try_body()
            return
        elif event == "journal:LeaveBody":
            self._current_body = ""
            self._try_body()
            return
        elif event == "journal:Touchdown":
            body = data.get("BodyName", "")
            if body:
                self._current_body = body
                self._try_body()
            return
        elif event == "journal:Liftoff":
            self._try_body()
            return
        elif event == "journal:Scan":
            if self._mode == "body" and data.get("BodyName", "") == self._current_body:
                self._show_body(self._current_body)

    def _try_body(self):
        if self._mode == "ship":
            return
        body = self._current_body
        if not body and self.status and self.status.body_name:
            body = self.status.body_name
        if body:
            self._show_body(body)
        else:
            self._hide_dynamic()

    def _poll_body(self):
        if not self._alive:
            return
        try:
            self._read_navroute()
            self._update_sys_display()
            body = self.status.body_name if self.status else None
            if body and body != self._current_body:
                self._current_body = body
                if self._mode != "ship":
                    self._show_body(body)
            elif not body and self._current_body:
                self._current_body = ""
                if self._mode == "body":
                    self._hide_dynamic()
        except Exception:
            pass
        if self._alive:
            self.overlay.schedule(1000, self._poll_body)

    # ── Dynamic display (ship / FSS / body) ────────────────────

    def _show_ship(self, data):
        self._mode = "ship"
        self.body_frame.pack_forget()
        self.header.config(text="Target")
        self.header.pack(fill=tk.X, pady=(0, 2))
        self.ship_frame.pack(fill=tk.X)

        ship = data.get("Ship_Localised") or data.get("Ship", "")
        pilot = data.get("PilotName_Localised") or data.get("PilotName", "")
        rank = data.get("PilotRank", "")
        faction = data.get("Faction", "")
        legal = data.get("LegalStatus", "")
        shield = data.get("ShieldHealth")
        hull = data.get("HullHealth")
        subsystem = data.get("Subsystem", "")
        sub_health = data.get("SubsystemHealth")

        name_parts = [ship]
        if faction:
            name_parts.append(f"[{faction}]")
        self.name_label.config(text="  ".join(name_parts))

        status_parts = []
        if pilot:
            p = f"{pilot} ({rank})" if rank else pilot
            status_parts.append(p)
        if legal:
            status_parts.append(legal)
        self.status_label.config(text="  ".join(status_parts))

        health_parts = []
        if shield is not None:
            health_parts.append(f"Shield: {shield:.0f}%")
        if hull is not None:
            health_parts.append(f"Hull: {hull:.0f}%")
        self.health_label.config(text="  ".join(health_parts))

        if subsystem:
            sub_text = f"Subsys: {subsystem}"
            if sub_health is not None:
                sub_text += f" ({sub_health:.0f}%)"
            self.subsystem_label.config(text=sub_text)
        else:
            self.subsystem_label.config(text="")

        self.sep.pack(fill=tk.X, pady=(0, 4))
        self._update_dynamic_visibility()
        self.overlay.resize_plugin(self.name)

    def _show_body(self, body_name):
        self._mode = "body"
        self._current_body = body_name
        self.ship_frame.pack_forget()
        self.header.config(text="Target")
        self.header.pack(fill=tk.X, pady=(0, 2))
        self.body_frame.pack(fill=tk.X)

        self.body_name_label.config(text=body_name)
        body_data = self.game.body_data(body_name) if self.game else None

        if body_data:
            pclass = body_data.get("planet_class", "")
            landable = body_data.get("landable", False)
            tf_state = body_data.get("terraform_state", "")

            type_parts = [pclass] if pclass else []
            if landable:
                type_parts.append("Landable")
            if tf_state:
                type_parts.append(tf_state)
            self.body_type_label.config(text=" | ".join(type_parts) if type_parts else "")

            gravity = body_data.get("gravity")
            temp = body_data.get("temperature")
            pressure = body_data.get("surface_pressure")

            stat_parts = []
            if gravity is not None and gravity > 0:
                g_val = gravity / G
                stat_parts.append(f"G: {g_val:.2f}g")
            if temp is not None:
                stat_parts.append(f"Temp: {temp:.0f}K")
            if pressure is not None and pressure > 0:
                if pressure >= 1_000_000:
                    stat_parts.append(f"Press: {pressure / 1_000_000:.2f}M atm")
                elif pressure >= 1_000:
                    stat_parts.append(f"Press: {pressure / 1_000:.2f}k atm")
                else:
                    stat_parts.append(f"Press: {pressure:.2f} atm")

            radius = body_data.get("radius")
            if radius and not gravity:
                stat_parts.append(f"R: {radius / 1000:.0f}km")

            self.body_stats_label.config(text="  ".join(stat_parts))

            atmo = body_data.get("atmosphere", "")
            atmo_comp = body_data.get("atmosphere_composition", [])
            atmo_parts = [atmo] if atmo and atmo != "None" else []
            if atmo_comp:
                comp_strs = []
                for comp in atmo_comp[:4]:
                    aname = comp.get("Name", "")
                    apct = comp.get("Percent", 0)
                    if aname:
                        comp_strs.append(f"{aname} {apct:.1f}%")
                if comp_strs:
                    atmo_parts.append("(" + ", ".join(comp_strs) + ")")
            volc = body_data.get("volcanism", "")
            if volc and volc != "None":
                atmo_parts.append(volc)
            self.body_atmo_label.config(text="  ".join(atmo_parts))

            materials = body_data.get("materials", {})
            if materials:
                mat_cols = []
                sorted_mats = sorted(materials.items(), key=lambda x: -x[1])
                half = (len(sorted_mats) + 1) // 2
                for i in range(half):
                    left = sorted_mats[i]
                    col = f"{left[0].title():12s} {left[1]:.1f}%"
                    if i + half < len(sorted_mats):
                        right = sorted_mats[i + half]
                        col += f"    {right[0].title():12s} {right[1]:.1f}%"
                    mat_cols.append(col)
                self.body_materials_label.config(text="\n".join(mat_cols))
            else:
                self.body_materials_label.config(text="")
        else:
            self.body_type_label.config(text="No scan data")
            self.body_stats_label.config(text="")
            self.body_atmo_label.config(text="")
            self.body_materials_label.config(text="")

        self.sep.pack(fill=tk.X, pady=(0, 4))
        self._update_dynamic_visibility()
        self.overlay.resize_plugin(self.name)

    def _hide_dynamic(self):
        self.ship_frame.pack_forget()
        self.body_frame.pack_forget()
        self.header.pack_forget()
        self.sep.pack_forget()
        self.overlay.resize_plugin(self.name)

    _SEC_COLORS = {"low": "#44ff44", "medium": "#ffff00", "high": "#ff4444"}
    _ALLEG_COLORS = {
        "federation": "#4a90d9",
        "empire": "#c9362b",
        "alliance": "#ffd700",
        "independent": "#888888",
    }

    # ── System / route info (always visible) ───────────────────

    def _update_sys_display(self):
        sys_parts = [f"System: {self.current_system or '--'}"]
        if self._system_power:
            sys_parts.append(self._system_power)
        self.sys_line.config(text="  |  ".join(sys_parts))

        self.detail_line.config(
            text=self._system_faction if self._system_faction else ""
        )

        alleg_color = self._ALLEG_COLORS.get(
            self._system_allegiance.lower(), ""
        ) if self._system_allegiance else ""
        self.alleg_label.config(
            text=self._system_allegiance if self._system_allegiance else "",
            fg=alleg_color if alleg_color else "",
        )

        sec = self._system_security.lower() if self._system_security else ""
        color = self._SEC_COLORS.get(sec, "")
        self.alleg_sep.config(text="  |  " if self._system_security else "")
        self.sec_label.config(
            text=self._system_security if self._system_security else "",
            fg=color if color else "",
        )
        self._update_dynamic_visibility()


