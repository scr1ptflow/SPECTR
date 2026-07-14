# SPECTR — Elite Dangerous Desktop Companion

PySide6 desktop GUI for Elite Dangerous commanders with a **FUI (Futuristic User Interface)**-themed interface. Reads game journals to display commander stats, ship info, location, missions, exobiology data, Galnet news, and live server status.

## Quick Start

```bash
./run
```

Creates a virtual environment, installs PySide6, and launches the app. Double-click `SPECTR.desktop` from the file manager for an app-like experience (no terminal).

## Features

| Tab | What it shows |
|-----|---------------|
| **NEWS** | Galnet articles with day-selector buttons (last 5 days), community goals |
| **COMMANDER** | Ranks with progress bars, powerplay, credits, rebuy, notoriety. Inara API fallback for rank data |
| **SHIP** | Ship type/name, shield/fuel/hull health bars, scrollable module grids (left: CORE/HARDPOINTS/UTILITY, right: OPTIONAL) with engineering grades and MFD-style status, cockpit annunciator warning lights |
| **LOCATION** | Current star system, body, station, faction, government, economy, security, population, system map with zoom/pan and body visibility toggles |
| **SCANNER** | Long Range Scanner — find nearby stations and fleet carriers via EDSM, with landing pad filtering |
| **MISSIONS** | Active missions vs completed/failed/abandoned outcomes in separate tables |
| **ENGINEERING** | Materials inventory (Raw/Manufactured/Encoded) with grades; engineer ranks from Inara API |
| **LOG** | Event log from journal — travel, combat, trade, exploration, ship events with filters |
| **LABORATORY** | Exobiology sample tracking with predicted CR value per species (86 species database) |
| **SETTINGS** | Journal path, commander name, Inara/EDSM API keys, journal validation |

### FUI Interface
- Custom-painted side tab navigation with per-tab accent colours (CYAN/ORANGE/BLUE/PURPLE/TEAL/YELLOW/RED/PINK/GREEN/GRAY)
- Data frames with coloured left accent rails
- Colour-thresholded 10-segment health bars (green >= 80%, yellow 20-80%, red < 20%)
- Cockpit-style annunciator warning lights (2-column grid, glow amber/red when active)
- Status bar with live server status indicator (ONLINE/OFFLINE/MAINTENANCE)
- Game time (UTC +1286 years = Elite Dangerous timeline) / local system clock — click to toggle
- All widgets painted via `QPainter` — no images, pure vector FUI styling
- Window size and position persisted between sessions

### Async Networking
Network fetches (Galnet, Long Range Scanner, Engineers) run in background `QThread` workers — the UI stays responsive during network requests.

### Live Server Status
Async checks every 3 minutes against `auth.frontierstore.net` and `elite.frontier.co.uk`. Status colour-coded in the top bar.

## Configuration

Settings are stored at `~/.config/spectr/config.json` or configure via the **SETTINGS** tab:

- **Journal Path** — `~/Saved Games/Frontier Developments/Elite Dangerous`
- **Commander Name** — Your CMDR name
- **Inara API Key** — Optional, enables rank fallback data
- **EDSM API Key** — Reserved for future integration

The settings panel validates your journal path on save and warns if no journal files are found.

## Requirements

- Python 3.11+
- PySide6 (auto-installed by the launcher)
- Elite Dangerous (journal files from Odyssey)

## Manual Launch

```bash
python -m spectr
```
