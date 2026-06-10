import tkinter as tk
from .follow_route import SCOOPABLE

NEUTRON = {"N", "H"}


class RouteView(tk.Canvas):
    HEIGHT = 56

    def __init__(self, parent, bg="#0d0d1a", **kwargs):
        super().__init__(
            parent, height=self.HEIGHT, bg=bg,
            highlightthickness=0, bd=0, **kwargs
        )
        self._route = []
        self._current_idx = -1
        self._total_dist = 0.0
        self._jump_range = 0.0
        self.bind("<Configure>", lambda e: self._redraw())

    def set_route(self, route, current_idx, total_dist=0.0, jump_range=0.0):
        self._route = route
        self._current_idx = current_idx
        self._total_dist = total_dist
        self._jump_range = jump_range
        self._redraw()

    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        if w < 60 or len(self._route) < 2:
            return

        n = len(self._route)
        n_hops = n - 1
        pad = 10
        left = pad
        right = w - pad
        bar_w = right - left
        bar_y = self.HEIGHT * 0.55

        if n_hops > 40:
            self._draw_ticks(left, right, bar_w, bar_y)
        else:
            self._draw_dots(left, right, bar_w, bar_y)

    def _draw_dots(self, left, right, bar_w, bar_y):
        n = len(self._route)
        idx = self._current_idx

        xs = [left + (i / (n - 1)) * bar_w for i in range(n)]

        radii = []
        colors = []
        for i in range(n):
            if i < idx:
                radii.append(2.5)
                colors.append("#555555")
            elif i == idx:
                radii.append(5)
                colors.append("#00d4aa")
            elif i == idx + 1:
                radii.append(3.5)
                colors.append("#ffaa00")
            else:
                radii.append(3)
                colors.append("#776644")

        if n > 1:
            self.create_line(left, bar_y, right, bar_y, fill="#333333", width=2)

        for i in range(1, n):
            lx = xs[i - 1]
            rx = xs[i]
            if i < idx:
                line_color = "#444444"
            elif i == idx:
                line_color = "#00d4aa"
            elif i == idx + 1:
                line_color = "#886644"
            else:
                line_color = "#554433"
            self.create_line(lx, bar_y, rx, bar_y, fill=line_color, width=2)

        for i in range(n):
            x = xs[i]
            r = radii[i]
            color = colors[i]
            entry = self._route[i]
            star_class = entry.get("star_class", "")
            is_neutron = star_class in NEUTRON

            self.create_oval(x - r, bar_y - r, x + r, bar_y + r, fill=color, outline=color)

            if star_class in SCOOPABLE:
                self.create_arc(
                    x - 5, bar_y - 9, x + 5, bar_y - 1,
                    start=0, extent=180, fill="#44aaff", outline=""
                )

            if is_neutron:
                self.create_oval(x - 2, bar_y - 8, x + 2, bar_y + 8, fill="#ff44ff", outline="")

        # --- Arrow above next jump ---
        next_idx = idx + 1 if idx >= 0 else 0
        if 0 <= next_idx < n:
            ax = left + (next_idx / (n - 1)) * bar_w
            ay = bar_y - 12
            arrow_color = "#ffaa00"
            self.create_polygon(
                ax, ay - 7,
                ax - 5, ay,
                ax + 5, ay,
                fill=arrow_color, outline="",
            )
            next_name = self._route[next_idx].get("name", "")
            if next_name:
                self.create_text(
                    ax, ay - 11,
                    text=next_name,
                    fill=arrow_color, anchor=tk.S,
                    font=("Consolas", 7, "bold"),
                )

        # --- First & last system names ---
        if n > 0:
            self.create_text(
                left, self.HEIGHT - 1,
                text=self._route[0].get("name", ""),
                fill="#777777", anchor=tk.SW, font=("Consolas", 7)
            )
            self.create_text(
                right, self.HEIGHT - 1,
                text=self._route[-1].get("name", ""),
                fill="#777777", anchor=tk.SE, font=("Consolas", 7)
            )

    def _draw_ticks(self, left, right, bar_w, bar_y):
        n = len(self._route)
        idx = self._current_idx
        step = max(1, n // 60)

        # --- Arrow above next tick ---
        next_idx = idx + 1 if idx >= 0 else 0
        if 0 <= next_idx < n:
            ax = left + (next_idx / (n - 1)) * bar_w
            ay = bar_y - 12
            arrow_color = "#ffaa00"
            self.create_polygon(
                ax, ay - 7,
                ax - 5, ay,
                ax + 5, ay,
                fill=arrow_color, outline="",
            )
            next_name = self._route[next_idx].get("name", "")
            if next_name:
                self.create_text(
                    ax, ay - 11,
                    text=next_name,
                    fill=arrow_color, anchor=tk.S,
                    font=("Consolas", 7, "bold"),
                )

        for i in range(0, n, step):
            x = left + (i / (n - 1)) * bar_w

            if i < idx:
                color = "#555555"
                h = 4
            elif i == idx:
                color = "#00d4aa"
                h = 10
            elif i == idx + 1:
                color = "#ffaa00"
                h = 6
            else:
                color = "#776644"
                h = 4

            self.create_line(x, bar_y - h, x, bar_y + h, fill=color, width=1.5)

        if n > 0:
            self.create_text(
                left, self.HEIGHT - 1,
                text=self._route[0].get("name", ""),
                fill="#777777", anchor=tk.SW, font=("Consolas", 7)
            )
            self.create_text(
                right, self.HEIGHT - 1,
                text=self._route[-1].get("name", ""),
                fill="#777777", anchor=tk.SE, font=("Consolas", 7)
            )
