import tkinter as tk
from core.plugin_base import Plugin


class BioScanner(Plugin):
    name = "Bio Samples"
    version = "1.0.0"
    description = "Shows bio samples with 3/3 scan gauge per species"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event

        self.pcfg = config.plugin_config(self.name)
        sf = self.overlay._scale_factor
        self.PIP_W = max(10, round(26 * sf))
        self.PIP_H = max(10, round(26 * sf))
        self.PIP_GAP = max(2, round(6 * sf))
        win_pos = self.pcfg.get("window_position", "top")
        self.win = overlay.create_plugin_window(
            self.name, position=win_pos, width=400, height=80
        )
        parent = self.win.container
        self.win.attributes("-alpha", 1.0)

        self.win.update_idletasks()

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,
        )
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        self._accent = config.get("overlay", "accent_color", default="#00d4aa")

        self._label = tk.Label(
            parent, text="-- No Target --", font=font,
            bg=bg, fg=self._accent, anchor=tk.W,
        )
        self._label.pack(fill=tk.X)

        self._canvas = tk.Canvas(
            parent, height=max(16, round(32 * sf)), bg=bg,
            highlightthickness=0, bd=0,
        )
        self._canvas.pack(fill=tk.X)

        self.win.update_idletasks()

        self.current_body = ""
        self._current = None

        self._draw(0)

        event_bus.subscribe("journal:ScanOrganic", self._handler)
        event_bus.subscribe("journal:FSDJump", self._handler)
        event_bus.subscribe("journal:Location", self._handler)
        event_bus.subscribe("journal:ApproachBody", self._handler)
        event_bus.subscribe("journal:LeaveBody", self._handler)

    def on_unload(self):
        if hasattr(self, "win"):
            try:
                self.win.destroy()
            except Exception:
                pass
        for ev in ("journal:ScanOrganic", "journal:FSDJump", "journal:Location",
                    "journal:ApproachBody", "journal:LeaveBody"):
            self.event_bus.unsubscribe(ev, self._handler)

    def on_event(self, event, data):
        if event in ("journal:FSDJump", "journal:Location"):
            self.current_body = ""
            self._current = None
            self._label.config(text="-- No Target --")
            self._draw(0)
            self.overlay.resize_plugin(self.name)
            return

        if event == "journal:ApproachBody":
            self.current_body = data.get("Body", "")
            return

        if event == "journal:LeaveBody":
            self.current_body = ""
            return

        if event == "journal:ScanOrganic":
            self._on_scan(data)

    def _on_scan(self, data):
        species = data.get("Species_Localised", "") or data.get("Species", "")
        body = data.get("Body", self.current_body)
        name = species
        key = f"{body}|{name}"

        if self._current and self._current["key"] == key:
            self._current["count"] = min(self._current["count"] + 1, 3)
        else:
            self._current = {"key": key, "name": name, "count": 1}

        self._label.config(text=self._current["name"])
        self._draw(self._current["count"])

    def _draw(self, count):
        self._canvas.delete("all")
        cw = self._canvas.winfo_width()
        if cw < 10:
            cw = self._canvas.master.winfo_width() - 20
        if cw < 10:
            cw = round(380 * self.overlay._scale_factor)
        total_w = 3 * self.PIP_W + 2 * self.PIP_GAP
        start_x = (cw - total_w) // 2
        sf = self.overlay._scale_factor
        py = max(1, round(2 * sf))
        lw = max(1, round(2 * sf))

        for i in range(3):
            x = start_x + i * (self.PIP_W + self.PIP_GAP)
            fill = self._accent if i < count else "#444444"
            outline = self._accent if i < count else "#777777"
            self._canvas.create_rectangle(
                x, py, x + self.PIP_W, py + self.PIP_H,
                fill=fill, outline=outline, width=lw,
            )
