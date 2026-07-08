from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Static

from spectr.config import save_config


class PanelBase(Static):
    """Base class for all content panels."""


class DashboardPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Dashboard", id="panel-title", classes="panel-title")
        yield Static(
            "Welcome to SPECTR - Elite Dangerous Companion\n\n"
            "Select a tab from the sidebar to view your game data.\n\n"
            "Configure your journal path in Settings to get started.",
            id="dashboard-welcome",
        )

    def on_mount(self) -> None:
        app = self.app
        journal = app.journal
        config = app.config

        if config.get("journal_path"):
            welcome = self.query_one("#dashboard-welcome")
            cmdr = journal.get_commander()
            system = journal.get_current_system()
            ship = journal.get_ship_type()
            credits = journal.get_credits()

            lines = ["Dashboard", "", "Connected to journals."]
            if cmdr:
                lines.append(f"Commander: {cmdr}")
            if system:
                lines.append(f"System: {system}")
            if ship:
                lines.append(f"Ship: {ship}")
            if credits is not None:
                lines.append(f"Credits: {credits:,}")
            welcome.update("\n".join(lines))


class CommanderPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Commander", classes="panel-title")
        yield RichLog(id="commander-log", highlight=True)

    def on_mount(self) -> None:
        log = self.query_one("#commander-log", RichLog)
        app = self.app
        config = app.config
        journal = app.journal

        cmdr = journal.get_commander() or config.get("commander_name") or "Unknown"
        log.write(f"Commander Name: {cmdr}")

        if journal.journal_path and journal.journal_path.exists():
            events = journal.get_all_events("Commander")
            if events:
                log.write("")
                log.write("Recent Commander Events:")
                for e in events[-5:]:
                    log.write(f"  {e.timestamp}: {e.event}")


class ShipPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Ship", classes="panel-title")
        yield RichLog(id="ship-log", highlight=True)

    def on_mount(self) -> None:
        log = self.query_one("#ship-log", RichLog)
        journal = self.app.journal

        ship_type = journal.get_ship_type() or "Unknown"
        ship_name = journal.get_ship_name()
        log.write(f"Ship Type: {ship_type}")
        if ship_name:
            log.write(f"Ship Name: {ship_name}")

        loadout = journal.get_latest_event("Loadout")
        if loadout:
            log.write("")
            log.write("Modules:")
            for module in loadout.get("Modules", []):
                slot = module.get("Slot", "?")
                item = module.get("Item", "?")
                log.write(f"  {slot}: {item}")


class LocationPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Location", classes="panel-title")
        yield RichLog(id="location-log", highlight=True)

    def on_mount(self) -> None:
        log = self.query_one("#location-log", RichLog)
        journal = self.app.journal

        system = journal.get_current_system() or "Unknown"
        log.write(f"Current System: {system}")

        location = journal.get_latest_event("Location")
        if location:
            log.write(f"Body: {location.get('Body', 'N/A')}")
            log.write(f"Station: {location.get('StationName', 'N/A')}")


class MissionsPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Missions", classes="panel-title")
        yield RichLog(id="missions-log", highlight=True)

    def on_mount(self) -> None:
        log = self.query_one("#missions-log", RichLog)
        journal = self.app.journal

        missions = journal.get_all_events("MissionAccepted")
        if missions:
            for m in missions[-10:]:
                log.write(
                    f"{m.timestamp}: {m.get('Name')} - "
                    f"{m.get('DestinationSystem', '?')}"
                )
        else:
            log.write("No active missions found in journal.")


class LaboratoryPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Laboratory", classes="panel-title")
        with Horizontal(id="lab-summary"):
            yield Static(id="lab-count", classes="lab-stat")
            yield Static(id="lab-value", classes="lab-stat")
        yield RichLog(id="lab-detail", highlight=True)

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        journal = self.app.journal
        summary = journal.get_organic_summary()

        count_w = self.query_one("#lab-count", Static)
        count_w.update(
            f"[bold]Sellable Samples[/bold]\n[bold white]{summary['total_sellable']}[/bold white]"
        )

        value_w = self.query_one("#lab-value", Static)
        value_w.update(
            f"[bold]Predicted Value[/bold]\n[bold yellow]{summary['total_value']:,}[/bold yellow] CR"
        )

        detail = self.query_one("#lab-detail", RichLog)
        detail.clear()
        if summary["pending"]:
            detail.write(f"{'System':<16} {'Body':<14} {'Species':<22} {'Sets':>5} {'Value':>12}")
            detail.write("-" * 72)
            for p in summary["pending"]:
                sys_name = p["system"][:16] if p["system"] else "?"
                body_name = p["body"][:14] if p["body"] else "?"
                species_name = p["species"][:22]
                val_str = f"{p['predicted_value']:,}"
                detail.write(
                    f"{sys_name:<16} {body_name:<14} {species_name:<22} "
                    f"{p['sellable']:>5} {val_str:>12}"
                )
        else:
            detail.write("No pending organic data. Use your Genetic Sampler to collect samples.")


class SettingsPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Settings", classes="panel-title")
        with Vertical(id="settings-form"):
            yield Label("Journal Path (e.g. ~/Saved Games/Frontier Developments/Elite Dangerous)")
            yield Input(
                placeholder="~/Saved Games/Frontier Developments/Elite Dangerous",
                id="input-journal-path",
            )
            yield Label("Commander Name")
            yield Input(placeholder="Commander Name", id="input-commander-name")
            yield Label("Inara API Key")
            yield Input(placeholder="Inara API Key", id="input-inara-key")
            yield Label("Inara App Name")
            yield Input(placeholder="SPECTR", id="input-inara-app")
            yield Label("EDSM API Key")
            yield Input(placeholder="EDSM API Key", id="input-edsm-key")
            yield Label("EDSM App Name")
            yield Input(placeholder="SPECTR", id="input-edsm-app")
            yield Button("Save Settings", id="save-settings", variant="primary")
            yield Static("", id="settings-status")

    def on_mount(self) -> None:
        config = self.app.config
        self.query_one("#input-journal-path", Input).value = config.get("journal_path", "")
        self.query_one("#input-commander-name", Input).value = config.get("commander_name", "")
        self.query_one("#input-inara-key", Input).value = config.get("inara_api_key", "")
        self.query_one("#input-inara-app", Input).value = config.get("inara_app_name", "SPECTR")
        self.query_one("#input-edsm-key", Input).value = config.get("edsm_api_key", "")
        self.query_one("#input-edsm-app", Input).value = config.get("edsm_app_name", "SPECTR")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-settings":
            new_config = {
                "journal_path": self.query_one("#input-journal-path", Input).value.strip(),
                "commander_name": self.query_one("#input-commander-name", Input).value.strip(),
                "inara_api_key": self.query_one("#input-inara-key", Input).value.strip(),
                "inara_app_name": self.query_one("#input-inara-app", Input).value.strip() or "SPECTR",
                "edsm_api_key": self.query_one("#input-edsm-key", Input).value.strip(),
                "edsm_app_name": self.query_one("#input-edsm-app", Input).value.strip() or "SPECTR",
            }
            save_config(new_config)
            self.app.config = new_config
            self.app.journal.set_path(new_config["journal_path"])
            status = self.query_one("#settings-status", Static)
            status.update("Settings saved successfully.")

