from __future__ import annotations

import logging
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from spectr.config import load_config
from spectr.edsm import EDSMClient
from spectr.journal import JournalReader
from spectr.server_status import ServerStatusChecker
from spectr.ui.panels import (
    CaptainsLogPanel, CommanderPanel, DashboardPanel, EngineeringPanel,
    LaboratoryPanel, LocationPanel, MissionsPanel, ScannerPanel,
    SettingsPanel, ShipPanel,
)
from spectr.ui.widgets import (
    CYAN, ORANGE, BLUE, PURPLE, TEAL, YELLOW, RED, PINK, GRAY, GREEN,
    DARK,
    FUITab, FUIStatusBar,
)

log = logging.getLogger(__name__)

_STATUS_COLOR = {
    "ONLINE":      CYAN,
    "OFFLINE":     RED,
    "MAINTENANCE": ORANGE,
    "UNKNOWN":     GRAY,
}

TAB_ITEMS = [
    ("dashboard",    "NEWS",         CYAN),
    ("commander",    "COMMANDER",    ORANGE),
    ("ship",         "SHIP",         BLUE),
    ("location",     "LOCATION",     PURPLE),
    ("scanner",      "SCANNER",      CYAN),
    ("missions",     "MISSIONS",     TEAL),
    ("engineering",  "ENGINEERING",  GREEN),
    ("laboratory",   "LABORATORY",   YELLOW),
    ("settings",     "SETTINGS",     GRAY),
    ("captainslog",  "LOG",          PINK),
]

TAB_PANELS = {
    "dashboard":    DashboardPanel,
    "commander":    CommanderPanel,
    "ship":         ShipPanel,
    "location":     LocationPanel,
    "scanner":      ScannerPanel,
    "missions":     MissionsPanel,
    "engineering":  EngineeringPanel,
    "laboratory":   LaboratoryPanel,
    "settings":     SettingsPanel,
    "captainslog":  CaptainsLogPanel,
}

_TAB_COLORS = {k: c for k, _, c in TAB_ITEMS}


class MainWindow(QMainWindow):
    """FUI-themed main window with a tabbed sidebar and stacked panels."""

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.journal = JournalReader(self.config.get("journal_path", ""))
        self.edsm = EDSMClient()
        self._server_status = "UNKNOWN"
        self._current_tab = "dashboard"
        self._settings = QSettings("SPECTR", "SPECTR")
        self._setup_ui()
        self.apply_font_size()
        self._restore_window_state()
        self._start_status_checker()
        log.info("SPECTR started — journal path: %s", self.config.get("journal_path", "(unset)"))

    def _setup_ui(self):
        self.setWindowTitle("SPECTR  ◆  Elite Dangerous Companion")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 860)

        central = QWidget()
        central.setStyleSheet(f"background:{DARK};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.status_bar = FUIStatusBar(ORANGE)
        root.addWidget(self.status_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet(f"background:{DARK};")
        sidebar_widget.setFixedWidth(195)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 12, 0, 12)
        sidebar_layout.setSpacing(1)

        self.tab_buttons: list[FUITab] = []
        self._tab_map: dict[str, FUITab] = {}

        for tab_id, label, color in TAB_ITEMS:
            btn = FUITab(label, color)
            btn.clicked.connect(lambda checked, tid=tab_id: self._switch_tab(tid))
            sidebar_layout.addWidget(btn)
            self.tab_buttons.append(btn)
            self._tab_map[tab_id] = btn

        sidebar_layout.addStretch()

        body.addWidget(sidebar_widget)

        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background:rgba(255,102,0,30);")
        body.addWidget(sep)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{DARK};")
        self.panels: dict[str, QWidget] = {}
        for tab_id, panel_cls in TAB_PANELS.items():
            panel = panel_cls(self)
            self.panels[tab_id] = panel
            self.stack.addWidget(panel)
        body.addWidget(self.stack, 1)

        root.addLayout(body, 1)

        self._switch_tab("dashboard")

    def _restore_window_state(self) -> None:
        geo = self._settings.value("window/geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        state = self._settings.value("window/state")
        if state is not None:
            self.restoreState(state)

    def apply_font_size(self) -> None:
        try:
            size = int(self.config.get("font_size", "11"))
        except (ValueError, TypeError):
            size = 11
        size = max(8, min(32, size))
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(size)
            app.setFont(font)

    def closeEvent(self, event) -> None:
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())
        super().closeEvent(event)

    def _start_status_checker(self) -> None:
        checker = ServerStatusChecker(self)
        checker.status_changed.connect(self._on_server_status)
        checker.start(interval_ms=180_000)

    def _on_server_status(self, status: str) -> None:
        self._server_status = status
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        color = _TAB_COLORS.get(self._current_tab, CYAN)
        s = self._server_status
        self.status_bar.set_status(f"{s}")
        self.status_bar.set_status_color(_STATUS_COLOR.get(s, GRAY))
        self.status_bar.set_accent_color(color)

    def _switch_tab(self, tab_id: str) -> None:
        self._current_tab = tab_id

        for btn in self.tab_buttons:
            btn.setChecked(False)
        if tab_id in self._tab_map:
            self._tab_map[tab_id].setChecked(True)

        self.stack.setCurrentWidget(self.panels[tab_id])
        self._update_status_bar()
        self.panels[tab_id].refresh()
