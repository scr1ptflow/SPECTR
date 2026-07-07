# SPECTR — Elite Dangerous Tool Suite

```
./tools              interactive menu (banner)
./tools web          start Web UI server (--port, --reload)
./tools config       edit journal path, Inara/EDSM API keys
./tools backup       gzip-compress journals to backups/journals/ (incremental)
./tools restore      decompress journals from backup back to journal dir
```

## Web UI

```
./tools web                 # defaults to 0.0.0.0:8000
./tools web --port 8080     # custom port
./tools web --reload        # auto-reload on changes
```

Single server with a tabbed cockpit sidebar at `/cockpit/`:

| Mount | App | Description |
|-------|-----|-------------|
| `/cockpit/` | cockpit | Tabbed dashboard shell — sidebar with iframes |
| `/blackbox/` | blackbox | Flight Recorder — LCARS timeline, ship-relevant events, day filters, CSV export |
| `/ship/` | ship_status | Hull, shields, modules, cargo manifest |
| `/missions/` | missions | Active/failed/complete missions with progress bars |
| `/lrs/` | lrs | Long Range Scanner — standalone scan page |
| `/captains-log/` | captains_log | Narrative event log with sessions, financials, milestones |
| `/system-map/` | system_map | SVG orrery view with evenly-spaced orbits, info panel |
| `/navigation/` | navigation | Route table with auto 3-state exobiology ticks |
| `/engineering/` | engineering | Material inventory (Raw/Manufactured/Encoded) with collected/total counts, engineer standings |
| `/carrier/` | carrier | Fleet carrier jump history, location, services |
| `/notes/` | notes | Per-system note editor with lookup |
| `/laboratory/` | laboratory | Exobiology samples — counts complete sets (3 scans = 1 sample), death-reset tracking |

Swagger docs at each sub-app's `/docs` path.

## First Launch

On first run, `./tools` (or `tools.bat`) prompts for:
- **Journal path** (required) — your Elite Dangerous journal directory
- **Inara API key** (optional)
- **EDSM API key** (optional)

Creates `config.json`. The recorder starts automatically when the web server starts.

## Web App Details

### cockpit (`/cockpit/`)
Tabbed sidebar: Ship, Missions, LRS, Flight Recorder, Captains Log, System Map, Navigation.

### blackbox — Flight Recorder (`/blackbox/`)
Watches journal files incrementally, records events to SQLite. Web UI shows an LCARS timeline with day-of-week filters, All button, and CSV export.

### ship — Ship Status (`/ship/`)
Four-column LCARS grid updated every 500ms: Shield/Hull, Cargo (value + items), Credits/Ship Value/Rebuy. Module health overridden from real-time `Status.json`. Cargo value from built-in price table (~90 commodities).

### missions — Mission Monitor (`/missions/`)
Cards with auto-detected progress (Kills, Passengers, Delivered, Tons Mined). 1s auto-refresh.

### lrs — Long Range Sensor (`/lrs/`)
Reads current system from journal, queries EDSM for nearby stations with services. Checks extensible in `long_range_sensor/checkers.py`.

### captains-log — Captain's Log (`/captains-log/`)
Day-grouped narrative log using `fmt_captains_log()` for human-readable sentences. Session summaries per `LoadGame` boundary. Per-day financial ledger. Ship filter. First-discovery and milestone badges. Live mode with 2s polling and auto-scroll. Non-ship vehicles (SLV, SRV, on-foot) excluded from ship tracking.

### system-map — System Map (`/system-map/`)
SVG orrery view with evenly-spaced orbits, per-body labels (color-coded by subtype), info panel on click. Value tiers (low/medium/high) shown as colored rings around bodies (gray/orange/green), gold ring for valuable exobiology. Dual legend bars at bottom. Moon info panel below parent body info, auto-shows first moon. Auto-refresh on FSD jump.

### navigation — Route Tracker (`/navigation/`)
Upload a Spansh CSV route or load from server cache. 3-state auto-tick per body: red (unscanned), yellow (bio signals detected, partial), green (complete). Reads `Scan`, `SAASignalsFound`, `BuyOrganicData`, `SellOrganicData` from blackbox DB. 30s polling. Spansh route planner with From/To/Range/Efficiency inputs.

### carrier — Fleet Carrier (`/carrier/`)
Dashboard showing carrier location, jump history, services, and finance data from journal events.

### notes — System Notes (`/notes/`)
Per-system note editor with system lookup, tag support, and CRUD via API.

### engineering — Materials & Engineers (`/engineering/`)
Material inventory grouped by Raw/Manufactured/Encoded with sectioned layout by grade. Category tabs show collected vs total unique types (e.g. `Raw (20/28)`). Threshold-based count coloring (low/med/high). Engineer standings with rank, stage, and progress bars.

### laboratory — Exobiology Samples (`/laboratory/`)
Unsold organic sample inventory. Groups by genus, counts only complete sets (3 scans = 1 sellable sample). Each SellOrganicData BioData entry counts as 1 set. Death-reset: filters scans/sales to only count events after the most recent `Died` event. Body and system names resolved from journal events.

## config (`./tools config`)

Interactive submenu to set/update journal path, Inara API key, EDSM API key. Also accessible via `c` in the interactive menu.

## Backup/Restore (`./tools backup` / `./tools restore`)

Compresses all `Journal.*.log` files from the journal directory into `backups/journals/` using gzip. Only re-compresses files whose modification time or size changed (incremental via `manifest.json`). Restore decompresses them back to the original journal directory — useful before reinstalling the game.

```
./tools backup               # incremental gzip backup
./tools restore              # restore all files from backup
python3 tools_backup.py list     # list backed-up files with compression ratio
```

## Background

Elite Dangerous journals events are stored in an SQLite DB (`blackbox.db`). The recorder runs as a background thread in the web server, watching for new journal files and appending events. UGT display uses a +1286 year offset.
