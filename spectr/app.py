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
        self._show_panel("dashboard")


    def _show_panel(self, tab_id: str) -> None:
        for panel in self.query_one("#content").children:
            panel.add_class("hidden")
        for panel in self.query_one("#content").children:
            for tid, pcls in TAB_PANELS.items():
                if tid == tab_id and isinstance(panel, pcls):
                    panel.remove_class("hidden")
                    return


def main() -> None:
    app = SpectrApp()
    app.run()


if __name__ == "__main__":
    main()
