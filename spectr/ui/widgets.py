from __future__ import annotations

import math
from datetime import datetime, timezone

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QPainter, QPen, QFont, QLinearGradient,
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

CYAN    = "#00ccdd"
ORANGE  = "#ff6600"
BLUE    = "#4488cc"
PURPLE  = "#8855cc"
TEAL    = "#22aa99"
YELLOW  = "#ffbb33"
RED     = "#dd3344"
PINK    = "#cc5577"
GREEN   = "#33bb66"
GRAY    = "#445566"
GRAY_L  = "#667788"
WHITE   = "#dde0e8"
DARK    = "#000000"
DARK2   = "#080808"
DARK3   = "#101010"


def fui_color(index: int) -> str:
    return [CYAN, ORANGE, BLUE, PURPLE, TEAL, YELLOW, RED][index % 7]


class FUIBar(QWidget):
    def __init__(self, color: str = CYAN, width: int = 2, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedHeight(width)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(self._color)
        p.drawRect(self.rect())


class FUIPanel(QFrame):
    """Data panel with semi-transparent dark background, thin border,
    and an optional title with a short underline accent."""

    def __init__(self, title: str = "", color: str = CYAN, parent=None):
        super().__init__(parent)
        self._accent = QColor(color)
        self._border_color = QColor(color)
        self._border_color.setAlpha(60)

        self.setStyleSheet(
            f"background:rgba(0,0,0,180);"
            f"border:1px solid rgba(255,102,0,40);"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(6)

        if title:
            title_row = QHBoxLayout()
            title_row.setSpacing(10)
            self.title_label = QLabel(title.upper())
            self.title_label.setStyleSheet(
                f"color:{color};font-size:11px;font-weight:bold;"
                f"background:transparent;border:none;padding:0;"
                f"letter-spacing:2px;"
            )
            title_row.addWidget(self.title_label)

            accent = QWidget()
            accent.setFixedHeight(2)
            accent.setFixedWidth(24)
            accent.setStyleSheet(f"background:{color};border:none;")
            title_row.addWidget(accent)
            title_row.addStretch()

            outer.addLayout(title_row)

        self._content = QVBoxLayout()
        self._content.setSpacing(6)
        outer.addLayout(self._content)

    def content_layout(self) -> QVBoxLayout:
        return self._content

    def set_accent(self, color: str):
        self._accent = QColor(color)
        self._border_color = QColor(color)
        self._border_color.setAlpha(60)
        self.update()


class FUITab(QPushButton):
    """Minimal sidebar tab. Active: bright text + left accent bar + glow.
    Inactive: dim text with subtle left border."""

    _HEIGHT = 38

    def __init__(self, text: str, color: str = CYAN, parent=None):
        super().__init__(text, parent)
        self._color = QColor(color)
        self._font = QFont("sans-serif", 11)
        self._font.setBold(False)
        self.setCheckable(True)
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(self._font)
        self._glow_effect = None

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        active = self.isChecked()
        hover = self.underMouse()

        if hover and not active:
            p.fillRect(r, QColor(255, 102, 0, 12))

        if active:
            p.setPen(Qt.NoPen)
            p.setBrush(self._color)
            p.drawRect(r.x() + 1, r.y() + 6, 3, r.height() - 12)
            grad = QLinearGradient(r.x(), r.y(), r.x(), r.bottom())
            grad.setColorAt(0, QColor(self._color).lighter(120))
            grad.setColorAt(1, QColor(self._color))
            p.setPen(QPen(QColor(self._color), 1))
            p.drawLine(r.x() + 6, r.bottom() - 1, r.right() - 6, r.bottom() - 1)

        text_color = self._color if active else QColor(70, 80, 100)
        if hover and not active:
            text_color = self._color
        p.setPen(text_color)
        p.setFont(self._font)
        text_rect = r.adjusted(16, 0, -8, 0)
        p.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())


class FUIButton(QPushButton):
    """Futuristic button with thin border, transparent background,
    and fill on hover/active."""

    def __init__(self, text: str, color: str = CYAN, parent=None):
        super().__init__(text, parent)
        self._color = QColor(color)
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        f = QFont("sans-serif", 10)
        f.setBold(True)
        self.setFont(f)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        active = self.isDown() or self.isChecked()
        hover = self.underMouse()

        if active or hover:
            fill = self._color.lighter(130 if active else 160)
            fill.setAlpha(30 if hover else 50)
            p.fillRect(r, fill)

        border_color = self._color
        if not active and not hover:
            border_color = QColor(self._color)
            border_color.setAlpha(100)
        p.setPen(QPen(border_color, 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(r)

        text_color = self._color if (active or hover) else QColor(self._color).darker(140)
        p.setPen(text_color)
        p.setFont(self.font())
        p.drawText(r, Qt.AlignCenter, self.text())


class FUIStatusBar(QWidget):
    """Clean HUD-style top bar with server status and time."""

    def __init__(self, color: str = CYAN, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._show_game = True
        self.setFixedHeight(56)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._accent_bar = FUIBar(color, 2)
        layout.addWidget(self._accent_bar)

        row = QWidget()
        row.setStyleSheet(f"background:rgba(0,0,0,200);")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(20, 6, 20, 8)

        self.status_icon = QLabel("◇")
        self.status_icon.setStyleSheet(
            f"color:{color};font-size:14px;background:transparent;"
        )
        row_layout.addWidget(self.status_icon)

        self.status_text = QLabel("SYS: ONLINE")
        self.status_text.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:bold;background:transparent;"
            f"letter-spacing:1px;"
        )
        row_layout.addWidget(self.status_text)

        row_layout.addStretch()

        self._time_widget = QWidget()
        self._time_widget.setStyleSheet("background:transparent;")
        self._time_widget.setCursor(Qt.PointingHandCursor)
        self._time_widget.installEventFilter(self)
        time_layout = QVBoxLayout(self._time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(0)

        self.game_time_label = QLabel()
        self.game_time_label.setStyleSheet(
            f"color:{GRAY_L};font-size:11px;font-weight:normal;"
            f"background:transparent;letter-spacing:1px;"
        )
        time_layout.addWidget(self.game_time_label)

        self.local_time_label = QLabel()
        self.local_time_label.setStyleSheet(
            f"color:{GRAY_L};font-size:11px;font-weight:normal;"
            f"background:transparent;letter-spacing:1px;"
        )
        time_layout.addWidget(self.local_time_label)

        row_layout.addWidget(self._time_widget)
        layout.addWidget(row)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clocks)
        self._clock_timer.start(1000)
        self._update_clocks()

    def eventFilter(self, obj, event):
        if obj is self._time_widget and event.type() == event.Type.MouseButtonPress:
            self._show_game = not self._show_game
            self._update_clocks()
            return True
        return super().eventFilter(obj, event)

    def set_accent_color(self, color: str):
        self._accent_bar.set_color(color)

    def _update_clocks(self) -> None:
        utc = datetime.now(timezone.utc)
        try:
            game_dt = utc.replace(year=utc.year + 1286)
        except ValueError:
            game_dt = utc.replace(year=utc.year + 1286, day=28)
        self.game_time_label.setText(
            f"GAME  {game_dt.strftime('%Y-%m-%d  %H:%M')}"
        )
        local = datetime.now()
        self.local_time_label.setText(
            f"SYS   {local.strftime('%Y-%m-%d  %H:%M')}"
        )
        self.game_time_label.setVisible(self._show_game)
        self.local_time_label.setVisible(not self._show_game)

    def set_status(self, text: str):
        self.status_text.setText(f"SYS: {text}")

    def set_status_color(self, color: str):
        self.status_text.setStyleSheet(
            f"color:{color};font-size:11px;font-weight:bold;background:transparent;"
            f"letter-spacing:1px;"
        )
        self.status_icon.setStyleSheet(
            f"color:{color};font-size:14px;background:transparent;"
        )


class FUIProgressBar(QWidget):
    """10-segment progress bar with green→yellow→red progression."""

    _SEGMENTS = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 1.0
        self.setFixedHeight(10)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        r = self.rect()

        segs = self._SEGMENTS
        gap = 2
        total_gap = gap * (segs - 1)
        seg_w = (r.width() - total_gap) // segs
        fill_count = round(segs * self._value)

        for i in range(segs):
            sx = r.x() + i * (seg_w + gap)
            sy = r.y() + 1
            sh = r.height() - 2

            if i >= fill_count:
                p.fillRect(sx, sy, seg_w, sh, QColor(8, 8, 8))
                continue

            if i < 3:
                c = QColor(102, 51, 0)
            elif i < 8:
                c = QColor(204, 82, 0)
            else:
                c = QColor(255, 102, 0)
            p.fillRect(sx, sy, seg_w, sh, c)


class FUIContinuousBar(QWidget):
    """Single continuous bar with orange fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 1.0
        self.setFixedHeight(10)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        r = self.rect()

        w = r.width()
        fill_w = int(w * self._value)
        y = r.y() + 1
        h = r.height() - 2

        if fill_w < w:
            p.fillRect(r.x() + fill_w, y, w - fill_w, h, QColor(8, 8, 8))

        if fill_w > 0:
            r_end = int(w * 0.30)
            g_start = int(w * 0.80)

            rw = min(r_end, fill_w)
            if rw > 0:
                p.fillRect(r.x(), y, rw, h, QColor(102, 51, 0))
            if fill_w > r_end:
                yw = min(g_start, fill_w) - r_end
                if yw > 0:
                    p.fillRect(r.x() + r_end, y, yw, h, QColor(204, 82, 0))
            if fill_w > g_start:
                gw = fill_w - g_start
                if gw > 0:
                    p.fillRect(r.x() + g_start, y, gw, h, QColor(255, 102, 0))


_STAR_COLORS: dict[str, str] = {
    "O": "#9bb0ff", "B": "#aabfff", "A": "#cad7ff",
    "F": "#f8f7ff", "G": "#fff4ea", "K": "#ffd2a1",
    "M": "#ffcc6f", "L": "#ff8844", "T": "#ff6633",
    "Y": "#ff4422", "W": "#99ccff",
}

_STAR_RADII: dict[str, float] = {
    "O": 10.0, "B": 7.0, "A": 2.5, "F": 1.4,
    "G": 1.0, "K": 0.7, "M": 0.3, "L": 0.1, "T": 0.08,
    "Y": 0.05, "W": 0.02,
}


class SystemMapWidget(QWidget):
    """Interactive schematic of the current star system."""

    body_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bodies: list[dict] = []
        self._selected: int | None = None
        self._body_rects: list[tuple[dict, int, int, int, int]] = []
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background:#000000;border:1px solid #0e1420;border-radius:4px;")
        self.setCursor(Qt.PointingHandCursor)

    def set_bodies(self, bodies: list[dict]) -> None:
        self._bodies = bodies
        self._selected = None
        self._body_rects.clear()
        self.update()

    def mousePressEvent(self, ev) -> None:
        mx, my = ev.position().x(), ev.position().y()
        for body, bx, by, bw, bh in self._body_rects:
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                self._selected = body.get("BodyId")
                self.update()
                self.body_clicked.emit(body)
                return
        self._selected = None
        self.update()
        self.body_clicked.emit({})

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.fillRect(r, QColor(0, 0, 0))

        cx, cy = r.width() // 2, r.height() // 2
        if not self._bodies:
            p.setPen(QColor(*_hex_rgb(GRAY)))
            p.setFont(QFont("monospace", 10))
            p.drawText(r, Qt.AlignCenter, "No body data available")
            return

        self._body_rects.clear()

        stars = [b for b in self._bodies if b.get("StarType")]
        planets = [b for b in self._bodies if not b.get("StarType")]

        if len(stars) == 1:
            sx, sy = cx, cy
            sr = max(14, min(28, int(self._radius_for_star(stars[0]) * 14)))
            self._draw_star(p, stars[0], sx, sy, sr)
        elif len(stars) >= 2:
            orbit_r = min(cx, cy) * 0.45
            for i, s in enumerate(stars):
                angle = (i * 2 * math.pi) / len(stars) - math.pi / 2
                sx = int(cx + orbit_r * math.cos(angle))
                sy = int(cy + orbit_r * math.sin(angle))
                sr = max(10, min(20, int(self._radius_for_star(s) * 10)))
                self._draw_star(p, s, sx, sy, sr)
        elif stars:
            sr = max(14, min(28, int(self._radius_for_star(stars[0]) * 14)))
            self._draw_star(p, stars[0], cx, cy, sr)

        max_orbit = max(
            (b.get("SemiMajorAxis") or b.get("DistanceFromArrivalLs") or 1)
            for b in planets
        ) if planets else 1

        base_r = max(14, min(28, int(self._radius_for_star(stars[0]) * 14))) if stars else 14
        min_orbit_r = base_r + 30 if len(stars) <= 1 else min(cx, cy) * 0.6
        max_orbit_r = min(cx, cy) - 30
        if max_orbit_r < min_orbit_r + 20:
            max_orbit_r = min_orbit_r + 60

        for b in planets:
            dist = b.get("SemiMajorAxis") or b.get("DistanceFromArrivalLs") or 0
            if dist <= 0:
                dist = max_orbit * 0.5
            orbit_r = min_orbit_r + (max_orbit_r - min_orbit_r) * (dist / max_orbit) if max_orbit > 0 else min_orbit_r + 40

            p.setPen(QPen(QColor(30, 40, 55), 1, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(cx - int(orbit_r), cy - int(orbit_r),
                          int(orbit_r) * 2, int(orbit_r) * 2)

            body_radius = self._radius_for_planet(b)
            angle = (b.get("BodyId", 0) * 2.399) % (2 * math.pi)
            bx = int(cx + orbit_r * math.cos(angle) - body_radius)
            by = int(cy + orbit_r * math.sin(angle) - body_radius)
            bw = body_radius * 2
            bh = body_radius * 2

            bcolor = QColor(self._planet_color(b))
            if b.get("BodyId") == self._selected:
                sel_pen = QPen(QColor(ORANGE), 2)
                p.setPen(sel_pen)
                p.setBrush(bcolor)
                p.drawEllipse(bx - 3, by - 3, bw + 6, bh + 6)
            else:
                p.setPen(QPen(QColor(20, 20, 20)))
                p.setBrush(bcolor)
                p.drawEllipse(bx, by, bw, bh)

            if b.get("Landable"):
                p.setPen(QPen(QColor(YELLOW), 1))
                p.setBrush(Qt.NoBrush)
                p.drawRect(bx + bw // 2 - 2, by + bh + 2, 4, 4)

            self._body_rects.append((b, bx, by, bw, bh))

            name = b.get("Name", "")
            short = name.split()[-1] if name else ""
            if len(short) > 8:
                short = short[:7] + "."
            if short:
                p.setPen(QColor(150, 160, 170))
                p.setFont(QFont("monospace", 6))
                p.drawText(bx, by + bh + 8, bw, 10, Qt.AlignCenter, short)

    def _radius_for_star(self, star: dict) -> float:
        return _STAR_RADII.get(star.get("StarType", "G"), 1.0)

    def _draw_star(self, p: QPainter, star: dict, cx: int, cy: int, radius: int) -> None:
        stype = star.get("StarType", "G")
        scol = QColor(_STAR_COLORS.get(stype, "#fff4ea"))
        glow = QColor(scol)
        glow.setAlpha(40)
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - radius - 6, cy - radius - 6,
                      (radius + 6) * 2, (radius + 6) * 2)
        p.setBrush(scol)
        p.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        self._body_rects.append((star, cx - radius, cy - radius,
                                 radius * 2, radius * 2))
        label = star.get("Name", "Star").split()[-1]
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("monospace", 7))
        p.drawText(cx - radius, cy + radius + 12,
                   radius * 2, 14, Qt.AlignCenter, label)

    def _radius_for_planet(self, body: dict) -> int:
        pclass = (body.get("PlanetClass") or "").lower()
        mass = body.get("MassEm") or body.get("Mass") or 1.0
        if "gas giant" in pclass or "jovian" in pclass:
            return max(6, min(12, int(3 + mass * 1.5)))
        if "earthlike" in pclass or "water" in pclass:
            return max(4, min(9, int(2 + mass * 2)))
        return max(3, min(7, int(2 + mass * 2)))

    def _planet_color(self, body: dict) -> str:
        pclass = (body.get("PlanetClass") or "").lower()
        if "earthlike" in pclass:
            return "#55aaff"
        if "water world" in pclass or "water" in pclass:
            return "#3388cc"
        if "gas giant" in pclass:
            if "ammonia" in pclass:
                return "#ccaa33"
            if "water" in pclass:
                return "#88aadd"
            return "#aa8844"
        if "rocky" in pclass or "rock" in pclass:
            return "#887766"
        if "metal" in pclass:
            return "#999999"
        if "icy" in pclass:
            return "#aaccdd"
        if "snowball" in pclass:
            return "#ccddff"
        if "high" in pclass:
            return "#aa6633"
        if "volcanic" in pclass or "lava" in pclass:
            return "#cc3300"
        return "#665544"


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


LcarsBlock = FUIPanel
LcarsBar = FUIBar
LcarsTab = FUITab
LcarsPill = FUIButton
LcarsStatusBar = FUIStatusBar
HealthBar = FUIProgressBar
lcars_color = fui_color
