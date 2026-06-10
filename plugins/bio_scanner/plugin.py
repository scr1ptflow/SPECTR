import tkinter as tk
from core.plugin_base import Plugin


class BioScanner(Plugin):
    name = "Bio Samples"
    version = "1.0.0"
    description = "Shows bio samples with 3/3 scan gauge per species"

    PIP_W = 22
    PIP_H = 16
    PIP_GAP = 5

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.event_bus = event_bus
        self.game = game
        self.status = status
        self._handler = self.on_event

        compass_h = 150
        gap = 7
        self.win = overlay.create_plugin_window(
            self.name, position="center-top", width=280, height=60
        )
        self.win._pl_oy = compass_h + gap
        parent = self.win.container
        self.win.attributes("-alpha", 1.0)

        self.win.update_idletasks()
        screen_w = self.win.winfo_screenwidth()
        x = (screen_w - 280) // 2
        self.win.geometry(f"280x60+{x}+{compass_h + gap}")

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            config.get("overlay", "font_size", default=11),
        )
        bg = config.get("overlay", "bg_color", default="#0a0f08")
        self._accent = config.get("overlay", "accent_color", default="#00d4aa")

        self._label = tk.Label(
            parent, text="-- No Target --", font=font,
            bg=bg, fg=self._accent, anchor=tk.W,
        )
        self._label.pack(fill=tk.X)

        self._canvas = tk.Canvas(
            parent, width=260, height=22, bg=bg,
            highlightthickness=0, bd=0,
        )
        self._canvas.pack(fill=tk.X)

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
        cw = 260
        ch = 22
        total_w = 3 * self.PIP_W + 2 * self.PIP_GAP
        start_x = (cw - total_w) // 2
        pip_y = (ch - self.PIP_H) // 2

        for i in range(3):
            x = start_x + i * (self.PIP_W + self.PIP_GAP)
            fill = self._accent if i < count else "#2a2a2a"
            self._canvas.create_rectangle(
                x, pip_y, x + self.PIP_W, pip_y + self.PIP_H,
                fill=fill, outline="#555555", width=1,
            )

        self._canvas.create_text(
            cw // 2, ch // 2 + self.PIP_H // 2 + 2,
            text=f"{count}/3",
            fill="#888888", font=("Consolas", 8),
        )
