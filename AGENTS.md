# SPECTR — Elite Dangerous Tool Suite

## Project

Web UI tools for Elite Dangerous, sharing a venv and config. All functionality is exposed via the web server; the launcher offers `web`, `config`, `backup`, and `restore`.

- **Never push or commit unless the user explicitly asks.**

## Session state — next: TBD

Completed: #1 Material & Engineering Dashboard, #2 Carrier Navigator, #3 Notes, #4 Laboratory, #5 Journal Backup/Restore, various fixes (EDSM timeout, notes PUT, carrier event name, ship filter, SQL indexes, batch commits, removed recorder_state.json).
- Colour-coded each tool with a unique LCARS accent (red Flight Recorder, teal Ship Status, orange Missions, mint LRS, yellow Captain's Log, deep blue System Map, purple Navigation, cyan Engineering, lavender Carrier, green Laboratory).
- Laboratory death-reset: filters ScanOrganic/SellOrganicData to only count events after most recent `Died` timestamp.
- Laboratory counts complete sample sets (3 scans = 1 set), hides partial scans.
- Laboratory SellOrganicData: each BioData entry = 1 set (Count field is absent in journal). Body/System names resolved via Scan events and FSDJump/Location SystemAddress mapping.
- Engineering material tabs show `Category (collected/total)` counts.
- Improved Codex key parsing: `$Codex_Ent_Shrubs_03_M_Name` → `Shrubs 03 M`.
- Captain's Log Codex milestone uses `_resolve_field()` so `$` keys render legibly.
- Journal backup tool (`tools_backup.py`): gzip compressed, incremental by mtime+size, manifest-tracked. Integrated into `./tools backup`/`./tools restore`.
- System Map: value tiers (low/medium/high) shown as colored rings around bodies (gray/orange/green), gold ring for valuable exo. Dual legend bars (value tiers + body types). Moon info panel below parent body info, auto-shows first moon. Info panel fields one-per-line.

## Conventions

- **Package:** `spectr-blackbox` v0.1.0
- **Launcher:** `./tools` creates venv, installs deps, dispatches to web or config
- **Config:** `config.json` — journal path, optional Inara/EDSM API keys. Generated on first run via interactive prompts in `tools`/`tools.bat`.
- **Python:** >=3.10, dependencies in `pyproject.toml` (`watchdog`, `fastapi`, `uvicorn`, `python-multipart`). Installed via `pip install -e .` in `ensure_deps()`.

## Structure

```
blackbox/
  __init__.py   — package metadata
  formatter.py  — shared fmt_event, fmt_date, fmt_time, fmt_captains_log, _resolve_field
  recorder.py   — watches journal dir, reads new lines incrementally
  store.py      — SQLite layer (events + status tables)
long_range_sensor/
  __init__.py   — package metadata
  journal.py    — reads current system from latest journal file
  edsm.py       — EDSM API client (system info, sphere search, station lookup)
  checkers.py   — extensible check registry + exobiology checker
missions/
  __init__.py   — package metadata
  reader.py     — builds mission state from journal events
ship_status/
  __init__.py   — package metadata
  reader.py     — journal/status reading, module name resolution
webui/
  __init__.py
  server.py     — FastAPI server, mounts all sub-apps, suppresses uvicorn access logs
  _utils.py     — shared helpers (get_conn, resolve_db, read_config, find_journal_dir, _PROJECT_DIR)
  cockpit/
    server.py   — cockpit routes (system, LRS check)
    static/
      index.html — tabbed sidebar shell (Ship, Missions, LRS, Flight Recorder, Captains Log, Engineering) with iframes
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
      index.html — table view with selectable cells, auto-load from ?path=, server-side CSV cache, 3-state auto ticks (red/yellow/green) from blackbox Scan/SAASignalsFound events, dedicated per-body subtype tick column, route planner panel with From/To/Range/Efficiency inputs
  engineering/
    __init__.py
    server.py   — Engineering API (material inventory aggregation from MaterialCollected/Discarded/Trade events, engineer progress from EngineerProgress events)
    static/
      index.html — material inventory grouped by Raw/Manufactured/Encoded with count thresholds, engineer standings with progress bars
  carrier/
    server.py   — Carrier API (jump history, location, services)
    static/
      index.html — fleet carrier dashboard
  notes/
    server.py   — Notes CRUD API per system
    static/
      index.html — note editor with system lookup
  laboratory/
    server.py   — Laboratory API (unsold exobiology samples, values)
    static/
      index.html — genus-grouped table with summary stats
tools_backup.py — Journal backup/restore CLI (gzip, incremental, manifest-tracked)
```

## Launcher (`./tools`)

| Subcommand | Description |
|------------|-------------|
| `web`      | Start Web UI server (`--port`, `--reload`) |
| `config`   | Interactive submenu for journal path, Inara/EDSM API keys |
| `backup`   | Gzip-compress journals to `backups/journals/` (incremental) |
| `restore`  | Decompress journals from backup back to journal dir |
| *(none)*   | Interactive menu with banner |

## Conventions

- Database file path is `blackbox.db`, resolved relative to project root via `_PROJECT_DIR`.
- Recorder tracks per-file byte position in memory (`_positions` dict), not persisted.
- Event display formatting lives in `blackbox/formatter.py` — shared between CLI and webui. Uses `_resolve_field()` / `_parse_localisation_key()` to handle `$` localization keys.
- Timestamps are offset +1286 years for UGT display. Times are suffixed with ` UGT`.
- Material names use `Name_Localised`; fallback `Name` is run through `_cap()` to capitalize first letter. `MaterialTrade` sub-fields always capped.
- No ORM; raw SQL via `sqlite3`.
- SQLite uses WAL mode.
- Flight Recorder webui shows only current UGT day by default, with day-of-week filters, All button, and CSV export.
- Blackbox API filters to ship-relevant events only (SHIP_EVENTS whitelist in `webui/blackbox/server.py`).
- Captain's Log shows narrative events only (filters `LaunchDrone`, `FSSSignalDiscovered`, `Fileheader`, `ShipLocker`, `CarrierStatistics`). Enriched with session summaries, per-day financial ledger, ship filter, first-discovery badges, and milestone highlights (promotion, carrier buy, Sag A*, Colonia, Founders World). Live mode with 2s polling and auto-scroll. Non-ship vehicles (SLV, SRV, on-foot) are excluded from ship tracking.
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

- `blackbox/exobiology.py` — shared exobiology species→value table (Canonn/Fandom), genus classification, `is_high_value()` helper
- `blackbox/formatter.py` — shared fmt_event, fmt_date, fmt_time, fmt_captains_log, _resolve_field
- `blackbox/recorder.py` — `_read_journal()` incremental file reader
- `blackbox/store.py` — `_init_schema()` table definitions
- `webui/_utils.py` — shared db/config helpers, `_PROJECT_DIR`
- `long_range_sensor/checkers.py` — check registry + exobiology
- `long_range_sensor/edsm.py` — EDSM API client (urllib, no extra deps)
- `missions/reader.py` — mission state builder from journal events
- `ship_status/reader.py` — journal/status reading, module name/rating resolution, bulkhead type extraction, cargo value, economy, ship finances
- `webui/ship_status/static/index.html` — 4-column LCARS grid: Shield/Hull | Cargo (value+items) | Finances | reserved
- `webui/captains_log/server.py` — Captain's Log API (narrative event log by day, enriched with sessions, ship tracking, financials, milestones)
- `webui/captains_log/static/index.html` — day-grouped narrative log with date picker, ship filter, session headers, financial ledger, first-discovery/milestone badges, live mode
- `webui/system_map/server.py` — System Map API (system info, bodies, stations, nearby nav)
- `webui/system_map/static/index.html` — SVG orrery view with evenly-spaced orbits, per-body labels, info panel
- `webui/navigation/server.py` — Navigation API (CSV cache, route loading, system polling, exobiology status, Spansh route planner at POST `/api/route/plan`)
- `webui/navigation/static/index.html` — Navigation table with auto 3-state ticks (red/yellow/green) from blackbox DB, route planner panel with From/To/Range/Efficiency inputs
- `tools_backup.py` — Journal backup/restore (gzip, incremental by mtime+size, manifest.json in backup dir)

## Gotchas

- Inara/EDSM API keys in `config.json` are unused by blackbox; LRS uses EDSM key.
- EDSM sphere-systems caps at ~100 LY (returns empty beyond that).
- `(journal_file, line_number)` UNIQUE constraint in DB prevents duplicates from restarts.
- Material events use `Name_Localised` (falls back to `Name` with `_cap()` first-letter capitalization).
- Ship bulkhead Item varies by ship: `armour_*`, `int_bulkheads_*`, or `<ship>_armour_gradeN` (e.g. `lakonminer_armour_grade1`).
- Cargo value returns None if any item has no known price; unknown items are silently skipped for total calculation.
- Navigation exo-status auto-detection: checks blackbox DB for `Scan` events (body visited) and `SAASignalsFound` events (biological signal count). Bodies with bio signals but no matching genus/species in `BuyOrganicData`/`SellOrganicData` show as partial. Server-side cache at `navigation_cache/route.csv`.
- Navigation exo-status DB path must be project root `blackbox.db` — `webui/navigation/server.py` uses `_PROJECT_DIR` from `webui/_utils.py`.
- Navigation subtype tick column shows per-body status (same state as the main body tick, not global per-subtype).
- `webui/_utils.py:get_conn()` creates a fresh connection per call (no pooling); callers must always `close()`.
