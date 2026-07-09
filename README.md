# SPECTR — Elite Dangerous TUI Companion

Terminal UI for Elite Dangerous commanders. Reads game journals to display commander stats, ship info, location, missions, exobiology samples, and more.

## Requirements

- Python 3.11+
- Elite Dangerous (journal files from Odyssey)

## Quick Start

```bash
./run.sh
```

The launcher creates a virtual environment and installs dependencies automatically on first run.

## Configuration

Settings are stored at `~/.config/spectr/config.json`. Configure via the **Settings** tab in the app:

- **Journal Path** — Location of Elite Dangerous journal files (typically `~/Saved Games/Frontier Developments/Elite Dangerous`)
- **Commander Name** — Your CMDR name
- **Inara API Key** — For Inara integration (optional)
- **EDSM API Key** — For EDSM integration (optional)

## Tabs

| Tab | Description |
|-----|-------------|
| Dashboard | Overview: credits, current system, ship |
| Commander | Commander profile with ranks, progress bars, squadron, powerplay |
| Ship | Ship type, name, module loadout |
| Location | Current star system, body, station |
| Missions | Active mission history |
| Laboratory | Exobiology sample tracking with value prediction |
| Settings | Configuration editor |

### Commander Panel Features

- **Ranks** — Combat, Trade, Explore, CQC, Empire, Federation, Soldier, Exobiologist with rank name labels and colored progress bars (red < 30%, yellow 30–65%, green ≥ 65%)
- **Squadron** — Displayed next to commander name
- **Powerplay** — Power, rank, merits shown in finances
- **Credits / Rebuy / Notoriety** — From journal, optionally enriched via Inara

Data sources: journal `Rank`/`Progress` events (primary), Inara API merged as fallback when configured.

## Run Manually

```bash
python -m spectr
```
