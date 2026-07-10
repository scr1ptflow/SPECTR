# FUI-styled content panels — one QWidget subclass per tab.

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget, QScrollArea,
)

from spectr.config import save_config, validate_config
from spectr.galnet import GalnetFetcher
from spectr.inara import InaraClient
from spectr.ui.widgets import (
    CYAN, ORANGE, BLUE, PURPLE, TEAL, YELLOW, RED, PINK, GRAY, GRAY_L, WHITE, DARK, DARK2, DARK3,
    LcarsBar, LcarsBlock, LcarsPill, HealthBar, lcars_color,
)

GREEN = "#00cc66"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background worker for network fetches (keeps UI responsive)
# ---------------------------------------------------------------------------

class _GalnetWorker(QThread):
    """Fetch Galnet articles in a background thread."""
    done = Signal(list)

    def run(self):
        try:
            articles = GalnetFetcher().get_articles("/galnet")
            self.done.emit(articles)
        except Exception as exc:
            log.warning("Galnet fetch failed: %s", exc)
            self.done.emit([])


class _CommunityGoalsWorker(QThread):
    """Fetch community goals from Galnet in a background thread."""
    done = Signal(list)

    def run(self):
        try:
            fetcher = GalnetFetcher()
            articles = fetcher.get_articles("/galnet")
            # Filter for CG-related articles
            cg_keywords = {"community goal", "community goals", "galactic initiative"}
            cgs = [a for a in articles if any(kw in a.title.lower() for kw in cg_keywords)]
            self.done.emit(cgs)
        except Exception as exc:
            log.warning("Community goals fetch failed: %s", exc)
            self.done.emit([])


# ---------------------------------------------------------------------------
# Base panel with LCARS scroll-wrapper and title
# ---------------------------------------------------------------------------

class PanelBase(QWidget):
    """FUI-styled base panel."""

    def __init__(self, window, title: str, color: str):
        super().__init__()
        self.window = window
        self._color = color

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header with title + underline accent
        header = QWidget()
        header.setStyleSheet(f"background:{DARK};")
        hdr = QVBoxLayout(header)
        hdr.setContentsMargins(20, 12, 20, 6)
        hdr.setSpacing(4)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(
            f"color:{color};font-size:16px;font-weight:bold;"
            f"background:transparent;letter-spacing:2px;"
        )
        hdr.addWidget(self.title_label)

        accent = QWidget()
        accent.setFixedHeight(2)
        accent.setFixedWidth(32)
        accent.setStyleSheet(f"background:{color};border:none;")
        hdr.addWidget(accent)

        outer.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:transparent;width:6px;border:none;}"
            "QScrollBar::handle:vertical{background:#222244;min-height:30px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        )
        outer.addWidget(scroll, 1)

        container = QWidget()
        container.setStyleSheet(f"background:{DARK};")
        self._content = QVBoxLayout(container)
        self._content.setContentsMargins(20, 16, 20, 16)
        self._content.setSpacing(12)
        scroll.setWidget(container)

    def content_layout(self) -> QVBoxLayout:
        return self._content

    def refresh(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Dashboard — Galnet news feed in LCARS data blocks
# ---------------------------------------------------------------------------

class DashboardPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Galnet News", ORANGE)
        self._articles: list = []
        self._active_btn: QPushButton | None = None
        self._worker: _GalnetWorker | None = None
        self._cg_worker: _CommunityGoalsWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        # Article viewer block
        block = LcarsBlock("Galnet Feed", ORANGE)
        self.article_view = QTextBrowser()
        self.article_view.setOpenExternalLinks(True)
        self.article_view.setStyleSheet(
            f"background:{DARK2};border:1px solid #222;border-radius:4px;"
            f"padding:8px;color:{WHITE};"
        )
        block.content_layout().addWidget(self.article_view)
        c.addWidget(block, 1)

        # Date filter buttons row
        date_row = QHBoxLayout()
        date_row.setSpacing(6)
        self.date_btns: list[QPushButton] = []
        self.date_row_layout = date_row
        c.addLayout(date_row)

        # Community Goals block
        cg_block = LcarsBlock("Community Goals", YELLOW)
        self.cg_content = QLabel("Loading...")
        self.cg_content.setStyleSheet(f"color:{GRAY};padding:4px;background:transparent;")
        self.cg_content.setAlignment(Qt.AlignTop)
        self.cg_content.setWordWrap(True)
        cg_block.content_layout().addWidget(self.cg_content)
        c.addWidget(cg_block)

    def refresh(self) -> None:
        self.article_view.setPlainText("Loading galnet feed...")
        self.cg_content.setText("Loading community goals...")

        self._worker = _GalnetWorker(self)
        self._worker.done.connect(self._on_articles_loaded)
        self._worker.start()

        self._cg_worker = _CommunityGoalsWorker(self)
        self._cg_worker.done.connect(self._on_cgs_loaded)
        self._cg_worker.start()

    def _on_articles_loaded(self, articles: list) -> None:
        self._articles = articles

        # Remove old date buttons
        for btn in self.date_btns:
            btn.deleteLater()
        self.date_btns.clear()

        # Extract up to 5 most recent unique dates from articles
        seen = set()
        unique_dates: list[str] = []
        for a in self._articles:
            if a.date not in seen:
                seen.add(a.date)
                unique_dates.append(a.date)

        for i, d in enumerate(unique_dates[:5]):
            day = d.split(" ")[0]
            btn = QPushButton(day)
            btn.setProperty("date", d)
            btn.setFixedSize(40, 28)
            btn.clicked.connect(self._on_date_click)
            self.date_row_layout.addWidget(btn)
            self.date_btns.append(btn)

        if self.date_btns:
            self._select_date(0)
        else:
            self.article_view.setPlainText("No news available")

    def _on_cgs_loaded(self, cgs: list) -> None:
        if not cgs:
            self.cg_content.setText("No active goals")
            return
        lines = []
        for cg in cgs[:5]:
            lines.append(
                f"<span style='color:{YELLOW};font-weight:bold'>{cg.title}</span><br>"
                f"<span style='color:{GRAY}'>{cg.date}</span>"
            )
        self.cg_content.setText("<br><br>".join(lines))

    def _select_date(self, index: int) -> None:
        self._active_btn = None
        for i, btn in enumerate(self.date_btns):
            active = i == index
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )
            if active:
                self._active_btn = btn

        d = self.date_btns[index].property("date") if self.date_btns else None
        self._show_articles(d)

    def _on_date_click(self):
        btn = self.sender()
        if btn and btn in self.date_btns:
            self._select_date(self.date_btns.index(btn))

    def _show_articles(self, filter_date: str | None = None) -> None:
        articles = self._articles
        if filter_date:
            articles = [a for a in articles if a.date == filter_date]

        if not articles:
            self.article_view.setPlainText("No news available")
            return

        lines = []
        for a in articles:
            lines.append(
                f"<span style='color:{ORANGE};font-weight:bold'>{a.title}</span>"
                f"  <span style='color:{GRAY}'>{a.date}</span><br>"
                f"{a.body.replace(chr(10), '<br>')}<br><hr>"
            )
        self.article_view.setHtml("<br>".join(lines))


# ---------------------------------------------------------------------------
# Commander — ranks, progress, powerplay, finances
# ---------------------------------------------------------------------------

class CommanderPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Commander", BLUE)
        self._rank_names: dict[str, QLabel] = {}
        self._rank_bars: dict[str, HealthBar] = {}
        self._finance_labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        # === Commander Identity ===
        id_block = LcarsBlock("", BLUE)
        self.cmdr_label = QLabel()
        self.cmdr_label.setStyleSheet(f"color:{WHITE};font-size:16px;font-weight:bold;background:transparent;")
        id_block.content_layout().addWidget(self.cmdr_label)
        c.addWidget(id_block)

        # === 4x2 Rank Grid ===
        c.addWidget(LcarsBar(BLUE, 2))

        categories = [
            "Combat", "Trade", "Explore", "CQC",
            "Empire", "Federation", "Soldier", "Exobiologist",
        ]
        grid = QGridLayout()
        grid.setSpacing(10)
        c.addLayout(grid)

        for i, cat in enumerate(categories):
            row, col = divmod(i, 2)
            block = LcarsBlock(cat.upper(), lcars_color(i))
            block.content_layout().setSpacing(2)

            rank_name = QLabel("---")
            rank_name.setStyleSheet(f"color:{WHITE};font-size:13px;background:transparent;")
            block.content_layout().addWidget(rank_name)
            self._rank_names[cat] = rank_name

            bar = HealthBar()
            bar.setFixedHeight(14)
            block.content_layout().addWidget(bar)
            self._rank_bars[cat] = bar

            grid.addWidget(block, row, col)

        # === Powerplay ===
        c.addWidget(LcarsBar(BLUE, 2))
        self.pp_block = LcarsBlock("Powerplay", PINK)
        self.pp_inner = QVBoxLayout()
        self.pp_inner.setSpacing(2)
        self.pp_block.content_layout().addLayout(self.pp_inner)
        c.addWidget(self.pp_block)

        # === Finances ===
        c.addWidget(LcarsBar(BLUE, 2))
        fin_block = LcarsBlock("Finances", TEAL)
        fin_inner = QVBoxLayout()
        fin_inner.setSpacing(4)
        fin_block.content_layout().addLayout(fin_inner)

        _FINANCE_COLORS = {
            "credits":  YELLOW,
            "arx":      "#ff6600",
            "rebuy":    RED,
            "notoriety": WHITE,
        }
        for label, key in [
            ("Credits:",          "credits"),
            ("Mercenary Coins:",  "arx"),
            ("Rebuy Cost:",       "rebuy"),
            ("Notoriety:",        "notoriety"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(8)
            row.setAlignment(Qt.AlignHCenter)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{TEAL};font-weight:bold;background:transparent;")
            row.addWidget(lbl)
            val = QLabel()
            val.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            val.setStyleSheet(f"color:{_FINANCE_COLORS[key]};font-weight:bold;background:transparent;")
            row.addWidget(val)
            fin_inner.addLayout(row)
            self._finance_labels[key] = val
        c.addWidget(fin_block)

    def refresh(self) -> None:
        journal = self.window.journal
        config = self.window.config

        cmdr = journal.get_commander() or config.get("commander_name") or "Unknown"
        squadron = journal.get_squadron()
        text = f"<span style='color:{BLUE}'>{cmdr}</span>"
        if squadron:
            text += f"  <span style='color:{GRAY}'>— {squadron}</span>"
        self.cmdr_label.setText(text)

        ranks = journal.get_rank_levels()
        progress = journal.get_rank_progress()

        # Try Inara as fallback for missing rank data
        if not ranks:
            inara = self._get_inara_client(config)
            if inara:
                inara_ranks = inara.get_ranks()
                inara_progress = inara.get_rank_progress()
                if inara_ranks:
                    log.info("Using Inara rank data as fallback")
                    ranks = inara_ranks
                    progress = inara_progress

        for cat in self._rank_names:
            level = ranks.get(cat, 0)
            pct = progress.get(cat, 0) / 100
            self._rank_names[cat].setText(journal.get_rank_name(cat, level))
            self._rank_bars[cat].set_value(pct)

        pp = journal.get_powerplay()
        self._clear_layout(self.pp_inner)
        if pp:
            lbl = QLabel(f"<b>{pp['power'] or 'Powerplay'}</b>")
            lbl.setStyleSheet(f"color:{WHITE};background:transparent;")
            self.pp_inner.addWidget(lbl)
            self.pp_inner.addWidget(QLabel(f"Rank {pp['rank']}  |  {pp['merits']:,} merits"))

        credits = journal.get_credits()
        if credits is not None:
            self._finance_labels["credits"].setText(f"{credits:,}")
        self._finance_labels["arx"].setText("0")

        rebuy = journal.get_rebuy()
        if rebuy is not None:
            self._finance_labels["rebuy"].setText(f"{rebuy:,}")

        notoriety = journal.get_notoriety()
        colour = "green" if notoriety == 0 else "yellow" if notoriety < 3 else "red"
        self._finance_labels["notoriety"].setText(
            f"<span style='color:{colour}'>{notoriety}</span>"
        )

    def _get_inara_client(self, config: dict) -> InaraClient | None:
        api_key = config.get("inara_api_key", "")
        cmdr = config.get("commander_name", "")
        if not api_key or not cmdr:
            return None
        return InaraClient(
            api_key=api_key,
            cmdr_name=cmdr,
            app_name=config.get("inara_app_name", "SPECTR"),
        )

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_layout(sub)


# ---------------------------------------------------------------------------
# Ship — type/name, shield/fuel/hull bars, module table
# ---------------------------------------------------------------------------

class ShipPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Ship", PURPLE)
        self._module_cells: list[QWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        # === Ship Identity ===
        id_block = LcarsBlock("", PURPLE)
        self.ship_name_label = QLabel()
        self.ship_name_label.setAlignment(Qt.AlignCenter)
        self.ship_name_label.setStyleSheet(f"color:{WHITE};font-size:16px;font-weight:bold;background:transparent;")
        id_block.content_layout().addWidget(self.ship_name_label)
        c.addWidget(id_block)

        # === Three stat boxes (Shield | Fuel | Hull) ===
        c.addWidget(LcarsBar(PURPLE, 2))
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.shield_stat = self._make_stat_box("Shield Generator", PURPLE)
        stats_row.addWidget(self.shield_stat)

        # Fuel — custom box with integrity bar + fuel level bar
        self.fuel_stat = LcarsBlock("Fuel Tank", PURPLE)
        fuel_integrity_bar = HealthBar()
        fuel_integrity_bar.setObjectName("stat-bar-fuel")
        fuel_integrity_bar.setFixedHeight(18)
        self.fuel_stat.content_layout().addWidget(fuel_integrity_bar)
        # Fuel level text
        self._fuel_numbers = QLabel("0.0t / 0.0t")
        self._fuel_numbers.setAlignment(Qt.AlignCenter)
        self._fuel_numbers.setStyleSheet(f"color:{WHITE};font-size:12px;font-weight:bold;background:transparent;")
        self.fuel_stat.content_layout().addWidget(self._fuel_numbers)
        stats_row.addWidget(self.fuel_stat)

        self.hull_stat = self._make_stat_box("Hull Integrity", PURPLE)
        stats_row.addWidget(self.hull_stat)

        c.addLayout(stats_row)

        # === Module Grid (2 columns) ===
        c.addWidget(LcarsBar(PURPLE, 4))
        self._module_block = LcarsBlock("", PURPLE)
        self._module_grid = QGridLayout()
        self._module_grid.setSpacing(6)
        self._module_block.content_layout().addLayout(self._module_grid)
        c.addWidget(self._module_block, 1)

    def _make_stat_box(self, label: str, color: str) -> LcarsBlock:
        block = LcarsBlock(label, color)
        bar = HealthBar()
        bar.setObjectName(f"stat-bar-{label.lower().split()[0]}")
        bar.setFixedHeight(18)
        block.content_layout().addWidget(bar)
        return block

    def refresh(self) -> None:
        journal = self.window.journal
        raw = self.window.config.get("journal_path", "")
        journal_path = Path(raw).expanduser() if raw else None

        ship_type = journal.get_ship_type() or "Unknown"
        ship_name = journal.get_ship_name()
        ship_ident = journal.get_ship_ident()

        parts = []
        if ship_name:
            parts.append(f"<span style='color:{PURPLE}'><b>{ship_name}</b></span>")
        if ship_ident:
            parts.append(f"<span style='color:{GRAY_L}'><i>{ship_ident}</i></span>")
        if not parts:
            parts.append("<b>Unknown</b>")
        parts.append(f"<span style='color:{GRAY}'>{ship_type}</span>")
        self.ship_name_label.setText("  ".join(parts))

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
        # Cross-platform Status.json path
        status_path = self._find_status_file(journal_path)
        if status_path and status_path.exists():
            try:
                with open(status_path) as f:
                    status = json.loads(f.read())
                fuel_current = status.get("Fuel", {}).get("FuelMain", fuel_capacity)
                flags = status.get("Flags", 0)
                shields_up = bool(flags & (1 << 3))
            except Exception:
                pass

        if not shields_up:
            shield_health = 0.0

        self.findChild(HealthBar, "stat-bar-shield").set_value(shield_health)
        fuel_pct = fuel_current / fuel_capacity if fuel_capacity > 0 else 0
        self.findChild(HealthBar, "stat-bar-fuel").set_value(
            fuel_pct
        )
        self._fuel_numbers.setText(f"{fuel_current:.1f}t / {fuel_capacity:.1f}t")
        self.findChild(HealthBar, "stat-bar-hull").set_value(hull_health)

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

        # Clear old module cells
        for w in self._module_cells:
            w.deleteLater()
        self._module_cells.clear()

        cols = 2
        for i, m in enumerate(filtered):
            slot = m.get("Slot", "?")
            item = m.get("Item", "?")
            name = m.get("Item_Localised") or _slot_label(slot, item)
            health = m.get("Health", 1.0)

            # Engineering info
            eng = m.get("Engineering")
            eng_text = ""
            if eng:
                grade = eng.get("Grade", 0)
                max_grade = eng.get("MaxGrade", 5)
                eng_name = eng.get("Modifier", "")
                if grade and max_grade:
                    eng_text = f" G{grade}/{max_grade}"
                if eng_name:
                    eng_text += f" {eng_name}"

            cell = QWidget()
            cell.setStyleSheet(f"background:{DARK2};border-radius:4px;border:1px solid #222;")
            row = QHBoxLayout(cell)
            row.setContentsMargins(8, 2, 8, 2)
            row.setSpacing(6)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"color:{WHITE};font-size:11px;background:transparent;")
            name_lbl.setFixedWidth(160)
            row.addWidget(name_lbl)

            if eng_text:
                eng_lbl = QLabel(eng_text)
                eng_lbl.setStyleSheet(f"color:{TEAL};font-size:10px;background:transparent;")
                row.addWidget(eng_lbl)

            bar = HealthBar()
            bar.setFixedHeight(14)
            bar.set_value(health)
            row.addWidget(bar, 1)

            self._module_grid.addWidget(cell, i // cols, i % cols)
            self._module_cells.append(cell)

    @staticmethod
    def _find_status_file(journal_path: Path | None) -> Path | None:
        """Find Status.json, handling both Windows and Linux paths."""
        if not journal_path or not journal_path.exists():
            return None
        status = journal_path / "Status.json"
        if status.exists():
            return status
        return None


# ---------------------------------------------------------------------------
# Location — system, body, station, faction, government, economy
# ---------------------------------------------------------------------------

class LocationPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Location", TEAL)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        block = LcarsBlock("Current Location", TEAL)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            f"color:{WHITE};font-size:14px;padding:8px;"
            f"background:{DARK2};border-radius:4px;border:1px solid #222;"
        )
        block.content_layout().addWidget(self.info_label)
        c.addWidget(block)
        c.addStretch()

    def refresh(self) -> None:
        journal = self.window.journal
        system = journal.get_current_system() or "Unknown"
        lines = [f"<span style='color:{TEAL};font-weight:bold'>System:</span>  {system}"]

        location = journal.get_latest_event("Location")
        if location:
            body = location.get("Body", "N/A")
            station = location.get("StationName", "N/A")
            body_type = location.get("BodyType", "")
            distance = location.get("DistFromStarLs")
            faction = location.get("SystemFaction", "")
            if isinstance(faction, dict):
                faction = faction.get("Name", "")
            government = location.get("SystemGovernment", "")
            economy = location.get("SystemEconomy", "")
            security = location.get("SystemSecurity", "")
            population = location.get("Population", 0)

            lines.append(f"<span style='color:{TEAL};font-weight:bold'>Body:</span>  {body}")
            if body_type:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Body Type:</span>  {body_type}")
            if distance is not None:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Distance from Star:</span>  {distance:.1f} Ls")
            lines.append(f"<span style='color:{TEAL};font-weight:bold'>Station:</span>  {station}")
            if faction:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Faction:</span>  {faction}")
            if government:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Government:</span>  {government}")
            if economy:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Economy:</span>  {economy}")
            if security:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Security:</span>  {security}")
            if population:
                lines.append(f"<span style='color:{TEAL};font-weight:bold'>Population:</span>  {population:,}")

        self.info_label.setText("<br>".join(lines))


# ---------------------------------------------------------------------------
# Missions — active and completed
# ---------------------------------------------------------------------------

class MissionsPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Missions", YELLOW)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        # Active missions
        active_block = LcarsBlock("Active Missions", YELLOW)
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(4)
        self.active_table.setHorizontalHeaderLabels(["Timestamp", "Mission", "Destination", "Expires"])
        self.active_table.horizontalHeader().setStretchLastSection(True)
        self.active_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.active_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.active_table.setSelectionMode(QTableWidget.NoSelection)
        self._style_table(self.active_table, YELLOW)
        active_block.content_layout().addWidget(self.active_table)
        c.addWidget(active_block, 1)

        # Completed/failed missions
        c.addWidget(LcarsBar(YELLOW, 2))
        completed_block = LcarsBlock("Completed / Failed", GRAY)
        self.completed_table = QTableWidget()
        self.completed_table.setColumnCount(4)
        self.completed_table.setHorizontalHeaderLabels(["Timestamp", "Mission", "Outcome", "Reward"])
        self.completed_table.horizontalHeader().setStretchLastSection(True)
        self.completed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.completed_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.completed_table.setSelectionMode(QTableWidget.NoSelection)
        self._style_table(self.completed_table, GRAY)
        completed_block.content_layout().addWidget(self.completed_table)
        c.addWidget(completed_block, 1)

    @staticmethod
    def _style_table(table: QTableWidget, color: str) -> None:
        table.setStyleSheet(
            f"QTableWidget{{background:{DARK2};border:1px solid #222;border-radius:4px;"
            f"color:{WHITE};gridline-color:#222;}}"
            f"QHeaderView::section{{background:{DARK3};color:{color};font-weight:bold;"
            f"border:1px solid #222;padding:4px;}}"
            f"QTableWidget::item{{padding:3px 6px;border-bottom:1px solid #1a1a1a;}}"
        )

    def refresh(self) -> None:
        journal = self.window.journal

        # Active = MissionAccepted without a matching MissionCompleted/Failed/Abandoned
        accepted = journal.get_all_events("MissionAccepted")
        completed_names = set()
        for ev in journal.get_all_events("MissionCompleted"):
            completed_names.add(ev.get("MissionId", ""))
        for ev in journal.get_all_events("MissionFailed"):
            completed_names.add(ev.get("MissionId", ""))
        for ev in journal.get_all_events("MissionAbandoned"):
            completed_names.add(ev.get("MissionId", ""))

        active = [m for m in accepted if m.get("MissionId", "") not in completed_names]
        active = active[-10:]

        self.active_table.setRowCount(len(active))
        for i, m in enumerate(active):
            self.active_table.setItem(i, 0, QTableWidgetItem(m.timestamp))
            self.active_table.setItem(i, 1, QTableWidgetItem(m.get("Name", "")))
            self.active_table.setItem(i, 2, QTableWidgetItem(m.get("DestinationSystem", "?")))
            expires = m.get("Expiry", "")
            self.active_table.setItem(i, 3, QTableWidgetItem(expires[:16] if expires else ""))

        # Completed / failed / abandoned
        outcomes: list[tuple[str, str, str, str]] = []
        for ev in journal.get_all_events("MissionCompleted"):
            outcomes.append((ev.timestamp, ev.get("Name", ""), "Completed",
                             str(ev.get("Reward", 0)) if ev.get("Reward") else ""))
        for ev in journal.get_all_events("MissionFailed"):
            outcomes.append((ev.timestamp, ev.get("Name", ""), "Failed", ""))
        for ev in journal.get_all_events("MissionAbandoned"):
            outcomes.append((ev.timestamp, ev.get("Name", ""), "Abandoned", ""))

        outcomes.sort(key=lambda x: x[0], reverse=True)
        outcomes = outcomes[-10:]

        self.completed_table.setRowCount(len(outcomes))
        for i, (ts, name, outcome, reward) in enumerate(outcomes):
            self.completed_table.setItem(i, 0, QTableWidgetItem(ts))
            self.completed_table.setItem(i, 1, QTableWidgetItem(name))
            item = QTableWidgetItem(outcome)
            colour = GREEN if outcome == "Completed" else RED
            item.setForeground(QColor(colour))
            self.completed_table.setItem(i, 2, item)
            self.completed_table.setItem(i, 3, QTableWidgetItem(reward))


# ---------------------------------------------------------------------------
# Laboratory — exobiology
# ---------------------------------------------------------------------------

class LaboratoryPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Laboratory", RED)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        # Summary stats
        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        c.addLayout(summary_row)

        self.count_stat = self._make_summary_block("Sellable Samples", RED)
        summary_row.addWidget(self.count_stat)
        self.value_stat = self._make_summary_block("Predicted Value", RED)
        summary_row.addWidget(self.value_stat)

        # Detail table
        c.addWidget(LcarsBar(RED, 2))
        block = LcarsBlock("Pending Organic Data", RED)
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels(["System", "Body", "Species", "Sets", "Value", "First Footfall"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.detail_table.setSelectionMode(QTableWidget.NoSelection)
        self.detail_table.setStyleSheet(
            f"QTableWidget{{background:{DARK2};border:1px solid #222;border-radius:4px;"
            f"color:{WHITE};gridline-color:#222;}}"
            f"QHeaderView::section{{background:{DARK3};color:{RED};font-weight:bold;"
            f"border:1px solid #222;padding:4px;}}"
            f"QTableWidget::item{{padding:3px 6px;border-bottom:1px solid #1a1a1a;}}"
        )
        block.content_layout().addWidget(self.detail_table)
        c.addWidget(block, 1)

    def _make_summary_block(self, label: str, color: str) -> LcarsBlock:
        block = LcarsBlock(label, color)
        val = QLabel("0")
        val.setObjectName(f"lab-{label.lower().split()[0]}")
        val.setAlignment(Qt.AlignCenter)
        val.setStyleSheet(f"font-size:28px;font-weight:bold;color:{WHITE};background:transparent;")
        block.content_layout().addWidget(val)
        return block

    def refresh(self) -> None:
        journal = self.window.journal
        summary = journal.get_organic_summary()

        self.findChild(QLabel, "lab-sellable").setText(str(summary["total_sellable"]))
        self.findChild(QLabel, "lab-predicted").setText(f"{summary['total_value']:,} CR")

        pending = summary["pending"]
        self.detail_table.setRowCount(len(pending))
        for i, p in enumerate(pending):
            self.detail_table.setItem(i, 0, QTableWidgetItem(p["system"][:16]))
            self.detail_table.setItem(i, 1, QTableWidgetItem(p["body"][:14]))
            self.detail_table.setItem(i, 2, QTableWidgetItem(p["species"][:22]))
            self.detail_table.setItem(i, 3, QTableWidgetItem(str(p["sellable"])))
            val_item = QTableWidgetItem(f"{p['predicted_value']:,}")
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.detail_table.setItem(i, 4, val_item)
            # First footfall indicator
            self.detail_table.setItem(i, 5, QTableWidgetItem(""))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class SettingsPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Settings", GRAY)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        block = LcarsBlock("Configuration", GRAY)
        form = QVBoxLayout()
        form.setSpacing(4)

        fields = [
            ("journal_path",    "Journal Path",
             "~/Saved Games/Frontier Developments/Elite Dangerous"),
            ("commander_name",  "Commander Name", ""),
            ("inara_api_key",   "Inara API Key", ""),
            ("inara_app_name",  "Inara App Name", "SPECTR"),
            ("edsm_api_key",    "EDSM API Key", ""),
            ("edsm_app_name",   "EDSM App Name", "SPECTR"),
        ]
        self._inputs: dict[str, QLineEdit] = {}
        for key, label, placeholder in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{ORANGE};font-weight:bold;margin-top:6px;background:transparent;")
            form.addWidget(lbl)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setObjectName(f"input-{key}")
            inp.setStyleSheet(
                f"QLineEdit{{padding:6px 8px;border:1px solid #333;border-radius:4px;"
                f"background:{DARK2};color:{WHITE};}}"
                f"QLineEdit:focus{{border-color:{ORANGE};}}"
            )
            form.addWidget(inp)
            self._inputs[key] = inp

        block.content_layout().addLayout(form)

        save_btn = LcarsPill("Save Settings", ORANGE)
        save_btn.clicked.connect(self._on_save)
        block.content_layout().addWidget(save_btn)

        self.status_label = QLabel()
        self.status_label.setObjectName("settings-status")
        self.status_label.setStyleSheet(f"color:#00cc66;padding:4px 0;background:transparent;")
        block.content_layout().addWidget(self.status_label)

        c.addWidget(block)
        c.addStretch()

    def refresh(self) -> None:
        config = self.window.config
        for key, inp in self._inputs.items():
            val = config.get(key, "")
            if inp.placeholderText() == "SPECTR" and not val:
                val = "SPECTR"
            inp.setText(val)

    def _on_save(self):
        new_config = {}
        for key, inp in self._inputs.items():
            new_config[key] = inp.text().strip()

        # Validate before saving
        warnings = validate_config(new_config)
        if warnings:
            self.status_label.setStyleSheet(f"color:#ffcc00;padding:4px 0;background:transparent;")
            self.status_label.setText("Saved with warnings: " + "; ".join(warnings))
        else:
            self.status_label.setStyleSheet(f"color:#00cc66;padding:4px 0;background:transparent;")
            self.status_label.setText("Settings saved successfully.")

        save_config(new_config)
        # Merge with defaults so in-memory config keeps all keys
        from spectr.config import DEFAULT_CONFIG
        self.window.config = {**DEFAULT_CONFIG, **new_config}
        self.window.journal.set_path(new_config.get("journal_path", ""))


# ---------------------------------------------------------------------------
# Ship slot label resolver (unchanged from original)
# ---------------------------------------------------------------------------

_SLOT_LABELS: dict[str, str] = {
    "PowerPlant": "Power Plant",
    "MainEngines": "Thrusters",
    "FrameShiftDrive": "Frame Shift Drive",
    "LifeSupport": "Life Support",
    "PowerDistributor": "Power Distributor",
    "Sensors": "Sensors",
    "Armour": "Armour",
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
    "HullReinforcementPackage": "Hull Reinforcement Package",
    "ModuleReinforcementPackage": "Module Reinforcement Package",
    "GuardianHullReinforcement": "Guardian Hull Reinforcement",
    "GuardianModuleReinforcement": "Guardian Module Reinforcement",
    "GuardianShieldReinforcement": "Guardian Shield Reinforcement",
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


_ITEM_PREFIXES = {"int", "hpt", "pt", "at", "decoration", "paintjob", "shipkit"}

_ITEM_NAMES: dict[str, str] = {
    # Optional Internal — Protection
    "shieldgenerator": "Shield Generator",
    "shieldcellbank": "Shield Cell Bank",
    "hullreinforcementpackage": "Hull Reinforcement Package",
    "modulereinforcementpackage": "Module Reinforcement Package",
    "guardianshieldreinforcement": "Guardian Shield Reinforcement",
    "guardianhullreinforcement": "Guardian Hull Reinforcement",
    "guardianmodulereinforcement": "Guardian Module Reinforcement",
    # Optional Internal — Cargo & Trade
    "cargorack": "Cargo Rack",
    "corrosionproofcargorack": "Corrosion Resistant Cargo Rack",
    "refinery": "Refinery",
    "collectorlimpetcontroller": "Collector Limpet Controller",
    "prospectorlimpetcontroller": "Prospector Limpet Controller",
    "hatchbreakerlimpetcontroller": "Hatch Breaker Limpet Controller",
    # Optional Internal — Mining
    "seismiccharge": "Seismic Charge Launcher",
    "abrasionblaster": "Abrasion Blaster",
    "subsurfacedisplacementmissile": "Sub-surface Displacement Missile",
    "pulsewaveanalyser": "Pulse Wave Analyser",
    # Optional Internal — Exploration
    "fuelscoop": "Fuel Scoop",
    "autofieldmaintenanceunit": "Auto Field-Maintenance Unit",
    "detailedsurfacescanner": "Detailed Surface Scanner",
    "vehiclehangar": "Planetary Vehicle Hangar",
    "planetaryvehiclehangar": "Planetary Vehicle Hangar",
    "fighterhangar": "Fighter Hangar",
    "planetapproachsuite": "Planetary Approach Suite",
    "supercruiseassist": "Supercruise Assist",
    "dockingcomputer": "Docking Computer",
    "advanceddockingcomputer": "Advanced Docking Computer",
    "guardianfsdbooster": "Guardian Frame Shift Drive Booster",
    # Optional Internal — Passenger
    "economycabin": "Economy Passenger Cabin",
    "businesscabin": "Business Passenger Cabin",
    "firstclasscabin": "First Class Passenger Cabin",
    "luxurycabin": "Luxury Passenger Cabin",
    # Optional Internal — Combat
    "fighterhangar": "Fighter Hangar",
    "xenoscanner": "Xeno Scanner",
    "researchlimpetcontroller": "Research Limpet Controller",
    "repairlimpetcontroller": "Repair Limpet Controller",
    "fueltransferlimpetcontroller": "Fuel Transfer Limpet Controller",
    "decontaminationlimpetcontroller": "Decontamination Limpet Controller",
    "reconlimpetcontroller": "Recon Limpet Controller",
    "operationsmultilimpetcontroller": "Operations Multi Limpet Controller",
    "universalmultilimpetcontroller": "Universal Multi Limpet Controller",
    "rescuemultilimpetcontroller": "Rescue Multi Limpet Controller",
    "miningmultilimpetcontroller": "Mining Multi Limpet Controller",
    # Utility Mounts
    "chafflauncher": "Chaff Launcher",
    "electroniccountermeasure": "Electronic Countermeasure",
    "fsdwakescanner": "Frame Shift Wake Scanner",
    "heatsinklauncher": "Heat Sink Launcher",
    "killwarrantscanner": "Kill Warrant Scanner",
    "manifestscanner": "Manifest Scanner",
    "pointdefence": "Point Defence",
    "shieldbooster": "Shield Booster",
    "shutdownfieldneutraliser": "Shutdown Field Neutraliser",
    "compositionscanner": "Composition Scanner",
    "discoveryscanner": "Discovery Scanner",
    # Hardpoint — Lasers
    "pulselaser": "Pulse Laser",
    "burstlaser": "Burst Laser",
    "beamlaser": "Beam Laser",
    "mininglaser": "Mining Laser",
    # Hardpoint — Kinetic
    "multicannon": "Multi-cannon",
    "cannon": "Cannon",
    "fragmentcannon": "Fragment Cannon",
    "railgun": "Rail Gun",
    # Hardpoint — Explosive
    "missilerack": "Missile Rack",
    "seekermissilerack": "Seeker Missile Rack",
    "torpedopylon": "Torpedo Pylon",
    "minelauncher": "Mine Launcher",
    # Hardpoint — Plasma
    "plasmaaccelerator": "Plasma Accelerator",
    # Hardpoint — AX
    "axmulticannon": "AX Multi-cannon",
    "axmissilerack": "AX Missile Rack",
    "eaxmulticannon": "Enhanced AX Multi-cannon",
    "eaxmissilerack": "Enhanced AX Missile Rack",
    # Hardpoint — Guardian
    "gausscannon": "Guardian Gauss Cannon",
    "plasmacharger": "Guardian Plasma Charger",
    "shardcannon": "Guardian Shard Cannon",
    # Hardpoint — Mining
    "abrasionblaster": "Abrasion Blaster",
    "seismiccharge": "Seismic Charge Launcher",
    "subsurfacedisplacementmissile": "Sub-surface Displacement Missile",
    # Experimental / Powerplay
    "enforcercannon": "Enforcer Cannon",
    "retributorbeamlaser": "Retributor Beam Laser",
    "cytoscrambler": "Cytoscrambler",
    "packhound": "Pack-Hound Missile Rack",
    "imperialhammer": "Imperial Hammer Rail Gun",
    "advancedplasmaaccelerator": "Advanced Plasma Accelerator",
    "pacifier": "Pacifier Fragment Cannon",
    "mininglance": "Mining Lance",
    "containmentmissile": "Containment Missile",
    "pulsedisruptor": "Pulse Disruptor Laser",
    # Additional AX / AT weapon variants
    "dumbfiremissile": "Dumbfire Missile",
    "axmissile": "AX Missile",
    "axmulticannon": "AX Multi-cannon",
    "advancedtorppylon": "Advanced Torpedo Pylon",
    # Pre-engineered / Tech Broker
    "preengineeredfsd": "Engineered Frame Shift Drive",
    "preengineeredsurfacescanner": "Pre-engineered Detailed Surface Scanner",
}

def _item_name(item: str) -> str:
    raw = item.lstrip("$").rstrip(";")
    if not raw or raw == "?":
        return "Internal"
    parts = raw.split("_")
    while parts and parts[0].lower() in _ITEM_PREFIXES:
        parts = parts[1:]
    base = parts[0].lower() if parts else ""
    mk_suffix = ""
    if len(parts) > 1 and re.match(r"^mk[\w]+", parts[1], re.I):
        mk_raw = parts[1][2:].upper()
        mk_suffix = f" (MK {mk_raw})"
        parts = [parts[0]] + parts[2:]
    if base in _ITEM_NAMES:
        return _ITEM_NAMES[base] + mk_suffix
    name = parts[0] if parts else "Internal"
    if name.islower() and not name.isdigit():
        return name.replace("_", " ").title() + mk_suffix if name else "Internal"
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
    return name + mk_suffix


def _slot_label(slot: str, item: str) -> str:
    if slot.startswith(("MediumHardpoint", "SmallHardpoint", "TinyHardpoint")):
        return _item_name(item) if item != "?" else slot
    if slot.startswith("Slot"):
        return _item_name(item) if item != "?" else "Internal"
    return _SLOT_LABELS.get(slot, slot)
