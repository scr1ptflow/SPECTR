from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static
from textual.widget import Widget


TAB_ITEMS = [
    ("dashboard", "Dashboard"),
    ("commander", "Commander"),
    ("ship", "Ship"),
    ("location", "Location"),
    ("missions", "Missions"),
    ("laboratory", "Laboratory"),
    ("settings", "Settings"),
]


class Sidebar(Widget):
    def compose(self) -> ComposeResult:
        yield Static("SPECTR", id="sidebar-title", classes="sidebar-title")
        with Vertical(id="tab-list"):
            for tab_id, label in TAB_ITEMS:
                yield Button(
                    label,
                    id=f"tab-{tab_id}",
                    classes="tab-button",
                )

    def on_mount(self) -> None:
        self._activate_tab("dashboard")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        tab_id = event.button.id.replace("tab-", "")
        self._activate_tab(tab_id)
        self.app._show_panel(tab_id)

    def _activate_tab(self, tab_id: str) -> None:
        for button in self.query(Button):
            button.remove_class("active")
        active = self.query_one(f"#tab-{tab_id}")
        if active:
            active.add_class("active")
