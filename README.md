# SPECTR — Elite Dangerous Desktop Companion

PySide6 desktop GUI for Elite Dangerous commanders with a **Star Trek LCARS**-themed interface. Reads game journals to display commander stats, ship info, location, missions, exobiology data, Galnet news, and live server status.

## Quick Start

```bash
./run
```

Creates a virtual environment, installs PySide6, and launches the app. Double-click `SPECTR.desktop` from the file manager for an app-like experience (no terminal).

## Features

| Tab | What it shows |
|-----|---------------|
| **NEWS** | Galnet articles with day-selector buttons (last 5 days), community goals |
| **COMMANDER** | Ranks with progress bars, powerplay, credits, rebuy, notoriety |
| **SHIP** | Ship type/name, shield/fuel/hull health bars, full module loadout |
| **LOCATION** | Current star system, body, and station |
| **MISSIONS** | Recent mission history |
| **LABORATORY** | Exobiology sample tracking with value prediction per species |
| **SETTINGS** | Journal path, commander name, Inara/EDSM API keys |

### LCARS Interface
- Custom-painted side tab navigation with per-tab accent colours
- Data frames with coloured left accent rails
- Colour-thresholded health bars (green ≥ 65%, yellow ≥ 30%, red < 30%)
- Status bar with live server status indicator (ONLINE/OFFLINE/MAINTENANCE)
- Game time (UTC +1286 years = Elite Dangerous timeline) / local system clock — click to toggle
- All widgets painted via `QPainter` — no images, pure vector LCARS styling

### Live Server Status
Async checks every 3 minutes against `auth.frontierstore.net` and `elite.frontier.co.uk`. Status colour-coded in the top bar.

## Configuration

Settings are stored at `~/.config/spectr/config.json` or configure via the **SETTINGS** tab:

- **Journal Path** — `~/Saved Games/Frontier Developments/Elite Dangerous`
- **Commander Name** — Your CMDR name
- **Inara API Key** — Optional, enables rank fallback data

## Requirements

- Python 3.11+
- PySide6 (auto-installed by the launcher)
- Elite Dangerous (journal files from Odyssey)

## Manual Launch

```bash
python -m spectr
```
