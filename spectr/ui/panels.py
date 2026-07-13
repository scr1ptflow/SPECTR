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
from spectr.edsm import EDSMClient, get_pad_size, pad_compatible
from spectr.galnet import GalnetFetcher
from spectr.inara import InaraClient
from spectr.ui.widgets import (
    CYAN, ORANGE, BLUE, PURPLE, TEAL, YELLOW, RED, PINK, GREEN, GRAY, GRAY_L, WHITE, DARK, DARK2, DARK3,
    LcarsBar, LcarsBlock, LcarsPill, HealthBar, lcars_color,
    SystemMapWidget,
)

log = logging.getLogger(__name__)


def _table_style(color: str) -> str:
    """Return a QTableWidget stylesheet for the given accent colour."""
    return (
        f"QTableWidget{{background:{DARK2};border:1px solid #0e1420;border-radius:4px;"
        f"color:{WHITE};gridline-color:#0e1420;}}"
        f"QHeaderView::section{{background:{DARK3};color:{color};font-weight:bold;"
        f"border:1px solid #0e1420;padding:4px;}}"
        f"QTableWidget::item{{padding:3px 6px;border-bottom:1px solid #151a28;}}"
    )


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


class _BodiesWorker(QThread):
    """Fetch system bodies from EDSM API."""
    done = Signal(list)

    def __init__(self, system: str, parent=None):
        super().__init__(parent)
        self.system = system

    def run(self):
        try:
            client = EDSMClient()
            data = client.get_system_details(self.system)
            if data and isinstance(data, dict):
                raw_bodies = data.get("bodies", [])
                self.done.emit([_normalize_edsm_body(b) for b in raw_bodies])
            else:
                self.done.emit([])
        except Exception as exc:
            log.warning("Bodies fetch failed: %s", exc)
            self.done.emit([])


def _normalize_edsm_body(b: dict) -> dict:
    """Convert EDSM body fields to ED journal format."""
    terraform = b.get("isTerraformable", False)
    subtype = b.get("subType", "")
    spectral = b.get("spectralClass", "")
    star_type = spectral[0] if spectral else ""
    is_star = "Star" in subtype or b.get("type") == "Star"
    return {
        "BodyId": b.get("bodyId", -1),
        "Name": b.get("name", ""),
        "DistanceFromArrivalLs": b.get("distanceToArrival"),
        "StarType": star_type if is_star else "",
        "Subclass": spectral,
        "StellarMass": b.get("solarMasses"),
        "Radius": b.get("solarRadius"),
        "SurfaceTemperature": b.get("surfaceTemperature"),
        "PlanetClass": subtype if not is_star else "",
        "Atmosphere": b.get("atmosphereType", ""),
        "Volcanism": b.get("volcanismType", ""),
        "MassEm": b.get("earthMasses"),
        "SurfaceGravity": b.get("surfaceGravity"),
        "SemiMajorAxis": b.get("semiMajorAxis"),
        "OrbitalPeriod": b.get("orbitalPeriod"),
        "RotationPeriod": b.get("rotationalPeriod"),
        "Landable": b.get("isLandable"),
        "TerraformState": "Terraformable" if terraform else "",
        "Rings": b.get("rings", []),
        "Materials": b.get("materials", []),
    }


class PanelBase(QWidget):
    """FUI-styled base panel with scrollable content area."""

    def __init__(self, window, title: str, color: str):
        super().__init__()
        self.window = window
        self._color = color

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:transparent;width:6px;border:none;}"
            "QScrollBar::handle:vertical{background:#101828;min-height:30px;}"
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


class DashboardPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Galnet News", ORANGE)
        self._articles: list = []
        self._active_btn: QPushButton | None = None
        self._worker: _GalnetWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        block = LcarsBlock("Galnet Feed", ORANGE)
        self.article_view = QTextBrowser()
        self.article_view.setOpenExternalLinks(True)
        self.article_view.setStyleSheet(
            f"background:{DARK2};border:1px solid #0e1420;border-radius:4px;"
            f"padding:8px;color:{WHITE};font-size:14px;"
        )
        block.content_layout().addWidget(self.article_view)
        c.addWidget(block, 1)

        date_row = QHBoxLayout()
        date_row.setSpacing(6)
        self.date_btns: list[QPushButton] = []
        self.date_row_layout = date_row
        c.addLayout(date_row)

        cg_block = LcarsBlock("Community Goals", ORANGE)
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

    def _on_articles_loaded(self, articles: list) -> None:
        self._articles = articles

        for btn in self.date_btns:
            btn.deleteLater()
        self.date_btns.clear()

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

        cg_keywords = {"community goal", "community goals", "galactic initiative"}
        cgs = [a for a in self._articles if any(kw in a.title.lower() for kw in cg_keywords)]
        self._on_cgs_loaded(cgs)

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


class CommanderPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Commander", ORANGE)
        self._rank_names: dict[str, QLabel] = {}
        self._rank_bars: dict[str, HealthBar] = {}
        self._finance_labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        id_block = LcarsBlock("", ORANGE)
        self.cmdr_label = QLabel()
        self.cmdr_label.setStyleSheet(f"color:{WHITE};font-size:16px;font-weight:bold;background:transparent;")
        id_block.content_layout().addWidget(self.cmdr_label)
        c.addWidget(id_block)

        c.addWidget(LcarsBar(ORANGE, 2))

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

        c.addWidget(LcarsBar(ORANGE, 2))
        self.pp_block = LcarsBlock("Powerplay", PINK)
        self.pp_inner = QVBoxLayout()
        self.pp_inner.setSpacing(2)
        self.pp_block.content_layout().addLayout(self.pp_inner)
        c.addWidget(self.pp_block)

        c.addWidget(LcarsBar(ORANGE, 2))
        fin_block = LcarsBlock("Finances", TEAL)
        fin_inner = QVBoxLayout()
        fin_inner.setSpacing(4)
        fin_block.content_layout().addLayout(fin_inner)

        _FINANCE_COLORS = {
            "credits":  YELLOW,
            "arx":      ORANGE,
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
        text = f"<span style='color:{ORANGE}'>{cmdr}</span>"
        if squadron:
            text += f"  <span style='color:{GRAY}'>— {squadron}</span>"
        self.cmdr_label.setText(text)

        ranks = journal.get_rank_levels()
        progress = journal.get_rank_progress()

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


class ShipPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Ship", ORANGE)
        self._module_cells: list[QWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        id_block = LcarsBlock("", ORANGE)
        self.ship_name_label = QLabel()
        self.ship_name_label.setAlignment(Qt.AlignCenter)
        self.ship_name_label.setStyleSheet(f"color:{WHITE};font-size:16px;font-weight:bold;background:transparent;")
        id_block.content_layout().addWidget(self.ship_name_label)
        c.addWidget(id_block)

        c.addWidget(LcarsBar(ORANGE, 2))
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.shield_stat = self._make_stat_box("Shield Generator", ORANGE)
        stats_row.addWidget(self.shield_stat)

        self.fuel_stat = LcarsBlock("Fuel Tank", ORANGE)
        fuel_integrity_bar = HealthBar()
        fuel_integrity_bar.setObjectName("stat-bar-fuel")
        fuel_integrity_bar.setFixedHeight(18)
        self.fuel_stat.content_layout().addWidget(fuel_integrity_bar)
        self._fuel_numbers = QLabel("0.0t / 0.0t")
        self._fuel_numbers.setAlignment(Qt.AlignCenter)
        self._fuel_numbers.setStyleSheet(f"color:{WHITE};font-size:12px;font-weight:bold;background:transparent;")
        self.fuel_stat.content_layout().addWidget(self._fuel_numbers)
        stats_row.addWidget(self.fuel_stat)

        self.hull_stat = self._make_stat_box("Hull Integrity", ORANGE)
        stats_row.addWidget(self.hull_stat)

        c.addLayout(stats_row)

        c.addWidget(LcarsBar(ORANGE, 4))
        self._module_block = LcarsBlock("", ORANGE)
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
            parts.append(f"<span style='color:{ORANGE}'><b>{ship_name}</b></span>")
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

        for w in self._module_cells:
            w.deleteLater()
        self._module_cells.clear()

        cols = 2
        for i, m in enumerate(filtered):
            slot = m.get("Slot", "?")
            item = m.get("Item", "?")
            name = m.get("Item_Localised") or _slot_label(slot, item)
            health = m.get("Health", 1.0)

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
            cell.setStyleSheet(f"background:{DARK2};border-radius:4px;border:1px solid #0e1420;")
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


class LocationPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Location", ORANGE)
        self._bodies: list[dict] = []
        self._selected_body: dict | None = None
        self._bodies_worker: _BodiesWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        map_block = LcarsBlock("System Map", ORANGE)
        self.map_widget = SystemMapWidget()
        self.map_widget.body_clicked.connect(self._on_body_clicked)
        self.map_widget.setMinimumHeight(450)
        map_block.content_layout().addWidget(self.map_widget)
        top_row.addWidget(map_block, 4)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        sys_block = LcarsBlock("System Info", ORANGE)
        sys_inner = QVBoxLayout()
        sys_inner.setSpacing(2)
        self._sys_labels: dict[str, QLabel] = {}
        for key in ("system", "faction", "government", "economy", "security", "allegiance", "population", "station"):
            lbl = QLabel("")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color:{WHITE};font-size:12px;background:transparent;")
            sys_inner.addWidget(lbl)
            self._sys_labels[key] = lbl
        sys_block.content_layout().addLayout(sys_inner)
        right_col.addWidget(sys_block)

        top_row.addLayout(right_col, 1)
        c.addLayout(top_row, 1)

        c.addWidget(LcarsBar(ORANGE, 2))

        body_block = LcarsBlock("Body Details", ORANGE)
        body_block.setMaximumHeight(180)
        self._body_inner = QVBoxLayout()
        self._body_inner.setSpacing(2)
        self._body_labels: dict[str, QLabel] = {}
        self._body_placeholder = QLabel("Click a body on the map to view details")
        self._body_placeholder.setStyleSheet(f"color:{GRAY};font-size:12px;background:transparent;")
        self._body_placeholder.setAlignment(Qt.AlignCenter)
        self._body_inner.addWidget(self._body_placeholder)
        body_block.content_layout().addLayout(self._body_inner)
        c.addWidget(body_block)

    def _on_body_clicked(self, body: dict) -> None:
        self._selected_body = body if body else None
        self._update_body_info()

    def _update_body_info(self) -> None:
        while self._body_inner.count():
            item = self._body_inner.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._body_labels.clear()

        if not self._selected_body:
            lbl = QLabel("Click a body on the map to view details")
            lbl.setStyleSheet(f"color:{GRAY};font-size:12px;background:transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            self._body_inner.addWidget(lbl)
            return

        b = self._selected_body
        name = b.get("Name", "Unknown")
        header = QLabel(f"<span style='color:{ORANGE};font-size:14px;font-weight:bold'>{name}</span>")
        header.setStyleSheet("background:transparent;")
        self._body_inner.addWidget(header)

        fields = []
        btype = "Star" if b.get("StarType") else "Planet"
        fields.append(("Type", btype))

        if b.get("StarType"):
            fields.append(("Spectral Type", f"{b['StarType']}{b.get('Subclass', '')}"))
            if b.get("StellarMass"):
                fields.append(("Mass", f"{b['StellarMass']:.2f} M☉"))
            if b.get("Radius"):
                fields.append(("Radius", f"{b['Radius'] / 695700:.1f} R☉"))
            if b.get("SurfaceTemperature"):
                fields.append(("Temperature", f"{b['SurfaceTemperature']:.0f} K"))
            if b.get("DistanceFromArrivalLs") is not None:
                fields.append(("Distance", f"{b['DistanceFromArrivalLs']:.1f} Ls"))
        else:
            if b.get("PlanetClass"):
                fields.append(("Class", b["PlanetClass"]))
            if b.get("Atmosphere"):
                fields.append(("Atmosphere", b["Atmosphere"]))
            if b.get("Volcanism"):
                fields.append(("Volcanism", b["Volcanism"]))
            if b.get("MassEm"):
                fields.append(("Mass", f"{b['MassEm']:.3f} M⊕"))
            if b.get("SurfaceGravity"):
                fields.append(("Gravity", f"{b['SurfaceGravity']:.1f} g"))
            if b.get("SurfaceTemperature"):
                fields.append(("Temperature", f"{b['SurfaceTemperature']:.0f} K"))
            if b.get("DistanceFromArrivalLs") is not None:
                fields.append(("Distance", f"{b['DistanceFromArrivalLs']:.1f} Ls"))
            if b.get("OrbitalPeriod"):
                period_h = b["OrbitalPeriod"] / 3600
                fields.append(("Orbital Period", f"{period_h:.1f} h"))
            if b.get("RotationPeriod"):
                rot_h = abs(b["RotationPeriod"]) / 3600
                fields.append(("Rotation", f"{rot_h:.1f} h"))
            if b.get("SemiMajorAxis"):
                fields.append(("Semi-Major Axis", f"{b['SemiMajorAxis']:.0f} km"))
            if b.get("Landable") is not None:
                fields.append(("Landable", "Yes" if b["Landable"] else "No"))
            if b.get("TerraformState"):
                fields.append(("Terraform", b["TerraformState"]))

        rings = b.get("Rings") or []
        if rings:
            ring_names = ", ".join(r.get("Name", "?").split()[-1] for r in rings[:4])
            fields.append(("Rings", ring_names))

        mats = b.get("Materials") or []
        if mats:
            mat_names = [m.get("Name", "?") for m in mats[:6]]
            fields.append(("Materials", ", ".join(mat_names)))

        for label, value in fields:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl_key = QLabel(f"{label}:")
            lbl_key.setFixedWidth(110)
            lbl_key.setStyleSheet(f"color:{ORANGE};font-weight:bold;font-size:11px;background:transparent;")
            row.addWidget(lbl_key)
            lbl_val = QLabel(str(value))
            lbl_val.setStyleSheet(f"color:{WHITE};font-size:11px;background:transparent;")
            row.addWidget(lbl_val)
            self._body_inner.addLayout(row)

        self._body_inner.addStretch()

    def refresh(self) -> None:
        journal = self.window.journal
        info = journal.get_system_info()
        self._bodies = journal.get_system_bodies()
        self.map_widget.set_bodies(self._bodies)

        system = info.get("system", "")
        if not self._bodies and system:
            self._bodies_worker = _BodiesWorker(system, self)
            self._bodies_worker.done.connect(self._on_bodies_from_edsm)
            self._bodies_worker.start()

        self._sys_labels["system"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>System:</span>  "
            f"<span style='color:{WHITE}'>{info.get('system', 'Unknown')}</span>"
        )
        self._sys_labels["faction"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Faction:</span>  "
            f"<span style='color:{WHITE}'>{info.get('faction', '-')}</span>"
        )
        self._sys_labels["government"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Government:</span>  "
            f"<span style='color:{WHITE}'>{info.get('government', '-')}</span>"
        )
        self._sys_labels["economy"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Economy:</span>  "
            f"<span style='color:{WHITE}'>{info.get('economy', '-')}</span>"
        )
        self._sys_labels["security"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Security:</span>  "
            f"<span style='color:{WHITE}'>{info.get('security', '-')}</span>"
        )
        self._sys_labels["allegiance"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Allegiance:</span>  "
            f"<span style='color:{WHITE}'>{info.get('allegiance', '-')}</span>"
        )
        pop = info.get("population", 0)
        self._sys_labels["population"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Population:</span>  "
            f"<span style='color:{WHITE}'>{pop:,}</span>"
        )
        station = info.get("station", "")
        self._sys_labels["station"].setText(
            f"<span style='color:{ORANGE};font-weight:bold'>Station:</span>  "
            f"<span style='color:{WHITE}'>{station if station else '-'}</span>"
        )

        self._selected_body = None
        self._update_body_info()

    def _on_bodies_from_edsm(self, bodies: list) -> None:
        if bodies:
            self._bodies = bodies
            self.map_widget.set_bodies(self._bodies)
            self.map_widget.update()


class MissionsPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Missions", ORANGE)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        active_block = LcarsBlock("Active Missions", ORANGE)
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(4)
        self.active_table.setHorizontalHeaderLabels(["Timestamp", "Mission", "Destination", "Expires"])
        self.active_table.horizontalHeader().setStretchLastSection(True)
        self.active_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.active_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.active_table.setSelectionMode(QTableWidget.NoSelection)
        self._style_table(self.active_table, ORANGE)
        active_block.content_layout().addWidget(self.active_table)
        c.addWidget(active_block, 1)

        c.addWidget(LcarsBar(ORANGE, 2))
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
        table.setStyleSheet(_table_style(color))

    def refresh(self) -> None:
        journal = self.window.journal

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


class LaboratoryPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Laboratory", ORANGE)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        c.addLayout(summary_row)

        self.count_stat = self._make_summary_block("Sellable Samples", ORANGE)
        summary_row.addWidget(self.count_stat)
        self.value_stat = self._make_summary_block("Predicted Value", ORANGE)
        summary_row.addWidget(self.value_stat)

        c.addWidget(LcarsBar(ORANGE, 2))
        block = LcarsBlock("Pending Organic Data", ORANGE)
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(6)
        self.detail_table.setHorizontalHeaderLabels(["System", "Body", "Species", "Sets", "Value", "First Footfall"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.detail_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.detail_table.setSelectionMode(QTableWidget.NoSelection)
        self.detail_table.setStyleSheet(_table_style(ORANGE))
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
            self.detail_table.setItem(i, 5, QTableWidgetItem(""))


class SettingsPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Settings", ORANGE)
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        block = LcarsBlock("Configuration", ORANGE)
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
                f"QLineEdit{{padding:6px 8px;border:1px solid #0e1420;border-radius:4px;"
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
        self.status_label.setStyleSheet(f"color:{GREEN};padding:4px 0;background:transparent;")
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

        warnings = validate_config(new_config)
        if warnings:
            self.status_label.setStyleSheet(f"color:{YELLOW};padding:4px 0;background:transparent;")
            self.status_label.setText("Saved with warnings: " + "; ".join(warnings))
        else:
            self.status_label.setStyleSheet(f"color:{GREEN};padding:4px 0;background:transparent;")
            self.status_label.setText("Settings saved successfully.")

        save_config(new_config)
        from spectr.config import DEFAULT_CONFIG
        self.window.config = {**DEFAULT_CONFIG, **new_config}
        self.window.journal.set_path(new_config.get("journal_path", ""))


class _ScannerWorker(QThread):
    """Search nearby systems for stations using EDSM API."""
    done = Signal(list)

    def __init__(self, system: str, ship_type: str, radius: int, mode: str, parent=None):
        super().__init__(parent)
        self.system = system
        self.ship_type = ship_type
        self.radius = radius
        self.mode = mode

    def run(self):
        try:
            client = EDSMClient()
            pad_size = get_pad_size(self.ship_type)
            nearby = client.get_nearby_systems(self.system, self.radius, 200)

            results = []
            for sys_data in nearby[:50]:
                sys_name = sys_data.get("name", "")
                dist = sys_data.get("distance", 0)
                if not sys_name or sys_name == self.system:
                    continue

                stations = client.get_stations(sys_name)
                for st in stations:
                    name = st.get("name", "")
                    st_type = st.get("type", "")
                    max_pads = st.get("maxLandingPadSize", "L")
                    distance = st.get("distanceToArrival", 0)
                    is_planetary = st.get("isPlanetary", False)
                    controlling_faction = st.get("controllingFaction", {})
                    faction_name = controlling_faction.get("name", "") if isinstance(controlling_faction, dict) else ""
                    services = st.get("services", [])

                    if self.mode == "carriers" and "Fleet Carrier" not in st_type:
                        continue
                    if self.mode == "stations" and "Fleet Carrier" in st_type:
                        continue

                    if not pad_compatible(max_pads, pad_size):
                        continue

                    results.append({
                        "system": sys_name,
                        "distance_ly": dist,
                        "name": name,
                        "type": st_type,
                        "max_pads": max_pads,
                        "distance_ls": distance,
                        "planetary": is_planetary,
                        "faction": faction_name,
                        "services": services,
                    })

            results.sort(key=lambda x: (x["distance_ly"], x["distance_ls"]))
            self.done.emit(results[:50])
        except Exception as exc:
            log.warning("Scanner worker failed: %s", exc)
            self.done.emit([])


class _EngineerWorker(QThread):
    """Fetch engineer data from Inara API."""
    done = Signal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config

    def run(self):
        try:
            api_key = self.config.get("inara_api_key", "")
            cmdr = self.config.get("commander_name", "")
            if not api_key or not cmdr:
                self.done.emit({})
                return

            client = InaraClient(
                api_key=api_key,
                cmdr_name=cmdr,
                app_name=self.config.get("inara_app_name", "SPECTR"),
            )
            profile = client.get_commander_profile()
            engineers = profile.get("commanderEngineers", []) if profile else []
            self.done.emit({"engineers": engineers})
        except Exception as exc:
            log.warning("Engineer worker failed: %s", exc)
            self.done.emit({})


class ScannerPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Scanner", ORANGE)
        self._worker: _ScannerWorker | None = None
        self._results: list[dict] = []
        self._mode = "all"
        self._selected_radius = 50
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        ctrl_block = LcarsBlock("Scan Parameters", ORANGE)
        ctrl_inner = QVBoxLayout()
        ctrl_inner.setSpacing(4)

        self.ship_info = QLabel("Ship: Unknown")
        self.ship_info.setStyleSheet(f"color:{WHITE};font-size:12px;background:transparent;")
        ctrl_inner.addWidget(self.ship_info)

        radius_row = QHBoxLayout()
        radius_row.setSpacing(8)
        radius_lbl = QLabel("Radius:")
        radius_lbl.setStyleSheet(f"color:{ORANGE};font-weight:bold;background:transparent;")
        radius_row.addWidget(radius_lbl)
        self.radius_btns: list[QPushButton] = []
        for r in [25, 50, 100]:
            btn = QPushButton(f"{r} LY")
            btn.setFixedSize(60, 28)
            btn.setProperty("radius", r)
            btn.clicked.connect(self._on_radius_click)
            radius_row.addWidget(btn)
            self.radius_btns.append(btn)
        ctrl_inner.addLayout(radius_row)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_lbl = QLabel("Filter:")
        mode_lbl.setStyleSheet(f"color:{ORANGE};font-weight:bold;background:transparent;")
        mode_row.addWidget(mode_lbl)
        self.mode_btns: list[QPushButton] = []
        for mode_id, label in [("all", "All"), ("stations", "Stations"), ("carriers", "Carriers")]:
            btn = QPushButton(label)
            btn.setFixedSize(80, 28)
            btn.setProperty("mode", mode_id)
            btn.clicked.connect(self._on_mode_click)
            mode_row.addWidget(btn)
            self.mode_btns.append(btn)
        ctrl_inner.addLayout(mode_row)

        scan_row = QHBoxLayout()
        self.scan_btn = LcarsPill("SCAN", ORANGE)
        self.scan_btn.clicked.connect(self._start_scan)
        scan_row.addWidget(self.scan_btn)
        scan_row.addStretch()
        ctrl_inner.addLayout(scan_row)

        self.status_label = QLabel("Ready to scan")
        self.status_label.setStyleSheet(f"color:{GRAY};font-size:11px;background:transparent;")
        ctrl_inner.addWidget(self.status_label)

        ctrl_block.content_layout().addLayout(ctrl_inner)
        c.addWidget(ctrl_block)

        c.addWidget(LcarsBar(ORANGE, 2))
        results_block = LcarsBlock("Nearby Stations & Carriers", ORANGE)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(
            ["Name", "System", "Dist (LY)", "Dist (Ls)", "Type", "Pads", "Faction"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.results_table.setSelectionMode(QTableWidget.NoSelection)
        self.results_table.setStyleSheet(_table_style(ORANGE))
        results_block.content_layout().addWidget(self.results_table)
        c.addWidget(results_block, 1)

    def refresh(self) -> None:
        journal = self.window.journal

        ship_type = journal.get_ship_type() or "Unknown"
        pad = get_pad_size(self.window.journal.get_latest_event("Loadout").get("Ship", "") if journal.get_latest_event("Loadout") else "")
        pad_label = {"S": "Small", "M": "Medium", "L": "Large"}.get(pad, "Unknown")
        system = journal.get_current_system() or "Unknown"

        self.ship_info.setText(
            f"<span style='color:{ORANGE}'>{ship_type}</span>  |  "
            f"Pad: <span style='color:{YELLOW}'>{pad_label}</span>  |  "
            f"System: <span style='color:{WHITE}'>{system}</span>"
        )

        for btn in self.radius_btns:
            r = btn.property("radius")
            active = r == 50
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )

        for btn in self.mode_btns:
            m = btn.property("mode")
            active = m == self._mode
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )

    def _on_radius_click(self):
        btn = self.sender()
        if not btn:
            return
        self._selected_radius = btn.property("radius")
        for b in self.radius_btns:
            br = b.property("radius")
            active = br == self._selected_radius
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            b.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )

    def _on_mode_click(self):
        btn = self.sender()
        if not btn:
            return
        self._mode = btn.property("mode")
        for b in self.mode_btns:
            m = b.property("mode")
            active = m == self._mode
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            b.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )

    def _start_scan(self):
        system = self.window.journal.get_current_system()
        if not system:
            self.status_label.setText("No system data available")
            return

        loadout = self.window.journal.get_latest_event("Loadout")
        ship = loadout.get("Ship", "") if loadout else ""

        radius = self._selected_radius

        self.status_label.setText(f"Scanning {radius} LY radius...")
        self.scan_btn.setEnabled(False)

        self._worker = _ScannerWorker(system, ship, radius, self._mode, self)
        self._worker.done.connect(self._on_scan_done)
        self._worker.start()

    def _on_scan_done(self, results: list):
        self._results = results
        self.scan_btn.setEnabled(True)
        self.status_label.setText(f"Found {len(results)} landing-compatible locations")

        self.results_table.setRowCount(len(results))
        for i, r in enumerate(results):
            name_item = QTableWidgetItem(r["name"])
            if "Fleet Carrier" in r["type"]:
                name_item.setForeground(QColor(YELLOW))
            self.results_table.setItem(i, 0, name_item)
            self.results_table.setItem(i, 1, QTableWidgetItem(r["system"][:18]))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{r['distance_ly']:.1f}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{r['distance_ls']:.0f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(r["type"][:18]))
            self.results_table.setItem(i, 5, QTableWidgetItem(r["max_pads"]))
            self.results_table.setItem(i, 6, QTableWidgetItem(r["faction"][:20]))


class CaptainsLogPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Captain's Log", ORANGE)
        self._events: list[dict] = []
        self._filter = "all"
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        ctrl_block = LcarsBlock("Log Controls", ORANGE)
        ctrl_inner = QHBoxLayout()
        ctrl_inner.setSpacing(8)

        self.filter_btns: list[QPushButton] = []
        for filt_id, label in [
            ("all", "All Events"),
            ("travel", "Travel"),
            ("combat", "Combat"),
            ("trade", "Trade"),
            ("exploration", "Exploration"),
            ("ship", "Ship"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setProperty("filter", filt_id)
            btn.clicked.connect(self._on_filter_click)
            ctrl_inner.addWidget(btn)
            self.filter_btns.append(btn)

        ctrl_inner.addStretch()

        refresh_btn = LcarsPill("REFRESH", ORANGE)
        refresh_btn.clicked.connect(self.refresh)
        ctrl_inner.addWidget(refresh_btn)

        ctrl_block.content_layout().addLayout(ctrl_inner)
        c.addWidget(ctrl_block)

        c.addWidget(LcarsBar(ORANGE, 2))
        log_block = LcarsBlock("Mission Log", ORANGE)
        self.log_view = QTextBrowser()
        self.log_view.setOpenExternalLinks(False)
        self.log_view.setStyleSheet(
            f"background:{DARK2};border:1px solid #0e1420;border-radius:4px;"
            f"padding:8px;color:{WHITE};"
        )
        log_block.content_layout().addWidget(self.log_view)
        c.addWidget(log_block, 1)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.event_count = QLabel("0 events")
        self.event_count.setStyleSheet(f"color:{GRAY};font-size:11px;background:transparent;")
        stats_row.addWidget(self.event_count)
        stats_row.addStretch()
        self.session_time = QLabel("")
        self.session_time.setStyleSheet(f"color:{GRAY};font-size:11px;background:transparent;")
        stats_row.addWidget(self.session_time)
        c.addLayout(stats_row)

    def refresh(self) -> None:
        journal = self.window.journal
        self._events = self._collect_log_events(journal)
        self._render_log()
        self._highlight_filter()

    def _collect_log_events(self, journal) -> list[dict]:
        log_events = []
        event_categories = {
            "FSDJump": "travel",
            "Location": "travel",
            "Docked": "travel",
            "Undocked": "travel",
            "SupercruiseEntry": "travel",
            "SupercruiseExit": "travel",
            "Touchdown": "travel",
            "Liftoff": "travel",
            "ApproachBody": "travel",
            "LeaveBody": "travel",
            "Interdicted": "combat",
            "PVPKill": "combat",
            "Died": "combat",
            "HullDamage": "combat",
            "ShieldDamage": "combat",
            "BuyTradeGood": "trade",
            "SellTradeGood": "trade",
            "MarketBuy": "trade",
            "MarketSell": "trade",
            "MiningRefined": "trade",
            "Scan": "exploration",
            "FSSDiscoveryScan": "exploration",
            "FSSSignalDiscovered": "exploration",
            "FSSAllBodiesFound": "exploration",
            "SAAScanComplete": "exploration",
            "ScanOrganic": "exploration",
            "SellOrganicData": "exploration",
            "CodexEntry": "exploration",
            "Loadout": "ship",
            "ModuleBuy": "ship",
            "ModuleSell": "ship",
            "EngineerCraft": "ship",
            "EngineerCraftFailed": "ship",
            "Synthesis": "ship",
            "Repair": "ship",
            "BuyAmmo": "ship",
            "RefuelAll": "ship",
            "BuyShip": "ship",
            "SellShip": "ship",
            "StoreShip": "ship",
            "RetrieveShip": "ship",
            "MissionAccepted": "all",
            "MissionCompleted": "all",
            "MissionFailed": "all",
            "MissionAbandoned": "all",
        }

        for event in journal.read_all_events():
            category = event_categories.get(event.event)
            if category is None:
                continue

            timestamp = event.timestamp
            desc = self._describe_event(event)
            if desc:
                log_events.append({
                    "timestamp": timestamp,
                    "event": event.event,
                    "category": category,
                    "description": desc,
                })

        log_events.sort(key=lambda x: x["timestamp"], reverse=True)
        return log_events[:200]

    def _describe_event(self, event) -> str:
        ev = event.event

        if ev == "FSDJump":
            star = event.get("StarSystem", "?")
            return f"Jumped to <b>{star}</b>"
        elif ev == "Location":
            star = event.get("StarSystem", "?")
            body = event.get("Body", "")
            if body:
                return f"Entered system <b>{star}</b>, orbiting <b>{body}</b>"
            return f"Entered system <b>{star}</b>"
        elif ev == "Docked":
            station = event.get("StationName", "?")
            system = event.get("StarSystem", "")
            return f"Docked at <b>{station}</b> in {system}"
        elif ev == "Undocked":
            station = event.get("StationName", "?")
            return f"Undocked from <b>{station}</b>"
        elif ev == "SupercruiseEntry":
            return "Entered supercruise"
        elif ev == "SupercruiseExit":
            return "Dropped from supercruise"
        elif ev == "Touchdown":
            body = event.get("Body", "?")
            return f"Landed on <b>{body}</b>"
        elif ev == "Liftoff":
            body = event.get("Body", "?")
            return f"Lifted off from <b>{body}</b>"
        elif ev == "ApproachBody":
            body = event.get("Body", "?")
            return f"Approaching <b>{body}</b>"
        elif ev == "LeaveBody":
            body = event.get("Body", "?")
            return f"Leaving <b>{body}</b>"
        elif ev == "Scan":
            name = event.get("BodyName", "?")
            return f"Scanned <b>{name}</b>"
        elif ev == "Interdicted":
            attacker = event.get("Interdictor", "Unknown")
            return f"Interdicted by <b>{attacker}</b>"
        elif ev == "PVPKill":
            victim = event.get("Victim", "Unknown")
            return f"Destroyed <b>{victim}</b>"
        elif ev == "Died":
            killer = event.get("KillerName", "Unknown")
            return f"Destroyed by <b>{killer}</b>"
        elif ev == "MarketBuy":
            item = event.get("Type_Localised", event.get("Type", "?"))
            count = event.get("Count", 0)
            return f"Bought {count}x <b>{item}</b>"
        elif ev == "MarketSell":
            item = event.get("Type_Localised", event.get("Type", "?"))
            count = event.get("Count", 0)
            return f"Sold {count}x <b>{item}</b>"
        elif ev == "MiningRefined":
            item = event.get("Type_Localised", event.get("Type", "?"))
            return f"Refined <b>{item}</b>"
        elif ev == "FSSDiscoveryScan":
            body_count = event.get("BodyCount", 0)
            return f"Discovery scan — {body_count} bodies"
        elif ev == "FSSSignalDiscovered":
            name = event.get("SignalName", "?")
            return f"Discovered signal: <b>{name}</b>"
        elif ev == "FSSAllBodiesFound":
            system = event.get("SystemName", "?")
            return f"All bodies found in <b>{system}</b>"
        elif ev == "SAAScanComplete":
            body = event.get("BodyName", "?")
            probes = event.get("ProbesUsed", 0)
            return f"Surface scan complete: <b>{body}</b> ({probes} probes)"
        elif ev == "ScanOrganic":
            species = event.get("Species_Localised", event.get("Species", "?"))
            body = event.get("Body", "?")
            scan_type = event.get("ScanType", "Sample")
            return f"{scan_type}: <b>{species}</b> on {body}"
        elif ev == "SellOrganicData":
            return "Sold organic scan data"
        elif ev == "EngineerCraft":
            engineer = event.get("Engineer", "?")
            slot = event.get("Slot", "?")
            return f"Engineered <b>{slot}</b> at {engineer}"
        elif ev == "EngineerCraftFailed":
            engineer = event.get("Engineer", "?")
            return f"Engineering failed at {engineer}"
        elif ev == "MissionAccepted":
            name = event.get("Name", "?")
            return f"Accepted mission: <b>{name}</b>"
        elif ev == "MissionCompleted":
            name = event.get("Name", "?")
            reward = event.get("Reward", 0)
            if reward:
                return f"Completed mission: <b>{name}</b> — {reward:,} CR"
            return f"Completed mission: <b>{name}</b>"
        elif ev == "MissionFailed":
            name = event.get("Name", "?")
            return f"Mission failed: <b>{name}</b>"
        elif ev == "MissionAbandoned":
            name = event.get("Name", "?")
            return f"Mission abandoned: <b>{name}</b>"
        elif ev == "Synthesis":
            name = event.get("Name", "?")
            return f"Synthesized: <b>{name}</b>"
        elif ev == "Loadout":
            ship = event.get("ShipName", event.get("Ship", "?"))
            return f"Ship refit: <b>{ship}</b>"
        elif ev == "BuyShip":
            ship = event.get("ShipType", "?")
            return f"Purchased ship: <b>{ship}</b>"
        elif ev == "SellShip":
            ship = event.get("ShipType", "?")
            return f"Sold ship: <b>{ship}</b>"
        elif ev == "RefuelAll":
            return "Refueled"
        elif ev == "Repair":
            item = event.get("Item", "?")
            return f"Repaired: <b>{item}</b>"
        elif ev == "BuyAmmo":
            return "Purchased ammunition"
        elif ev == "HullDamage":
            return "Hull damage received"
        elif ev == "ShieldDamage":
            return "Shield damage received"
        elif ev == "CodexEntry":
            name = event.get("Name", "?")
            return f"Codex entry: <b>{name}</b>"
        elif ev == "ModuleBuy":
            slot = event.get("Slot", "?")
            item = event.get("BuyItem", "?")
            return f"Installed <b>{item}</b> in {slot}"
        elif ev == "ModuleSell":
            slot = event.get("Slot", "?")
            return f"Removed module from {slot}"
        elif ev == "StoreShip":
            ship = event.get("ShipType", "?")
            return f"Stored ship: <b>{ship}</b>"
        elif ev == "RetrieveShip":
            ship = event.get("ShipType", "?")
            return f"Retrieved ship: <b>{ship}</b>"
        elif ev == "BuyTradeGood":
            item = event.get("Type_Localised", event.get("Type", "?"))
            return f"Purchased trade goods: <b>{item}</b>"
        elif ev == "SellTradeGood":
            item = event.get("Type_Localised", event.get("Type", "?"))
            return f"Sold trade goods: <b>{item}</b>"
        return ""

    def _render_log(self):
        filtered = self._events
        if self._filter != "all":
            filtered = [e for e in self._events if e["category"] == self._filter]

        if not filtered:
            self.log_view.setHtml(
                f"<span style='color:{GRAY}'>No events recorded</span>"
            )
            self.event_count.setText("0 events")
            return

        lines = []
        for ev in filtered:
            cat_color = {
                "travel": CYAN,
                "combat": RED,
                "trade": YELLOW,
                "exploration": GREEN,
                "ship": BLUE,
                "all": GRAY,
            }.get(ev["category"], GRAY)

            lines.append(
                f"<span style='color:{GRAY}'>{ev['timestamp'][:19]}</span>  "
                f"<span style='color:{cat_color}'>[{ev['category'].upper()}]</span>  "
                f"{ev['description']}"
            )

        self.log_view.setHtml("<br>".join(lines))
        self.event_count.setText(f"{len(filtered)} events")

    def _on_filter_click(self):
        btn = self.sender()
        if not btn:
            return
        self._filter = btn.property("filter")
        self._highlight_filter()
        self._render_log()

    def _highlight_filter(self):
        for btn in self.filter_btns:
            f = btn.property("filter")
            active = f == self._filter
            bg = ORANGE if active else "transparent"
            fg = DARK if active else ORANGE
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};border:1px solid {ORANGE};"
                f"color:{fg};border-radius:4px;font-weight:bold;font-size:11px;}}"
                f"QPushButton:hover{{background:{ORANGE};color:{DARK};}}"
            )


class EngineeringPanel(PanelBase):
    def __init__(self, window):
        super().__init__(window, "Engineering", ORANGE)
        self._engineer_data: dict = {}
        self._worker: _EngineerWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        c = self.content_layout()

        mats_row = QHBoxLayout()
        mats_row.setSpacing(10)

        raw_block = LcarsBlock("Raw", ORANGE)
        self.raw_table = QTableWidget()
        self.raw_table.setColumnCount(3)
        self.raw_table.setHorizontalHeaderLabels(["Material", "Count", "Max"])
        self.raw_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.raw_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.raw_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.raw_table.setSelectionMode(QTableWidget.NoSelection)
        self.raw_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.raw_table.setStyleSheet(_table_style(ORANGE))
        raw_block.content_layout().addWidget(self.raw_table)
        mats_row.addWidget(raw_block, 1)

        mfg_block = LcarsBlock("Manufactured", ORANGE)
        self.mfg_table = QTableWidget()
        self.mfg_table.setColumnCount(4)
        self.mfg_table.setHorizontalHeaderLabels(["Material", "Grade", "Count", "Max"])
        self.mfg_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mfg_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.mfg_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.mfg_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.mfg_table.setSelectionMode(QTableWidget.NoSelection)
        self.mfg_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mfg_table.setStyleSheet(_table_style(ORANGE))
        mfg_block.content_layout().addWidget(self.mfg_table)
        mats_row.addWidget(mfg_block, 1)

        enc_block = LcarsBlock("Encoded", ORANGE)
        self.enc_table = QTableWidget()
        self.enc_table.setColumnCount(4)
        self.enc_table.setHorizontalHeaderLabels(["Material", "Grade", "Count", "Max"])
        self.enc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.enc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.enc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.enc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.enc_table.setSelectionMode(QTableWidget.NoSelection)
        self.enc_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.enc_table.setStyleSheet(_table_style(ORANGE))
        enc_block.content_layout().addWidget(self.enc_table)
        mats_row.addWidget(enc_block, 1)

        c.addLayout(mats_row, 1)

        c.addWidget(LcarsBar(ORANGE, 2))
        eng_block = LcarsBlock("Engineers", ORANGE)

        self.eng_status = QLabel("Loading engineer data...")
        self.eng_status.setStyleSheet(f"color:{GRAY};background:transparent;")
        eng_block.content_layout().addWidget(self.eng_status)

        self.eng_table = QTableWidget()
        self.eng_table.setColumnCount(4)
        self.eng_table.setHorizontalHeaderLabels(["Engineer", "System", "Rank", "Progress"])
        self.eng_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.eng_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.eng_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.eng_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.eng_table.setSelectionMode(QTableWidget.NoSelection)
        self.eng_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.eng_table.setStyleSheet(_table_style(ORANGE))
        eng_block.content_layout().addWidget(self.eng_table)
        c.addWidget(eng_block, 1)

    def refresh(self) -> None:
        journal = self.window.journal
        config = self.window.config

        raw_mats, mfg_mats, enc_mats = self._collect_materials(journal)

        self._fill_raw_table(raw_mats)
        self._fill_graded_table(self.mfg_table, mfg_mats)
        self._fill_graded_table(self.enc_table, enc_mats)

        self.eng_status.setText("Loading engineer data from Inara...")
        self._worker = _EngineerWorker(config, self)
        self._worker.done.connect(self._on_engineers_loaded)
        self._worker.start()

    def _fill_raw_table(self, materials: list[dict]):
        self.raw_table.setRowCount(len(materials))
        for i, m in enumerate(materials):
            self.raw_table.setItem(i, 0, QTableWidgetItem(m["name"]))
            count_item = QTableWidgetItem(str(m["count"]))
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if m["count"] >= m["max"]:
                count_item.setForeground(QColor(RED))
            elif m["count"] >= m["max"] * 0.8:
                count_item.setForeground(QColor(YELLOW))
            self.raw_table.setItem(i, 1, count_item)
            max_item = QTableWidgetItem(str(m["max"]))
            max_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.raw_table.setItem(i, 2, max_item)

    def _fill_graded_table(self, table: QTableWidget, materials: list[dict]):
        table.setRowCount(len(materials))
        for i, m in enumerate(materials):
            table.setItem(i, 0, QTableWidgetItem(m["name"]))
            grade_item = QTableWidgetItem(str(m["grade"]))
            grade_item.setTextAlignment(Qt.AlignCenter)
            grade_color = GREEN if m["grade"] >= 4 else YELLOW if m["grade"] >= 2 else WHITE
            grade_item.setForeground(QColor(grade_color))
            table.setItem(i, 1, grade_item)
            count_item = QTableWidgetItem(str(m["count"]))
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if m["count"] >= m["max"]:
                count_item.setForeground(QColor(RED))
            elif m["count"] >= m["max"] * 0.8:
                count_item.setForeground(QColor(YELLOW))
            table.setItem(i, 2, count_item)
            max_item = QTableWidgetItem(str(m["max"]))
            max_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 3, max_item)

    def _collect_materials(self, journal) -> tuple[list[dict], list[dict], list[dict]]:
        """Collect materials from journal, separated by type with grades."""
        raw_mats = []
        mfg_mats = []
        enc_mats = []

        event = journal.get_latest_event("Materials")
        if not event:
            return raw_mats, mfg_mats, enc_mats

        for mat in event.get("Raw", []):
            name = mat.get("Name", "")
            count = mat.get("Count", 0)
            raw_mats.append({"name": name, "count": count, "max": 1500, "grade": 0})
        raw_mats.sort(key=lambda x: x["name"])

        for mat in event.get("Manufactured", []):
            name = mat.get("Name", "")
            count = mat.get("Count", 0)
            grade = _MFG_GRADES.get(name, 1)
            mfg_mats.append({"name": name, "count": count, "max": 1500, "grade": grade})
        mfg_mats.sort(key=lambda x: (-x["grade"], x["name"]))

        for mat in event.get("Encoded", []):
            name = mat.get("Name", "")
            count = mat.get("Count", 0)
            grade = _ENC_GRADES.get(name, 1)
            enc_mats.append({"name": name, "count": count, "max": 1500, "grade": grade})
        enc_mats.sort(key=lambda x: (-x["grade"], x["name"]))

        return raw_mats, mfg_mats, enc_mats

    def _on_engineers_loaded(self, data: dict):
        engineers = data.get("engineers", [])

        if not engineers:
            self.eng_status.setText("No engineer data available — check Inara API key")
            self.eng_table.setRowCount(0)
            return

        self.eng_status.setText(f"{len(engineers)} engineers found")
        self.eng_table.setRowCount(len(engineers))

        for i, eng in enumerate(engineers):
            name = eng.get("engineerName", eng.get("name", "?"))
            system = eng.get("engineerSystem", eng.get("system", "?"))
            rank = eng.get("engineerRank", eng.get("rank", 0))
            progress = eng.get("engineerProgress", eng.get("progress", 0))

            name_item = QTableWidgetItem(name)
            if rank >= 5:
                name_item.setForeground(QColor(GREEN))
            self.eng_table.setItem(i, 0, name_item)
            self.eng_table.setItem(i, 1, QTableWidgetItem(system))

            rank_item = QTableWidgetItem(f"{rank}/5")
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_color = GREEN if rank >= 5 else YELLOW if rank >= 3 else WHITE
            rank_item.setForeground(QColor(rank_color))
            self.eng_table.setItem(i, 2, rank_item)

            progress_item = QTableWidgetItem(f"{progress}%")
            progress_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.eng_table.setItem(i, 3, progress_item)


# Manufactured material grades (1-5) — ED does not include grades in the journal
_MFG_GRADES: dict[str, int] = {
    "Shield Emitters": 1,
    "Hybrid Capacitors": 1,
    "Compact Composites": 1,
    "Grid Resistors": 1,
    "Proprietary Composites": 1,
    "Circuit Switchboards": 1,
    "Crystalline Elements": 1,
    "Weaponized Components": 2,
    "Shield Cycle Chargers": 2,
    "Composite Armatures": 2,
    "Mechanical Equipment": 2,
    "Syntax Collators": 2,
    "Heavy Duty Armatures": 2,
    "Filament Composites": 2,
    "Germanium Wire": 2,
    "Gallium Wire": 2,
    "Conductive Components": 2,
    "Military Supercapacitors": 3,
    "High Density Composites": 3,
    "Superconductors": 3,
    "Carbon Fibre Composites": 3,
    "Tungsten Carbide": 3,
    "Molybdenum Plate": 3,
    "Mercury Switch": 3,
    "Volley Triggers": 3,
    "Sector Radiators": 3,
    "Phase Shields": 3,
    "Compound Shielding": 4,
    "Heat Dispersion Plate": 4,
    "Heat Resistant Ceramics": 4,
    "Salvaged Alloys": 4,
    "Guardian Sentinel Blueprints": 4,
    "Imperial Shielding": 4,
    "Military Grade Fabrics": 4,
    "Modified Embedding Circuit": 4,
    "Electrochemical Arrays": 4,
    "Distorted Shield Cycle Records": 4,
    "Modular Terminals": 5,
    "Proto Light Alloys": 5,
    "Proto Radiolic Composites": 5,
    "Military Grade Alloys": 5,
    "Boron Ferrites": 5,
    "Shielding Sensors": 5,
    "Magnetic Emitter Coils": 5,
    "Heat Conduction Wiring": 5,
    "Strange Wake Solutions": 5,
    "Eccentric Hypotheses": 5,
}

# Encoded data grades (1-5) — same reason as above
_ENC_GRADES: dict[str, int] = {
    "Shield Frequency Data": 1,
    "Shield Pattern Analysis": 1,
    "Shield Cyclone Reflections": 1,
    "FSD Telemetry Record": 1,
    "Atmospheric Data": 1,
    "Disrupted Wake Echoes": 1,
    "Electrochemical Reactors": 1,
    "Reaction Process Diagrams": 1,
    "Atmospheric Processors": 1,
    "Cropped Emission Samples": 1,
    "Hybrid Reflectors": 2,
    "Focused Welding Emitters": 2,
    "Ionised Data": 2,
    "Classified Scan Fragments": 2,
    "Aberrant Shield Pattern Analysis": 2,
    "Peculiar Shield Data": 2,
    "Shielding Schemas": 2,
    "Specialised Legacy Firmware": 2,
    "Unexpected Emission Data": 2,
    "Distorted Shield Data": 2,
    "Tactical Data": 3,
    "Encryption Code Fragments": 3,
    "Tagged Scan Data Blocks": 3,
    "Symmetric Keys": 3,
    "Open Symmetric Keys": 3,
    "Imprecise Shield Waveforms": 3,
    "Untypical Shield Scans": 3,
    "Arbitrary Shield Analysis": 3,
    "Degraded Shield Pattern Data": 3,
    "Modified Consumer Firmware": 3,
    "Classified Scan Sector Keys": 4,
    "Inconsistent Shield Soak Data": 4,
    "Volatile Shield Data": 4,
    "Classified Scan Data": 4,
    "Thargoid Wake Data": 4,
    "Guardian Module Codes": 4,
    "Guardian Vehicle Bay Blueprints": 4,
    "Guardian Sentinal Weapon Data": 4,
    "Guardian Technology Cache Data": 4,
    "Guardian Fabrication Data": 4,
    "Adaptive Encryptors Capture": 5,
    "Classified Scan Database": 5,
    "Imprecise Shield Analysis": 5,
    "Peculiar Wake Data": 5,
    "Shield Pattern Analysis Data": 5,
    "Aberrant Shield Pattern Data": 5,
    "Distorted Shield Waveform Data": 5,
    "Guardian Sentinel Site Data": 5,
    "Guardian Basin History": 5,
    "Guardian Pylon Data": 5,
}


# Slot name → human-readable label (hardpoint/internal slots not covered by _ITEM_NAMES)
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

# Item internal name → display name (covers items by their ED internal identifier)
_ITEM_NAMES: dict[str, str] = {
    "shieldgenerator": "Shield Generator",
    "shieldcellbank": "Shield Cell Bank",
    "hullreinforcementpackage": "Hull Reinforcement Package",
    "modulereinforcementpackage": "Module Reinforcement Package",
    "guardianshieldreinforcement": "Guardian Shield Reinforcement",
    "guardianhullreinforcement": "Guardian Hull Reinforcement",
    "guardianmodulereinforcement": "Guardian Module Reinforcement",
    "cargorack": "Cargo Rack",
    "corrosionproofcargorack": "Corrosion Resistant Cargo Rack",
    "refinery": "Refinery",
    "collectorlimpetcontroller": "Collector Limpet Controller",
    "prospectorlimpetcontroller": "Prospector Limpet Controller",
    "hatchbreakerlimpetcontroller": "Hatch Breaker Limpet Controller",
    "seismiccharge": "Seismic Charge Launcher",
    "abrasionblaster": "Abrasion Blaster",
    "subsurfacedisplacementmissile": "Sub-surface Displacement Missile",
    "pulsewaveanalyser": "Pulse Wave Analyser",
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
    "economycabin": "Economy Passenger Cabin",
    "businesscabin": "Business Passenger Cabin",
    "firstclasscabin": "First Class Passenger Cabin",
    "luxurycabin": "Luxury Passenger Cabin",
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
    "pulselaser": "Pulse Laser",
    "burstlaser": "Burst Laser",
    "beamlaser": "Beam Laser",
    "mininglaser": "Mining Laser",
    "multicannon": "Multi-cannon",
    "cannon": "Cannon",
    "fragmentcannon": "Fragment Cannon",
    "railgun": "Rail Gun",
    "missilerack": "Missile Rack",
    "seekermissilerack": "Seeker Missile Rack",
    "torpedopylon": "Torpedo Pylon",
    "minelauncher": "Mine Launcher",
    "plasmaaccelerator": "Plasma Accelerator",
    "axmulticannon": "AX Multi-cannon",
    "axmissilerack": "AX Missile Rack",
    "eaxmulticannon": "Enhanced AX Multi-cannon",
    "eaxmissilerack": "Enhanced AX Missile Rack",
    "gausscannon": "Guardian Gauss Cannon",
    "plasmacharger": "Guardian Plasma Charger",
    "shardcannon": "Guardian Shard Cannon",
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
    "dumbfiremissile": "Dumbfire Missile",
    "axmissile": "AX Missile",
    "advancedtorppylon": "Advanced Torpedo Pylon",
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
