# SPECTR — Elite Dangerous Tool Suite

```
./tools                     interactive menu
./tools blackbox <command>  run blackbox directly
./tools config              edit journal path, Inara/EDSM API keys
./tools lrs <command>       run lrs directly
./tools web [--port 8000]   start Web UI server
./tools ship                show ship hull, shields, module health
./tools missions            list active/failed/complete missions
```

## Web UI

```
./tools web                 # defaults to 0.0.0.0:8000
./tools web --port 8080     # custom port
./tools web --reload        # auto-reload on changes
```

Runs a single server with a tabbed sidebar shell at `/cockpit/` and mounted sub-applications:

| Mount | App | Description |
|-------|-----|-------------|
| `/cockpit/` | cockpit | Tabbed dashboard shell — sidebar with iframes for each tool |
| `/blackbox/` | blackbox | Flight Recorder — LCARS timeline, ship-relevant events only, day-of-week filters, CSV export |
| `/ship/` | ship_status | Hull, shields, modules, cargo manifest |
| `/missions/` | missions | Active/failed/complete missions with kill progress |
| `/lrs/` | lrs | Long Range Scanner — standalone scan page |
| `/captains-log/` | captains_log | Day-grouped narrative event log with date picker and sidebar |
| `/system-map/` | system_map | SVG orrery view with evenly-spaced orbits, per-body labels, info panel |
| `/navigation/` | navigation | Route table with auto 3-state exobiology ticks from blackbox DB |

Swagger API docs at `/cockpit/docs`, `/blackbox/docs`, `/lrs/docs`, and `/captains-log/docs`.

The cockpit sidebar includes tabs for **Ship**, **Missions**, **LRS**, **Flight Recorder**, **Captains Log**, **System Map**, and **Navigation**.

## blackbox — Flight Recorder

Watches journal files and records events to a SQLite database.

| Command | Description |
|---------|-------------|
| `record` | Live-record events (`--once` for one-shot) |
| `summary` | Event counts and stats from DB |
| `log` | Formatted captain's log timeline |
| `query` | Run raw SQL against DB |

Config: `config.json` — generated automatically on first run (or copy `config.example.json`).

On first launch, `./tools` (or `tools.bat` on Windows) prompts for:
- **Journal path** (required) — your Elite Dangerous journal directory
- **Inara API key** (optional) — press Enter to skip
- **EDSM API key** (optional) — press Enter to skip

Creates `config.json` with the provided values.

## ship — Ship Status

Displays hull integrity, shield strength, module health, cargo manifest, and financial info.

```
./tools ship [--journal-dir <path>]
```

- Bars and percentages for hull and shields (shield from `Status.json` if available, otherwise shield generator module integrity)
- Modules grouped by category: hardpoints, utility mounts, core internal, optional internal
  - Module health overridden from real-time `Status.json` Modules array (not stale Loadout values)
  - Module rating shown in parentheses (e.g. `5D`, `3A`, `1E`)
  - Bulkhead type extracted from Item field (e.g. `Lightweight Mk II`, `Military Grade`, `1E`)
- Financial summary: ship value (HullValue + ModulesValue), insurance rebuy, wallet balance, cargo estimated value
- Current system economy from latest journal event
- Cargo value estimated from built-in price table (~90 commodities)
- Cargo manifest with per-item value and totals (reads `Cargo.json` in journal directory)

### Web UI (`/ship/`)

Four-column LCARS grid updated every 500ms:

| Column 1 | Column 2 | Column 3 | Column 4 |
|----------|----------|----------|----------|
| Shield % | Cargo (value, items) | Credits / Ship Value / Rebuy | *(reserved)* |
| Hull %   | (scrollable)        |                         | |

## lrs — Long Range Sensor

Finds nearby stations with services (exobiology, more coming).

```
./tools lrs check [--radius 100] [--ship-size L] [--checks exobiology] [--json]
```

- Reads your current system from the latest journal file
- Queries EDSM for nearby stations
- `--ship-size S|M|L` — filters by landing pad size (default: L)
- Default radius: 100 LY (EDSM max ~100 LY)
- Add new checks in `long_range_sensor/checkers.py` with `@checker(name, desc)`

## missions — Mission Monitor

Tracks active, failed, and completed missions from journal events.

```
./tools missions [--journal-dir <path>] [--json]
```

- Reads last `Missions` snapshot event and applies subsequent `MissionAccepted`/`Completed`/`Failed`/`Abandoned`/`Redirected` events
- Auto-detects progress type: KillTarget → Kills, PassengerTarget → Passengers, Count → Delivered/Tons Mined
- Shows progress bar with current/target for kills, passengers, deliveries, and mining missions
- Shows destination system/station, human-readable time until expiry, and credit reward
- Both CLI and Web UI display progress and time remaining

## captains-log — Captain's Log

A narrative log enriched with session summaries, ship tracking, financials, and milestones.

```
Web UI at /captains-log/
```

- Uses `fmt_captains_log()` for human-readable sentences ("Jumped to Sol", "Picked up 3x Zinc", "Docked at Jameson Memorial")
- **Session summaries** — events grouped into game sessions (bounded by `LoadGame`). Each session header shows ship, jumps, bounties, missions, credits earned/spent
- **Ship filter** — dropdown to view events for a specific ship only
- **Per-day financial ledger** — income, expenses, and net credits at the bottom of each day
- **First-discovery badges** — gold "★ First Discovery" badges on organic/exploration data sold with a bonus
- **Milestone highlights** — special badges for promotions, carrier purchase, ship destruction, Sag A*/Colonia/Founders World visits
- **Live mode** — toggle to show today's events with 2s auto-refresh and auto-scroll
- Left sidebar with available days, date picker, Today and All buttons
- Filters out operational noise: `LaunchDrone` (limpet spam), `FSSSignalDiscovered` (passive sensor data), `Fileheader`, `ShipLocker`, `CarrierStatistics`. These remain in the Blackbox timeline for reference.

## navigation — Route Tracker

Automatically tracks exobiology sampling progress per body from journal data.

```
Web UI at /navigation/
```

- Upload a Spansh CSV route or load from server cache (`navigation_cache/route.csv`)
- Each row gets a 3-state tick indicator:
  - **Red** — body not yet scanned
  - **Yellow** — scanned, biological signals detected (partial)
  - **Green** — scanned, no biological signals (complete)
- Ticks are automatic — reads `Scan`, `SAASignalsFound`, `BuyOrganicData`, and `SellOrganicData` events from the blackbox DB
- Progress bar shows complete / partial / pending counts
- Polls every 30s for updated status
- Server-side CSV cache survives browser storage clears

## config — Configuration

```
./tools config
```

Interactive submenu to set or update:
1. **Journal path** — your Elite Dangerous journal directory
2. **Inara API key** (optional)
3. **EDSM API key** (optional)

Also accessible via `c` in the interactive menu.
