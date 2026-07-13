# SPECTR — Agent Guide

## Project Structure
- `run` — Bash launcher, sets up .venv, installs PySide6, generates SPECTR.desktop
- `main.py` — Entry point for `python main.py`
- `spectr/__main__.py` — Entry point for `python -m spectr`
- `spectr/app.py` — QApplication setup, `main()` with logging config and KeyboardInterrupt handler
- `spectr/config.py` — JSON config at `~/.config/spectr/config.json`, with `validate_config()` and `load_config()`/`save_config()`
- `spectr/journal.py` — JournalReader: parses Elite journal files for ranks/progress, exobiology, powerplay, ship, location. File list is cached per directory.
- `spectr/inara.py` — InaraClient: fetches commander profile from Inara API (`/inapi/v1/`), used as rank fallback in CommanderPanel
- `spectr/galnet.py` — GalnetFetcher: scrapes community.elitedangerous.com for news articles
- `spectr/server_status.py` — ServerStatusChecker: async QNetworkAccessManager probes to Frontier auth/game servers
- `spectr/edsm.py` — EDSMClient: fetches nearby systems and stations from EDSM API, ship landing pad size mapping, pad compatibility checks
- `spectr/data/species.py` — Exobiology species database (86 species across 14 genera), `base_value()` / `lookup()` / `total_value()` API
- `spectr/data/icon.svg` — FUI-style app icon
- `spectr/ui/main_window.py` — MainWindow (QMainWindow) with FUITab sidebar + QStackedWidget, tab registry, server status integration, window state persistence via QSettings
- `spectr/ui/panels.py` — 10 PanelBase subclasses + 3 QThread workers. Network fetches (Galnet, Scanner, Engineers) use QThread subclasses with signals to keep UI responsive. Shared `_table_style()` helper for consistent table styling.
- `spectr/ui/widgets.py` — All FUI custom widgets: FUIBar, FUIPanel, FUITab, FUIButton, FUIProgressBar, FUIContinuousBar, FUIStatusBar. Backward-compatible aliases (LcarsBlock, LcarsTab, etc.)

## Conventions
- Panel classes extend `PanelBase(QWidget)`, placed in `panels.py`
- Each panel is registered in `TAB_PANELS` dict (class) and `TAB_ITEMS` list (id, label, colour) in `main_window.py`
- Panels access shared state via `self.window.journal` / `self.window.config`
- Panels define `refresh()` called each time the tab becomes visible
- All UI code uses PySide6 (Qt for Python)
- Network fetches (Galnet, Community Goals) use `QThread` subclasses with signals to keep UI responsive
- FUI colour palette in `widgets.py`: CYAN, ORANGE, BLUE, PURPLE, TEAL, YELLOW, RED, PINK, GRAY, WHITE, DARK/DARK2/DARK3
- Names: snake_case for methods/vars, PascalCase for classes
- `from __future__ import annotations` at top of every .py file
- All modules use `logging.getLogger(__name__)` for diagnostics

## Key Data Flow
- **Ranks & Progress** — Journal `Rank` / `Progress` events; Inara API merged as fallback when journal data is empty
- **Credits** — Journal `LoadGame.Credits`
- **Squadron** — Journal `LoadGame.SquadronName`
- **Powerplay** — Journal `Powerplay` / `PowerplayJoin` / `PowerplayDefect` events
- **Server Status** — `ServerStatusChecker` fires async HEAD to `auth.frontierstore.net` + `elite.frontier.co.uk`; emits ONLINE/OFFLINE/MAINTENANCE/UNKNOWN
- **Galnet** — `GalnetFetcher.get_articles("/galnet")` scrapes HTML in a `_GalnetWorker` QThread; articles cached in memory; day buttons filter client-side
- **Community Goals** — Filtered client-side from Galnet articles using keyword matching (no separate network fetch)
- **Exobiology** — `JournalReader.get_organic_summary()` single-pass aggregates ScanOrganic + SellOrganicData across all journal files
- **Missions** — Active missions (MissionAccepted minus completed/failed/abandoned) and completed/failed/abandoned outcomes shown separately
- **Location** — System, body, body type, distance from star, station, faction, government, economy, security, population
- **Ship** — Module data includes engineering grade/experimental display; Status.json read cross-platform
- **InaraClient** — Uses `header` block with `appName`/`appVersion`/`APIkey`/`commanderName`, events with `eventName`/`eventTimestamp`/`eventData`. Endpoint: `https://inara.cz/inapi/v1/`
- **EDSMClient** — Uses EDSM REST API for nearby systems and stations; ship landing pad size mapping (S/M/L); pad compatibility checks

## FUI Widget Architecture
- `FUIBar` — Thin horizontal strip, used as accent line
- `FUIPanel` (alias `LcarsBlock`) — Data frame with coloured left accent rail + optional title
- `FUITab` (alias `LcarsTab`) — Sidebar nav pill; active fills with accent colour, inactive shows rail only
- `FUIButton` (alias `LcarsPill`) — Fully rounded action button
- `FUIProgressBar` (alias `HealthBar`) — 10-segment progress bar, green >= 8th, yellow 2nd-7th, red < 2nd
- `FUIContinuousBar` — Single continuous bar with red/yellow/green position-based coloring
- `FUIStatusBar` (alias `LcarsStatusBar`) — Top bar: server status left, toggleable game/system clock right

## Sidebar / Tab System
- Sidebar uses FUITab buttons (not QListWidget), manually toggled via `_switch_tab()`
- `_switch_tab(tab_id)` updates button states, stack widget, status bar accent colour, and calls `panel.refresh()`
- Status bar accent follows active tab colour from `_TAB_COLORS` dict

## Tab Registry
| ID | Label | Accent | Panel Class |
|---|---|---|---|
| `dashboard` | NEWS | CYAN | DashboardPanel |
| `commander` | COMMANDER | ORANGE | CommanderPanel |
| `ship` | SHIP | BLUE | ShipPanel |
| `location` | LOCATION | PURPLE | LocationPanel |
| `scanner` | SCANNER | CYAN | ScannerPanel |
| `missions` | MISSIONS | TEAL | MissionsPanel |
| `engineering` | ENGINEERING | GREEN | EngineeringPanel |
| `captainslog` | LOG | PINK | CaptainsLogPanel |
| `laboratory` | LABORATORY | YELLOW | LaboratoryPanel |
| `settings` | SETTINGS | GRAY | SettingsPanel |

## Config Keys
| Key | Default | Notes |
|---|---|---|
| `journal_path` | `""` | Path to ED journal directory |
| `inara_api_key` | `""` | Used for rank fallback |
| `inara_app_name` | `"SPECTR"` | Sent to Inara API |
| `edsm_api_key` | `""` | Reserved for future EDSM integration |
| `edsm_app_name` | `"SPECTR"` | Reserved for future EDSM integration |
| `commander_name` | `""` | Fallback if journal lacks it; used for Inara lookups |

## Panel Details
- **DashboardPanel** — `_GalnetWorker` QThread fetches articles; date buttons filter client-side; CGs filtered from same article set and shown in yellow block
- **CommanderPanel** — 4x2 rank grid with `HealthBar`s, powerplay block (pink), finances block (teal); Inara fallback when journal ranks empty
- **ShipPanel** — Ship identity, 3 stat boxes (shield/fuel/hull), 2-column module grid with engineering info; Status.json for live fuel/shields
- **LocationPanel** — System, body, body type, distance from star, station, faction, government, economy, security, population
- **ScannerPanel** — Long Range Scanner: EDSM API finds nearby stations/carriers with landing pad filtering; radius 25/50/100 LY; ship pad size auto-detected; manual SCAN trigger (no auto-scan on tab switch)
- **MissionsPanel** — Active table (accepted minus completed/failed/abandoned) + completed/failed table with colored outcome
- **CaptainsLogPanel** — Star Trek-style event log from journal; filters by travel/combat/trade/exploration/ship; timestamps + descriptions
- **EngineeringPanel** — Materials inventory separated by type (Raw/Manufactured/Encoded) with grade display; engineers from Inara API with rank/progress
- **LaboratoryPanel** — Summary stats + detail table of pending organic data with predicted values
- **SettingsPanel** — 6 config fields, validation on save, status feedback
