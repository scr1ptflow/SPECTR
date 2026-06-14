SPECTR
Spatial Perception Environmental Command Terminal Readout

SPECTR is a lightweight, plugin-based overlay for Elite Dangerous. It runs on top of the game window, reading journal events in real-time to display live HUD panels — route progress, fuel, scoopable stars, and more.

Built with tkinter and DWM blur transparency, it keeps the game visible behind frosted-glass panels.

📑 Table of Contents
🧩 Architecture
📊 Plugins
⚙️ Settings
🎯 Design Philosophy
⚡ Performance
📦 Status
🛠️ Tech Stack
🔨 Building
⚙️ Configuration
🤖 Vibe Coded
🙏 Acknowledgements
📌 Notes
🧪 Plugin Development

🧩 Architecture

See [docs/architecture.md](docs/architecture.md) for the full directory layout and component breakdown.

```
core/
  app.py              — main entry, journal monitor, focus enforcement
  config.py           — Config class, config.json read/write
  overlay.py          — root tkinter window, transparency, blur, panel positioning
  event_bus.py        — pub/sub event system for journal + status events
  game.py             — game state (system info, body data cache)
  plugin_api.py       — @plugin, @on, @post_load decorators + PluginContext
  plugin_manager.py   — load/unload/discover plugins
  journal.py          — journal file reading, replay (latest file only on startup)
  status.py           — Elite Dangerous status flag parsing
  threads.py          — background thread submission helper

plugins/
  jump_tracker/       — Route progress, fuel gauge, neutron count, custom Spansh routes

data/                 — runtime persistence (stats.json, custom routes)
```

📊 Plugins

| Plugin | Version | Description |
|--------|---------|-------------|
| Jump Tracker | 1.3.0 | Route progress, current/destination system, fuel gauge, neutron star count, scoopable star indicator, progress %. Supports in-game NavRoute and custom Spansh JSON routes with persistent settings tab entry list. |

Jump Tracker features:
- In-game NavRoute (reads `NavRoute.json` directly) and custom Spansh route loading
- Fuel gauge (percentage from Status.json)
- Neutron star count (remaining route)
- Scoopable star indicator with color-coded star class
- Progress percentage, jumps remaining, total route distance
- Persistent jump stats across sessions (atomic saves)
- Custom route path saved and restored on restart
- Dynamic panel width (auto-sizes to content)
- Settings tab with scrollable route list (selectable Entry fields)

⚙️ Settings

Every plugin gets its own Settings tab inside a scrollable sidebar-based window.

- **Plugins tab** — enable/disable, dynamic mode (auto-hide), lock position, 3×3 position picker
- **Profiles** — save/load/switch overlay layout profiles
- **API Keys** — EDSM and Inara API key configuration
- **General** — opacity slider, font selector, font size, auto-hide on unfocus, hide terminal
- **Load All Journals** — manually replay all journal files on demand (startup reads only the latest journal for speed)

🎯 Design Philosophy

Each plugin is self-contained. No single monolithic HUD. Information appears only when relevant. Readability over density.

Goal: enhance awareness without overwhelming the pilot.

⚡ Performance

- Startup only reads the latest journal file (all plugin state persisted individually to disk)
- Full journal replay available on demand via Settings button (chunked via `after()` to avoid UI freeze)
- Event-driven updates (no per-frame polling)
- Lazy panel rendering

📦 Status

Active development. Currently one fully converted decorator-API plugin (Jump Tracker). Other plugins pending migration.

🛠️ Tech Stack

Python 3.14.5 + tkinter (GUI)
PyInstaller 6.20.0 (single-file build: dist/SPECTR.exe)
Plugin architecture (plugins/\<name\>/plugin.py)
Decorator API (@plugin, @on, @post_load)
Event bus (Elite Dangerous journal + status events)
DWM blur (frosted glass panels)
Resolution scaling (1920×1080 baseline)

🔨 Building

```
python -m PyInstaller main.spec --clean
```

Output: `dist/SPECTR.exe`

⚙️ Configuration

Auto-generated on first run as `config.json` (beside the exe or project root). Contains:

- Overlay settings (opacity, colors, font, offsets)
- Plugin enable/disable states
- Layout grid (3×3 positioning system)
- API keys (EDSM / Inara)
- Profile definitions

`config.json` is never committed (contains API keys).

🤖 Vibe Coded

Yes — this project is vibe coded.

It runs on intuition, late-night engineering decisions, and an unhealthy amount of:

"this should probably work"

🙏 Acknowledgements

SPECTR exists thanks to the Elite Dangerous community ecosystem.

Special thanks to:

- **EDDiscovery** — modular journal analysis tool whose plugin architecture influenced SPECTR's design
- **SrvSurvey** — exploration and exobiology workflows that informed scan-related features
- **EDMarketConnector (EDMC)** — journal export tool whose plugin system directly influenced SPECTR's decorator API

📌 Notes
- Designed for Elite Dangerous
- Not affiliated with Frontier Developments
- Use at your own risk during gameplay

🧪 Plugin Development

See [docs/plugin-development.md](docs/plugin-development.md) for:

- Plugin structure and decorator API
- Lifecycle (create, @on, @post_load, build_settings)
- PluginContext attributes and helper methods
- Scaling rules and overlay features
- Example plugins with settings tabs
- Best practices for state persistence and error handling
