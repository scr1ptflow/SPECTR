from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from spectr.config import load_config
from spectr.journal import JournalReader
from spectr.ui.panels import DashboardPanel, SettingsPanel
from spectr.ui.panels import CommanderPanel, ShipPanel, LocationPanel
from spectr.ui.panels import MissionsPanel, LaboratoryPanel
from spectr.ui.sidebar import Sidebar

TAB_PANELS = {
    "dashboard": DashboardPanel,
    "commander": CommanderPanel,
    "ship": ShipPanel,
    "location": LocationPanel,
    "missions": MissionsPanel,
    "laboratory": LaboratoryPanel,
    "settings": SettingsPanel,
}


class SpectrApp(App):
    TITLE = "SPECTR - Elite Dangerous Companion"
    SUB_TITLE = "Terminal UI for commanders"

    CSS = """
    Screen {
        layout: horizontal;
    }

    Sidebar {
        width: 20;
        min-width: 20;
        max-width: 20;
        background: $surface;
        height: 100%;
        border-right: solid $primary;
    }

    #sidebar-title {
        padding: 1 1;
        text-align: center;
        text-style: bold;
        background: $primary 30%;
        color: $text;
        height: 3;
    }

    #tab-list {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
    }

    #tab-list > .tab-button {
        width: 100%;
        height: 3;
        text-align: left;
        padding: 0 1;
        border: none;
        background: transparent;
        color: $text;
        margin: 0;
    }

    #tab-list > .tab-button:hover {
        background: $accent 20%;
    }

    #tab-list > .tab-button.active {
        background: $primary 30%;
        color: $primary;
        border-left: solid $primary;
    }

    #content {
        width: 1fr;
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
    }

    #content > .panel {
        width: 100%;
        height: 100%;
    }

    #content > .panel.hidden {
        display: none;
    }

    .panel-title {
        text-style: bold;
        padding: 0 0 1 0;
        border-bottom: solid $primary;
        margin-bottom: 1;
        height: 3;
    }

    #settings-form {
        padding: 0 1;
    }

    #settings-form > Label {
        margin-top: 1;
    }

    #settings-form > Input {
        margin-top: 0;
    }

    #settings-form > Button {
        margin-top: 1;
        width: 20;
    }

    #lab-summary {
        height: 5;
        margin-bottom: 1;
    }

    #lab-summary > .lab-stat {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        text-align: center;
        padding: 1;
        content-align: center middle;
    }

    #lab-summary > .lab-stat:first-child {
        margin-right: 1;
    }

    #ship-name {
        text-align: center;
        padding: 0 0 1 0;
        height: 3;
    }

    #ship-stats {
        height: 5;
        margin-bottom: 1;
    }

    #ship-stats > .ship-stat {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        text-align: center;
        padding: 1;
        content-align: center middle;
    }

    #ship-stats > .ship-stat:first-child {
        margin-right: 1;
    }

    #ship-stats > .ship-stat:last-child {
        margin-left: 1;
    }

    #dashboard-grid {
        grid-size: 2 4;
        grid-columns: 1fr 1fr 1fr 1fr;
        grid-rows: 1fr 1fr;
        height: 1fr;
        width: 100%;
        grid-gutter: 1;
    }

    .dashboard-cell {
        border: solid $primary 30%;
        padding: 0 1;
        overflow-y: auto;
    }

    #cmdr-name {
        text-align: center;
        text-style: bold;
        height: 3;
        padding: 0 0 1 0;
    }

    #cmdr-layout {
        height: 1fr;
    }

    #cmdr-left {
        width: 1fr;
        height: auto;
    }

    #cmdr-right {
        width: 1fr;
        height: auto;
        border-left: solid $primary 30%;
        padding-left: 1;
    }

    #ranks-columns {
        height: auto;
    }

    #ranks-left, #ranks-right {
        width: 1fr;
    }

    .rank-entry {
        height: 4;
    }

    #cmdr-finances {
        height: auto;
        margin-top: 1;
    }

    .finance-row {
        height: 3;
    }

    .finance-label {
        width: auto;
        text-style: bold;
    }

    .finance-value {
        width: 1fr;
        text-align: right;
    }

    .section-title {
        text-style: bold;
        padding: 0 0 1 0;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }

    .section-spacer {
        height: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.journal = JournalReader(self.config.get("journal_path", ""))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Sidebar()
        with Container(id="content"):
            for tab_id, panel_cls in TAB_PANELS.items():
                yield panel_cls(classes="panel hidden")
        yield Footer()

    def on_mount(self) -> None:
        self._panels: dict[str, PanelBase] = {}
        for panel, (tab_id, _) in zip(
            self.query_one("#content").children, TAB_PANELS.items()
        ):
            self._panels[tab_id] = panel
        self._current_panel: str | None = None
        self._show_panel("dashboard")

    def _show_panel(self, tab_id: str) -> None:
        if self._current_panel is not None:
            self._panels[self._current_panel].add_class("hidden")
        self._panels[tab_id].remove_class("hidden")
        self._current_panel = tab_id


def main() -> None:
    app = SpectrApp()
    app.run()


if __name__ == "__main__":
    main()
