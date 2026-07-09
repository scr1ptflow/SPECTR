from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Static

from spectr.config import save_config
from spectr.inara import InaraClient


class PanelBase(Static):
    """Base class for all content panels."""


class DashboardPanel(PanelBase):
    def compose(self) -> ComposeResult:
        with Grid(id="dashboard-grid"):
            yield Static(id="cell-commander", classes="dashboard-cell")
            yield Static(id="cell-ship", classes="dashboard-cell")
            yield Static(id="cell-location", classes="dashboard-cell")
            yield Static(id="cell-modules", classes="dashboard-cell")
            yield Static(id="cell-missions", classes="dashboard-cell")
            yield Static(id="cell-organic", classes="dashboard-cell")
            yield Static(id="cell-environment", classes="dashboard-cell")
            yield Static(id="cell-cargo", classes="dashboard-cell")

    def on_mount(self) -> None:
        app = self.app
        journal = app.journal
        config = app.config
        raw = config.get("journal_path", "")
        if not raw:
            return
        journal_path = Path(raw).expanduser()

        loadout = journal.get_latest_event("Loadout")
        hull_health = loadout.get("HullHealth", 1.0) if loadout else 1.0
        fuel_capacity = loadout.get("FuelCapacity", {}).get("Main", 128) if loadout else 128

        shield_health = 1.0
        shield_installed = False
        if loadout:
            for m in loadout.get("Modules", []):
                if m.get("Slot") == "ShieldGenerator":
                    shield_installed = True
                    shield_health = m.get("Health", 1.0)

        fuel_current = fuel_capacity
        shields_up = False
        docked = False
        landed = False
        supercruise = False
        status_path = journal_path / "Status.json"
        if status_path.exists():
            try:
                with open(status_path) as f:
                    status = json.loads(f.read())
                fuel_current = status.get("Fuel", {}).get("FuelMain", fuel_capacity)
                flags = status.get("Flags", 0)
                shields_up = bool(flags & (1 << 3))
                docked = bool(flags & 1)
                landed = bool(flags & (1 << 1))
                supercruise = bool(flags & (1 << 4))
            except (json.JSONDecodeError, OSError):
                pass

        # Commander
        cmdr = journal.get_commander() or config.get("commander_name") or "Unknown"
        credits = journal.get_credits()
        cmdr_lines = ["[bold]Commander[/bold]"]
        cmdr_lines.append(cmdr)
        if credits is not None:
            cmdr_lines.append(f"Credits: [yellow]{credits:,}[/yellow]")
        self.query_one("#cell-commander", Static).update("\n".join(cmdr_lines))

        # Ship
        ship_type = journal.get_ship_type() or "Unknown"
        ship_name = journal.get_ship_name()
        ship_ident = journal.get_ship_ident()

        ship_lines = ["[bold]Ship[/bold]"]
        name_parts = []
        if ship_name:
            name_parts.append(ship_name)
        if ship_ident:
            name_parts.append(f"({ship_ident})")
        if name_parts:
            ship_lines.append(" ".join(name_parts))
        ship_lines.append(f"[italic]{ship_type}[/italic]")
        hull_color = _health_color(hull_health)
        ship_lines.append(f"Hull: [{hull_color}]{_health_bar(hull_health)}[/{hull_color}]")
        if shield_installed:
            shield_label = "UP" if shields_up else "DOWN"
            shield_color = _health_color(shield_health)
            ship_lines.append(f"Shield: [{shield_color}]{_health_bar(shield_health)}[/{shield_color}] ({shield_label})")
        fuel_pct = fuel_current / fuel_capacity if fuel_capacity > 0 else 0
        fuel_color = _health_color(fuel_pct)
        ship_lines.append(f"Fuel: [{fuel_color}]{_health_bar(fuel_pct)}[/{fuel_color}]")
        self.query_one("#cell-ship", Static).update("\n".join(ship_lines))

        # Location
        system = journal.get_current_system() or "Unknown"
        location = journal.get_latest_event("Location")
        body = location.get("Body", "") if location else ""
        station = location.get("StationName", "") if location else ""

        loc_lines = ["[bold]Location[/bold]", f"System: {system}"]
        if body:
            loc_lines.append(f"Body: {body}")
        if station:
            loc_lines.append(f"Station: {station}")

        if docked:
            loc_lines.append("[green]Docked[/green]")
        elif landed:
            loc_lines.append("[yellow]Landed[/yellow]")
        elif supercruise:
            loc_lines.append("[blue]Supercruise[/blue]")
        else:
            loc_lines.append("[cyan]In Flight[/cyan]")

        self.query_one("#cell-location", Static).update("\n".join(loc_lines))

        # Modules
        critical = ["PowerPlant", "MainEngines", "FrameShiftDrive", "PowerDistributor"]
        mod_lines = ["[bold]Core Modules[/bold]"]
        if loadout:
            modules_info = []
            for m in loadout.get("Modules", []):
                slot = m.get("Slot", "")
                if slot in critical:
                    item = m.get("Item", "?")
                    h = m.get("Health", 1.0)
                    label = _slot_label(slot, item)
                    color = _health_color(h)
                    modules_info.append((label, h, color))
            if modules_info:
                max_label = max(len(l) for l, _, _ in modules_info)
                for label, h, color in modules_info:
                    padded = label.ljust(max_label)
                    mod_lines.append(f"[{color}]{padded}  {_health_bar(h)}[/{color}]")
        if len(mod_lines) == 1:
            mod_lines.append("No module data")
        self.query_one("#cell-modules", Static).update("\n".join(mod_lines))

        # Missions
        missions = journal.get_all_events("MissionAccepted")
        mis_lines = ["[bold]Missions[/bold]"]
        if missions:
            active = missions[-5:]
            mis_lines.append(f"Active: {len(active)}")
            for m in active:
                name = m.get("Name", "?")
                dest = m.get("DestinationSystem", "?")
                mis_lines.append(f"• {name} → {dest}")
        else:
            mis_lines.append("No active missions")
        self.query_one("#cell-missions", Static).update("\n".join(mis_lines))

        # Organic Lab
        organic = journal.get_organic_summary()
        org_lines = ["[bold]Organic Lab[/bold]"]
        if organic["total_sellable"] > 0:
            org_lines.append(f"Sellable: {organic['total_sellable']} samples")
            org_lines.append(f"Value: [yellow]{organic['total_value']:,}[/yellow] CR")
        else:
            org_lines.append("No samples ready")
        self.query_one("#cell-organic", Static).update("\n".join(org_lines))

        # Environment
        env_lines = ["[bold]Environment[/bold]"]
        if location:
            body_type = location.get("BodyType", "")
            if body_type:
                env_lines.append(f"Body: {body_type}")
            st = location.get("StarType") or location.get("StarClass", "")
            if st:
                env_lines.append(f"Star: {st}")
            eco = location.get("SystemEconomy_Localised") or location.get("SystemEconomy", "")
            if eco:
                env_lines.append(f"Economy: {eco}")
            gov = location.get("SystemGovernment_Localised") or location.get("SystemGovernment", "")
            if gov:
                env_lines.append(f"Gov: {gov}")
        if len(env_lines) == 1:
            env_lines.append("No data")
        self.query_one("#cell-environment", Static).update("\n".join(env_lines))

        # Cargo
        cargo_count = journal.get_cargo_count()
        cargo_lines = ["[bold]Cargo[/bold]"]
        if cargo_count is not None:
            cargo_lines.append(f"Total: {cargo_count} tons")
        else:
            cargo_lines.append("No cargo data")
        self.query_one("#cell-cargo", Static).update("\n".join(cargo_lines))


class CommanderPanel(PanelBase):
    _RANK_IDS = ["Combat", "Trade", "Explore", "CQC", "Empire", "Federation", "Soldier", "Exobiologist"]

    def compose(self) -> ComposeResult:
        with Horizontal(id="cmdr-layout"):
            with Vertical(id="cmdr-left"):
                yield Static(id="cmdr-name")
                with Horizontal(id="ranks-columns"):
                    with Vertical(id="ranks-left"):
                        yield Static(id="rank-combat", classes="rank-entry")
                        yield Static(id="rank-explore", classes="rank-entry")
                        yield Static(id="rank-empire", classes="rank-entry")
                        yield Static(id="rank-soldier", classes="rank-entry")
                    with Vertical(id="ranks-right"):
                        yield Static(id="rank-trade", classes="rank-entry")
                        yield Static(id="rank-cqc", classes="rank-entry")
                        yield Static(id="rank-federation", classes="rank-entry")
                        yield Static(id="rank-exobiologist", classes="rank-entry")
                with Vertical(id="cmdr-finances"):
                    with Horizontal(classes="finance-row"):
                        yield Static("Credits:", classes="finance-label")
                        yield Static(id="finance-credits", classes="finance-value")
                    with Horizontal(classes="finance-row"):
                        yield Static("Mercenary Coins:", classes="finance-label")
                        yield Static(id="finance-arx", classes="finance-value")
                    with Horizontal(classes="finance-row"):
                        yield Static("Rebuy Cost:", classes="finance-label")
                        yield Static(id="finance-rebuy", classes="finance-value")
                    with Horizontal(classes="finance-row"):
                        yield Static("Notoriety:", classes="finance-label")
                        yield Static(id="finance-notoriety", classes="finance-value")
                    yield Static(id="finance-power", classes="powerplay-row")
            with Vertical(id="cmdr-right"):
                yield Static("[bold]Galnet News[/bold]", classes="section-title")
                yield Static("[dim]No news available[/dim]", id="galnet-content")
                yield Static("", classes="section-spacer")
                yield Static("[bold]Community Goals[/bold]", classes="section-title")
                yield Static("[dim]No active goals[/dim]", id="cg-content")

    def on_mount(self) -> None:
        journal = self.app.journal
        config = self.app.config

        cmdr = journal.get_commander() or config.get("commander_name") or "Unknown"
        squadron = journal.get_squadron()
        cmdr_line = f"[bold]{cmdr}[/bold]"
        if squadron:
            cmdr_line += f"  [dim]— {squadron}[/dim]"
        self.query_one("#cmdr-name", Static).update(cmdr_line)

        ranks = journal.get_rank_levels()
        progress = journal.get_rank_progress()
        credits = journal.get_credits()

        api_key = config.get("inara_api_key", "")
        if api_key and cmdr != "Unknown":
            inara = InaraClient(api_key, cmdr, config.get("inara_app_name", "SPECTR"))
            inara_ranks = inara.get_ranks()
            inara_progress = inara.get_rank_progress()
            inara_credits = inara.get_credits()
            if inara_credits is not None:
                credits = inara_credits
            ranks = {**ranks, **inara_ranks}
            progress = {**progress, **inara_progress}

        for rk in self._RANK_IDS:
            cell = self.query_one(f"#rank-{rk.lower()}", Static)
            level = ranks.get(rk, 0)
            pct = progress.get(rk, 0) / 100
            name = journal.get_rank_name(rk, level)
            color = _health_color(pct)
            cell.update(f"[bold]{rk}[/bold]\n{name}\n[{color}]{_health_bar(pct)}[/{color}]")

        if credits is not None:
            self.query_one("#finance-credits", Static).update(f"[green]{credits:,}[/green]")

        arx = 0
        self.query_one("#finance-arx", Static).update(f"[green]{arx:,}[/green]")

        rebuy = journal.get_rebuy()
        if rebuy is not None:
            self.query_one("#finance-rebuy", Static).update(f"[red]{rebuy:,}[/red]")

        notoriety = journal.get_notoriety()
        color = "green" if notoriety == 0 else "yellow" if notoriety < 3 else "red"
        self.query_one("#finance-notoriety", Static).update(f"[{color}]{notoriety}[/{color}]")

        pp = journal.get_powerplay()
        if pp and pp["power"]:
            self.query_one("#finance-power", Static).update(
                f"[bold]{pp['power']}[/bold] Rank {pp['rank']} — {pp['merits']:,} merits"
            )


_SLOT_LABELS: dict[str, str] = {
    # Core Internal
    "PowerPlant": "Power Plant",
    "MainEngines": "Thrusters",
    "FrameShiftDrive": "Frame Shift Drive",
    "LifeSupport": "Life Support",
    "PowerDistributor": "Power Distributor",
    "Sensors": "Sensors",
    "Armour": "Armour",

    # Optional Internal
    "ShieldGenerator": "Shield Generator",
    "CargoHatch": "Cargo Hatch",
    "CargoRack": "Cargo Rack",
    "CorrosionProofCargoRack": "Corrosion Resistant Cargo Rack",
    "FuelTank": "Fuel Tank",
    "Refinery": "Refinery",
    "PlanetaryApproachSuite": "Planetary Approach Suite",
    "DetailedSurfaceScanner": "Detailed Surface Scanner",
    "DiscoveryScanner": "Discovery Scanner",
    "FuelScoop": "Fuel Scoop",
    "AutoFieldMaintenanceUnit": "Auto Field Maintenance Unit",
    "GuardianFSDBooster": "Guardian FSD Booster",
    "DockingComputer": "Docking Computer",
    "AdvancedDockingComputer": "Advanced Docking Computer",
    "SupercruiseAssist": "Supercruise Assist",
    "VehicleHangar": "Planetary Vehicle Hangar",
    "FighterHangar": "Fighter Hangar",
    "PassengerCabin": "Passenger Cabin",

    # Limpet Controllers
    "CollectorLimpetController": "Collector Limpet Controller",
    "ProspectorLimpetController": "Prospector Limpet Controller",
    "RepairLimpetController": "Repair Limpet Controller",
    "FuelTransferLimpetController": "Fuel Transfer Limpet Controller",
    "HatchBreakerLimpetController": "Hatch Breaker Limpet Controller",
    "ReconLimpetController": "Recon Limpet Controller",
    "ResearchLimpetController": "Research Limpet Controller",
    "DecontaminationLimpetController": "Decontamination Limpet Controller",
    "OperationsMultiLimpetController": "Operations Multi Limpet Controller",
    "RescueMultiLimpetController": "Rescue Multi Limpet Controller",
    "UniversalMultiLimpetController": "Universal Multi Limpet Controller",
    "XenoMultiLimpetController": "Xeno Multi Limpet Controller",

    # Reinforcements
    "HullReinforcementPackage": "Hull Reinforcement Package",
    "ModuleReinforcementPackage": "Module Reinforcement Package",
    "GuardianHullReinforcement": "Guardian Hull Reinforcement",
    "GuardianModuleReinforcement": "Guardian Module Reinforcement",
    "GuardianShieldReinforcement": "Guardian Shield Reinforcement",

    # Utility Mounts
    "ShieldBooster": "Shield Booster",
    "HeatSinkLauncher": "Heat Sink Launcher",
    "ChaffLauncher": "Chaff Launcher",
    "PointDefence": "Point Defence",
    "ElectronicCountermeasure": "Electronic Countermeasure",
    "PulseWaveAnalyser": "Pulse Wave Analyser",
    "KillWarrantScanner": "Kill Warrant Scanner",
    "ManifestScanner": "Manifest Scanner",
    "FsdWakeScanner": "Frame Shift Wake Scanner",
    "FrameShiftDriveInterdictor": "Frame Shift Drive Interdictor",
    "DataLinkScanner": "Data Link Scanner",
    "CompositionScanner": "Composition Scanner",
    "XenoScanner": "Xeno Scanner",
    "ShutdownFieldNeutraliser": "Shutdown Field Neutraliser",
}


def _slot_label(slot: str, item: str) -> str:
    if slot.startswith("MediumHardpoint"):
        return f"Hardpoint {slot[-1]}"
    if slot.startswith("SmallHardpoint"):
        return f"Hardpoint {slot[-1]}"
    if slot.startswith("TinyHardpoint"):
        return f"Utility {slot[-1]}"
    if slot.startswith("Slot"):
        comp = item.split("_")[-1] if "_" in item else item
        return comp.replace("class", "").capitalize() if comp else "Internal"
    return _SLOT_LABELS.get(slot, slot)


def _health_bar(health: float, width: int = 10) -> str:
    pct = max(0.0, min(1.0, health))
    filled = round(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {pct*100:.0f}%"


def _health_color(health: float) -> str:
    if health >= 0.65:
        return "green"
    if health >= 0.30:
        return "yellow"
    return "red"


class ShipPanel(PanelBase):
    def compose(self) -> ComposeResult:
        yield Static("Ship", classes="panel-title")
        yield Static(id="ship-name", classes="ship-name")
        with Horizontal(id="ship-stats"):
            yield Static(id="ship-shield", classes="ship-stat")
            yield Static(id="ship-fuel", classes="ship-stat")
            yield Static(id="ship-hull", classes="ship-stat")
        yield RichLog(id="ship-modules", highlight=True)

    def on_mount(self) -> None:
        journal = self.app.journal
        raw = self.app.config.get("journal_path", "")
        journal_path = Path(raw).expanduser() if raw else None

        ship_type = journal.get_ship_type() or "Unknown"
        ship_name = journal.get_ship_name()
        ship_ident = journal.get_ship_ident()

        name_parts = []
        if ship_name:
            name_parts.append(f"[bold]{ship_name}[/bold]")
        if ship_ident:
            name_parts.append(f"[italic]{ship_ident}[/italic]")
        if not name_parts:
            name_parts.append("[bold]Unknown[/bold]")
        name_parts.append(f"[dim]{ship_type}[/dim]")

        self.query_one("#ship-name", Static).update("  ".join(name_parts))

        loadout = journal.get_latest_event("Loadout")
        hull_health = loadout.get("HullHealth", 1.0) if loadout else 1.0
        fuel_capacity = loadout.get("FuelCapacity", {}).get("Main", 128) if loadout else 128

        shield_health = 1.0
        modules: list[dict] = []
        if loadout:
            for m in loadout.get("Modules", []):
                slot = m.get("Slot", "")
                if slot == "ShieldGenerator":
                    shield_health = m.get("Health", 1.0)
                modules.append(m)

        fuel_current = fuel_capacity
        shields_up = False
        status_path = (journal_path / "Status.json") if journal_path else None
        if status_path and status_path.exists():
            try:
                with open(status_path) as f:
                    status = json.loads(f.read())
                fuel_current = status.get("Fuel", {}).get("FuelMain", fuel_capacity)
                flags = status.get("Flags", 0)
                shields_up = bool(flags & (1 << 3))
            except (json.JSONDecodeError, OSError):
                pass

        shield_w = self.query_one("#ship-shield", Static)
        shield_label = "Shield (UP)" if shields_up else "Shield (DOWN)"
        shield_w.update(
            f"[bold]{shield_label}[/bold]\n{_health_bar(shield_health)}"
        )

        fuel_w = self.query_one("#ship-fuel", Static)
        fuel_pct = fuel_current / fuel_capacity if fuel_capacity > 0 else 0
        fuel_w.update(
            f"[bold]Fuel[/bold]\n{_health_bar(fuel_pct)}"
        )

        hull_w = self.query_one("#ship-hull", Static)
        hull_w.update(
            f"[bold]Hull[/bold]\n{_health_bar(hull_health)}"
        )

        module_log = self.query_one("#ship-modules", RichLog)
        module_log.clear()
        cos_slots = {"Decal1", "Decal2", "Decal3", "Nameplate", "ShipKitSpoiler",
                      "ShipKitWings", "ShipKitTail", "ShipKitArms",
                      "WeaponColour", "EngineColour", "ShipNameplate",
                      "VesselVoice"}

        combat_relevant = {"PowerPlant", "MainEngines", "FrameShiftDrive",
                           "LifeSupport", "PowerDistributor", "Sensors",
                           "Armour", "ShieldGenerator", "CargoHatch"}

        filtered = [m for m in modules if m.get("Slot") not in cos_slots]
        filtered.sort(key=lambda m: (
            0 if m.get("Slot") in combat_relevant else 1,
            m.get("Slot", "")
        ))

        rows = []
        for m in filtered:
            slot = m.get("Slot", "?")
            item = m.get("Item", "?")
            health = m.get("Health", 1.0)
            label = _slot_label(slot, item)
            health_str = _health_bar(health)
            color = _health_color(health)
            rows.append((label, health, health_str, color))

        col_count = max(1, (len(rows) + 1) // 2)
        left = rows[:col_count]
        right = rows[col_count:]

        max_len = max(len(r[0]) for r in rows) + 2 if rows else 20

        for i in range(max(len(left), len(right))):
            line = ""
            if i < len(left):
                lb, _, hs, _ = left[i]
                line += f"{lb:<{max_len}}{hs}"
            if i < len(right):
                if line:
                    line += "   "
                rb, _, hs, _ = right[i]
                line += f"{rb:<{max_len}}{hs}"
            module_log.write(line)


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

