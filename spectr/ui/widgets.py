from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt, QTimer
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


LcarsBlock = FUIPanel
LcarsBar = FUIBar
LcarsTab = FUITab
LcarsPill = FUIButton
LcarsStatusBar = FUIStatusBar
HealthBar = FUIProgressBar
lcars_color = fui_color
