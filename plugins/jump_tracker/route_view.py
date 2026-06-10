import tkinter as tk
from .follow_route import SCOOPABLE

NEUTRON = {"N", "H"}


class RouteView(tk.Canvas):
    _base_height = 56

    def __init__(self, parent, bg="#0d0d1a", scale_factor=1.0, **kwargs):
        self._sf = scale_factor
        self.HEIGHT = max(20, round(self._base_height * self._sf))
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
        if not self._route:
            return
        if w < 60:
            self.update_idletasks()
            w = self.winfo_width()
            if w < 60:
                self.after(50, self._redraw)
                return

        n = len(self._route)
        n_hops = max(n - 1, 1)
        pad = max(4, round(10 * self._sf))
        left = pad
        right = w - pad
        bar_w = right - left
        bar_y = self.HEIGHT * 0.55

        if n_hops > 40:
            self._draw_ticks(left, right, bar_w, bar_y)
        else:
            self._draw_dots(left, right, bar_w, bar_y)

        self._draw_arrow(left, bar_w, bar_y)
        self._draw_names(left, right)

    def _draw_arrow(self, left, bar_w, bar_y):
        n = len(self._route)
        idx = self._current_idx
        sf = self._sf
        next_idx = idx + 1 if idx >= 0 else 0
        if not (0 <= next_idx < n):
            return
        ax = left + (next_idx / (n - 1)) * bar_w if n > 1 else left + bar_w / 2
        ay = bar_y - round(20 * sf)
        ah = max(3, round(7 * sf))
        aw = max(2, round(5 * sf))
        self.create_polygon(
            ax, ay + ah,
            ax - aw, ay,
            ax + aw, ay,
            fill="#ffaa00", outline="",
        )

    def _draw_names(self, left, right):
        n = len(self._route)
        sf = self._sf
        if n == 0:
            return
        fs = max(5, round(7 * sf))
        self.create_text(
            left, self.HEIGHT - 1,
            text=self._route[0].get("name", ""),
            fill="#777777", anchor=tk.SW, font=("Consolas", fs),
        )
        self.create_text(
            right, self.HEIGHT - 1,
            text=self._route[-1].get("name", ""),
            fill="#777777", anchor=tk.SE, font=("Consolas", fs),
        )

    def _draw_dots(self, left, right, bar_w, bar_y):
        n = len(self._route)
        idx = self._current_idx
        sf = self._sf

        xs = [left + (i / (n - 1)) * bar_w for i in range(n)] if n > 1 else [left + bar_w / 2]

        radii = []
        colors = []
        for i in range(n):
            if i < idx:
                radii.append(max(1, round(2.5 * sf)))
                colors.append("#777777")
            elif i == idx:
                radii.append(max(2, round(5 * sf)))
                colors.append("#00d4aa")
            elif i == idx + 1:
                radii.append(max(1.5, round(3.5 * sf)))
                colors.append("#ffaa00")
            else:
                radii.append(max(1.5, round(3 * sf)))
                colors.append("#aa8866")

        lw = max(1, round(2 * sf))
        if n > 1:
            self.create_line(left, bar_y, right, bar_y, fill="#555555", width=lw)

        for i in range(1, n):
            lx = xs[i - 1]
            rx = xs[i]
            if i < idx:
                lc = "#555555"
            elif i == idx:
                lc = "#00d4aa"
            elif i == idx + 1:
                lc = "#cc8844"
            else:
                lc = "#776655"
            self.create_line(lx, bar_y, rx, bar_y, fill=lc, width=lw)

        for i in range(n):
            x = xs[i]
            r = radii[i]
            color = colors[i]
            entry = self._route[i]
            star_class = entry.get("star_class", "")
            outline_color = "#ff8800" if star_class in SCOOPABLE else color
            self.create_oval(x - r, bar_y - r, x + r, bar_y + r,
                             fill=color, outline=outline_color, width=max(1, round(2 * sf)))
            if star_class in NEUTRON:
                nw = max(1, round(2 * sf))
                nh = max(2, round(8 * sf))
                self.create_oval(x - nw, bar_y - nh, x + nw, bar_y + nh, fill="#ff44ff", outline="")

    def _draw_ticks(self, left, right, bar_w, bar_y):
        n = len(self._route)
        idx = self._current_idx
        sf = self._sf
        step = max(1, n // 60)

        for i in range(0, n, step):
            x = left + (i / (n - 1)) * bar_w if n > 1 else left + bar_w / 2

            if i < idx:
                color = "#777777"
                h = max(2, round(4 * sf))
            elif i == idx:
                color = "#00d4aa"
                h = max(4, round(10 * sf))
            elif i == idx + 1:
                color = "#ffaa00"
                h = max(3, round(6 * sf))
            else:
                color = "#aa8866"
                h = max(2, round(4 * sf))

            self.create_line(x, bar_y - h, x, bar_y + h, fill=color, width=max(1, round(1.5 * sf)))
