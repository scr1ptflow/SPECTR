# SPECTR — Elite Dangerous Tool Suite

## Project

Python CLI tools for Elite Dangerous, sharing a venv and config.

- **Never push or commit unless the user explicitly asks.**

## Conventions

- **Package:** `spectr-blackbox` v0.1.0
- **Launcher:** `./tools` creates venv, installs deps, dispatches to tools
- **Config:** `config.json` — journal path, optional Inara/EDSM API keys. Generated on first run via interactive prompts in `tools`/`tools.bat`.
- **Python:** >=3.10, dependencies in `pyproject.toml` (`watchdog`, `fastapi`, `uvicorn`, `python-multipart`). Installed via `pip install -e .` in `ensure_deps()`.

## Structure

```
blackbox/
  __init__.py   — package metadata
  __main__.py   — `python -m blackbox`
  cli.py        — argparse CLI: record, summary, log, query
  recorder.py   — watches journal dir, reads new lines incrementally
  store.py      — SQLite layer (events + status tables)
long_range_sensor/
  __init__.py   — package metadata
  __main__.py   — `python -m long_range_sensor`
  cli.py        — argparse CLI: check (exobiology)
  journal.py    — reads current system from latest journal file
  edsm.py       — EDSM API client (system info, sphere search, station lookup)
  checkers.py   — extensible check registry + exobiology checker
missions/
  __init__.py   — package metadata
  __main__.py   — `python -m missions`
  cli.py        — argparse CLI: list missions
  reader.py     — builds mission state from journal events
ship_status/
  __init__.py   — package metadata
  __main__.py   — `python -m ship_status`
  cli.py        — argparse CLI: show hull/shields/modules
  reader.py     — journal/status reading, module name resolution
webui/
  __init__.py
  server.py     — FastAPI server, mounts all sub-apps, suppresses uvicorn access logs
  cockpit/
    server.py   — cockpit routes (system, LRS check)
    static/
      index.html — tabbed sidebar shell (Ship, Missions, LRS, Flight Recorder, Captains Log) with iframes
  blackbox/
    server.py   — blackbox API (stats, log, events, query, event-types, status)
    static/
      index.html — LCARS timeline, day-of-week filters, CSV export
  ship_status/
    server.py   — ship status API
    static/
      index.html — 4-column layout, 1s auto-refresh
  missions/
    server.py   — missions API
    static/
      index.html — mission cards with kill progress, 1s auto-refresh
  captains_log/
    __init__.py
    server.py   — Captain's Log API (narrative event log by day)
    static/
      index.html — day-grouped narrative log with date picker and sidebar
  lrs/
    __init__.py
    server.py   — LRS API (system, check) + standalone scanner page
    static/
      index.html
  system_map/
    server.py   — System Map API (system info, bodies, stations, nearby nav)
    static/
      index.html — SVG orrery view with evenly-spaced orbits, per-body labels, info panel
  navigation/
    __init__.py
    server.py   — Navigation API (reads spansh CSV, returns columns + rows, exo-status endpoint for automatic exobiology tracking)
    static/
      index.html — table view with selectable cells, auto-load from ?path=, server-side CSV cache, 3-state auto ticks (red/yellow/green) from blackbox Scan/SAASignalsFound events, dedicated per-body subtype tick column
```

## Tools (`./tools <tool>`)

| Tool | Entry | Description |
|------|-------|-------------|
| `blackbox` | `blackbox.cli:main` | Flight recorder — record, summary, log, query |
| `config` | `tools` script | Interactive submenu for journal path, Inara/EDSM API keys |
| `lrs` | `long_range_sensor.cli:main` | Long Range Sensor — find nearest services (exobiology, more TBD) |
| `missions` | `missions.cli:main` | Mission monitor — list active, failed, completed |
| `ship` | `ship_status.cli:main` | Ship status — hull, shields, module health |

## lrs check command

- `lrs check` reads current system from latest journal, queries EDSM for nearby stations
- `--radius <LY>` — search radius (default 100, EDSM caps ~100 LY)
- `--checks <name>` — run specific check(s) (default: all)
- `--json` — raw JSON output
- Each check is a registered function in `checkers.py` — add new ones with `@checker(name, desc)`

## Conventions

- Database file path is `args.db` (default `blackbox.db`, resolved relative to project root via `_PROJECT_DIR`).
- Recorder tracks per-file byte position in memory (`_positions` dict), not persisted.
- Event display formatting lives in `blackbox/formatter.py` — shared between CLI and webui. Uses `_resolve_field()` / `_parse_localisation_key()` to handle `$` localization keys.
- Timestamps are offset +1286 years for UGT display. Times are suffixed with ` UGT`.
- Material names use `Name_Localised`; fallback `Name` is run through `_cap()` to capitalize first letter. `MaterialTrade` sub-fields always capped.
- No ORM; raw SQL via `sqlite3`.
- SQLite uses WAL mode.
- Flight Recorder webui shows only current UGT day by default, with day-of-week filters, All button, and CSV export.
- Blackbox API filters to ship-relevant events only (SHIP_EVENTS whitelist in `webui/blackbox/server.py`).
- Captain's Log shows narrative events only (filters `LaunchDrone`, `FSSSignalDiscovered`, `Fileheader`, `ShipLocker`, `CarrierStatistics`). Enriched with session summaries, per-day financial ledger, ship filter, first-discovery badges, and milestone highlights (promotion, carrier buy, Sag A*, Colonia, Founders World). Live mode with 2s polling and auto-scroll.
- Missions reader uses journal `KillTarget` field directly (falls back to name regex).
- Missions progress auto-detected: KillTarget → Kills, PassengerTarget → Passengers, Count → Delivered/Tons Mined.
- Missions reader computes `remaining` seconds from Expiry timestamp, `progress` dict with current/target/type.
- Module health overridden from `Status.json` Modules array (real-time) over stale Loadout values.
- Ship bulkhead type extracted from Item field (supports `armour_*`, `int_bulkheads_*`, `<ship>_armour_grade*`).
- Module rating shown as size+class (e.g. `5D`) extracted from `_size`/`_class`/`_grade` in Item.
- Cargo value uses built-in `_COMMODITY_PRICES` table (~90 items, lowercase keys, case-insensitive lookup).
- Economy read from latest `Location`/`FSDJump` event in journal.
- Ship value = HullValue + ModulesValue from Loadout; credits from Status.json Balance.

## Key files

- `blackbox/cli.py` — CLI record/summary/log/query commands
- `blackbox/formatter.py` — shared fmt_event, fmt_date, fmt_time, fmt_captains_log, _resolve_field
- `blackbox/recorder.py` — `_read_journal()` incremental file reader
- `blackbox/store.py` — `_init_schema()` table definitions
- `long_range_sensor/checkers.py` — check registry + exobiology
- `long_range_sensor/edsm.py` — EDSM API client (urllib, no extra deps)
- `missions/reader.py` — mission state builder from journal events
- `ship_status/reader.py` — journal/status reading, module name/rating resolution, bulkhead type extraction, cargo value, economy, ship finances
- `webui/ship_status/static/index.html` — 4-column LCARS grid: Shield/Hull | Cargo (value+items) | Finances | reserved
- `webui/captains_log/server.py` — Captain's Log API (narrative event log by day, enriched with sessions, ship tracking, financials, milestones)
- `webui/captains_log/static/index.html` — day-grouped narrative log with date picker, ship filter, session headers, financial ledger, first-discovery/milestone badges, live mode
- `webui/system_map/server.py` — System Map API (system info, bodies, stations, nearby nav)
- `webui/system_map/static/index.html` — SVG orrery view with evenly-spaced orbits, per-body labels, info panel
- `webui/navigation/server.py` — Navigation API (CSV cache, route loading, system polling, exobiology status)
- `webui/navigation/static/index.html` — Navigation table with auto 3-state ticks (red/yellow/green) from blackbox DB

## Gotchas

- Inara/EDSM API keys in `config.json` are unused by blackbox; LRS uses EDSM key.
- EDSM sphere-systems caps at ~100 LY (returns empty beyond that).
- `(journal_file, line_number)` UNIQUE constraint in DB prevents duplicates from restarts.
- Material events use `Name_Localised` (falls back to `Name` with `_cap()` first-letter capitalization).
- Ship bulkhead Item varies by ship: `armour_*`, `int_bulkheads_*`, or `<ship>_armour_gradeN` (e.g. `lakonminer_armour_grade1`).
- Cargo value returns None if any item has no known price; unknown items are silently skipped for total calculation.
- Navigation exo-status auto-detection: checks blackbox DB for `Scan` events (body visited) and `SAASignalsFound` events (biological signal count). Bodies with bio signals but no matching genus/species in `BuyOrganicData`/`SellOrganicData` show as partial. Server-side cache at `navigation_cache/route.csv`.
- Navigation exo-status DB path must be project root `blackbox.db` — `webui/navigation/server.py` uses three `os.path.dirname()` to reach it.
- Navigation subtype tick column shows per-body status (same state as the main body tick, not global per-subtype).
