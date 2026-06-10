import tkinter as tk
import math
from core.plugin_base import Plugin
from core.status import HAS_LAT_LONG, SUPERCRUISE, LANDED, IN_SRV, ON_FOOT


class GroundTarget(Plugin):
    name = "Compass"
    version = "1.0.0"
    description = "Surface heading compass with ruler bar and optional target bearing"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event

        self.overlay = overlay
        self.pcfg = config.plugin_config(self.name)
        win_pos = self.pcfg.get("window_position", "top")
        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=400, height=150,
        )
        parent = self.win.container

        self.font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        self.font_small = (self.font[0], max(self.font[1] - 1, 8))
        self._bg = config.get("overlay", "bg_color", default="#0a0f08")
        self._accent = config.get("overlay", "accent_color", default="#00d4aa")
        self._fg = config.get("overlay", "fg_color", default="#e0e0e0")
        sf = self.overlay._scale_factor
        bg = self._bg
        fg = self._fg

        self.target_lat = None
        self.target_lon = None
        self.target_name = ""
        self._last_bearing = None
        self._last_show_target = False

        self.info_label = tk.Label(
            parent, text="", font=self.font_small, bg=bg, fg=fg, anchor=tk.W,
        )
        self.info_label.pack(fill=tk.X)

        self.target_label = tk.Label(
            parent, text="", font=self.font, bg=bg, fg=self._accent, anchor=tk.W,
        )
        self.bearing_label = tk.Label(
            parent, text="", font=self.font, bg=bg, fg=fg, anchor=tk.CENTER,
        )

        self.compass_w = max(80, round(260 * sf))
        self.compass_h = max(20, round(55 * sf))
        self.canvas = tk.Canvas(
            parent, width=self.compass_w, height=self.compass_h, bg=bg,
            highlightthickness=0, bd=0,
        )

        self.win.attributes("-alpha", 1.0)
        self._visible = False

        event_bus.subscribe("status", self._handler)

        self._update_display()

    def on_unload(self):
        self.event_bus.unsubscribe("status", self._handler)
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass

    def set_target(self, lat, lon, name=""):
        self.target_lat = lat
        self.target_lon = lon
        self.target_name = name
        self._update_display()

    def clear_target(self):
        self.target_lat = None
        self.target_lon = None
        self.target_name = ""
        self._update_display()

    def _is_near_surface(self, s):
        if s is None:
            return False
        flags = s.flags
        if flags & (ON_FOOT | IN_SRV | LANDED):
            return True
        if flags & HAS_LAT_LONG:
            return True
        if (flags & SUPERCRUISE) and s.altitude is not None and s.altitude < 1000000:
            return True
        return False

    def _format_altitude(self, alt):
        if alt is None:
            return ""
        if abs(alt) >= 1000:
            return f"Alt: {alt / 1000:,.2f} km"
        return f"Alt: {alt:,.0f} m"

    def _format_distance(self, dist):
        if dist is None:
            return ""
        if dist >= 1000:
            return f"{dist / 1000:.2f} km"
        return f"{dist:.0f} m"

    def _has_pos(self, s):
        if s is None:
            return False
        if s.latitude is None or s.longitude is None:
            return False
        return math.isfinite(s.latitude) and math.isfinite(s.longitude)

    def _valid_coord(self, val):
        if val is None:
            return False
        try:
            f = float(val)
            return math.isfinite(f)
        except (ValueError, TypeError):
            return False

    def on_event(self, event, data):
        if event == "status":
            self._update_display()

    def _update_display(self):
        s = self.status
        if s is None:
            return

        show = self._has_pos(s) and self._is_near_surface(s)

        if show:
            heading = s.heading
            alt = s.altitude
            has_target = (self._valid_coord(self.target_lat)
                          and self._valid_coord(self.target_lon))

            info_parts = []
            if heading is not None:
                info_parts.append(f"H: {heading:.1f}\u00b0")
            if alt is not None:
                info_parts.append(self._format_altitude(alt))
            if s.latitude is not None and s.longitude is not None:
                info_parts.append(f"Pos: {s.latitude:.4f}, {s.longitude:.4f}")
            self.info_label.config(text="  ".join(info_parts))

            bearing = None
            distance = None
            if has_target:
                bearing = s.bearing_to(self.target_lat, self.target_lon)
                distance = s.distance_to(self.target_lat, self.target_lon)

                if self.target_name:
                    self.target_label.config(text=f"Target: {self.target_name}")
                else:
                    self.target_label.config(
                        text=f"Target: {self.target_lat:.4f}, {self.target_lon:.4f}"
                    )
                self.target_label.pack(fill=tk.X)

                dist_text = self._format_distance(distance)
                if bearing is not None and dist_text:
                    self.bearing_label.config(
                        text=f"Brg: {bearing:.1f}\u00b0  Dist: {dist_text}"
                    )
                elif bearing is not None:
                    self.bearing_label.config(text=f"Brg: {bearing:.1f}\u00b0")
                elif dist_text:
                    self.bearing_label.config(text=f"Dist: {dist_text}")
                else:
                    self.bearing_label.config(text="")
                self.bearing_label.pack(fill=tk.X)
            else:
                self.target_label.pack_forget()
                self.bearing_label.pack_forget()

            self.canvas.pack(pady=4)
            self._draw_compass(heading, has_target, bearing)
            self._last_bearing = bearing if has_target else None
            self._last_show_target = has_target

            if not self._visible:
                self._visible = True
                self.win.attributes("-alpha", 1.0)
        else:
            self.info_label.config(text="")
            self.target_label.pack_forget()
            self.bearing_label.pack_forget()
            self.canvas.pack_forget()
            if self._visible:
                self._visible = False
                self.win.attributes("-alpha", 0.0)

        self.overlay.resize_plugin(self.name)

    def _draw_compass(self, heading, has_target=False, bearing=None):
        c = self.canvas
        c.delete("all")
        w = self.compass_w
        h = self.compass_h
        bg = self._bg
        sf = self.overlay._scale_factor

        c.create_rectangle(0, 0, w, h, fill=bg, outline="")

        view_width = max(60, round(180 * sf))
        ppd = w / view_width
        tick_top = max(2, round(6 * sf))
        tick_bot = h - max(2, round(6 * sf))

        if heading is None:
            c.create_text(w / 2, h // 2, text="--", fill="#888888",
                          font=("Consolas", max(6, round(10 * sf))), anchor=tk.CENTER)
            return

        start_deg = int((heading - view_width / 2) // 10) * 10
        end_deg = int((heading + view_width / 2) // 10) * 10 + 10

        for deg in range(start_deg, end_deg + 10, 10):
            rel = deg - heading
            x = w / 2 + rel * ppd
            if x < 0 or x > w:
                continue
            if deg % 30 == 0:
                c.create_line(x, tick_top, x, tick_bot, fill="#555555", width=max(1, round(sf)))
                c.create_text(x, h - max(1, round(2 * sf)), text=f"{deg % 360:03d}", fill="#888888",
                              font=("Consolas", max(5, round(7 * sf))), anchor=tk.S)
            else:
                c.create_line(x, tick_top + max(2, round(6 * sf)), x, tick_bot - max(2, round(6 * sf)), fill="#444444", width=max(1, round(sf)))

        cx = w / 2
        c.create_line(cx, 0, cx, h, fill=self._accent, width=max(1, round(2 * sf)))
        c.create_text(cx, 0, text="\u25b2", fill=self._accent,
                      font=("Consolas", max(5, round(8 * sf))), anchor=tk.N)

        if has_target and bearing is not None:
            rel = bearing - heading
            while rel > 180:
                rel -= 360
            while rel < -180:
                rel += 360
            tx = w / 2 + rel * ppd
            if 0 <= tx <= w:
                c.create_text(tx, 0, text="\u25bc", fill="#ff4444",
                              font=("Consolas", max(6, round(10 * sf))), anchor=tk.N)
                c.create_line(tx, max(3, round(10 * sf)), tx, h - max(1, round(2 * sf)), fill="#ff4444", width=max(1, round(sf)), dash=(max(2, round(3 * sf)), max(1, round(2 * sf))))
