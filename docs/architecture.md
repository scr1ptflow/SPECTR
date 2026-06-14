# Architecture

## Directory Layout

```
SPECTR/
├── core/
│   ├── app.py              — Main entry point, journal monitor, focus enforcement
│   ├── config.py           — Config class, config.json read/write, DEFAULT_CONFIG
│   ├── event_bus.py        — Pub/sub event system with queue and wildcard support
│   ├── game.py             — Game state tracker (system info, body data, body_data_cache)
│   ├── journal.py          — Journal file reading, live monitoring, replay
│   ├── overlay.py          — Root tkinter window, transparency, blur, panel positioning, drag/resize
│   ├── plugin_api.py       — @plugin, @on, @post_load decorators + PluginContext
│   ├── plugin_base.py      — Old-style Plugin base class (legacy, kept for compatibility)
│   ├── plugin_manager.py   — PluginManager class: load/unload/discover plugins, profiles
│   ├── settings_ui.py      — Settings window with sidebar tabs, plugin config, profiles
│   ├── status.py           — Elite Dangerous Status.json flag parser
│   ├── threads.py          — Thread pool submission helper (for API calls)
│   └── window.py           — GameWindow: polls for Elite Dangerous window bounds/focus
│
├── plugins/
│   ├── plugin_manager/     — Settings UI window (old-style Plugin subclass, special case)
│   ├── jump_tracker/       — Route progress, fuel gauge, neutron count, Spansh routes
│   │   └── plugin.py       — Jump Tracker (decorator API, 1.3.0)
│
├── data/                   — Runtime data (materials.json, codex firsts, etc.)
├── docs/
│   ├── architecture.md     — This file
│   └── plugin-development.md  — Plugin API reference
│
├── config.json             — User config (runtime, never committed)
├── main.spec               — PyInstaller build spec
├── AGENTS.md               — Project context for AI coding assistants
└── README.md
```

## Core Components

### Event Bus (`core/event_bus.py`)

The central communication hub. All journal events and status updates flow through it.

- `publish(event, data)` — puts an event on the queue (thread-safe)
- `subscribe(event, callback)` — register a handler for a specific event name
- `unsubscribe(event, callback)` — remove a handler
- `process_queue(max_events=200)` — drain the queue, calling subscribers

Events are named hierarchically: `"journal"` catches all journal events, `"journal:FSDJump"` catches only FSDJump events. The `"status"` event is separate.

### Overlay (`core/overlay.py`)

Manages the transparent tkinter window that sits on top of Elite Dangerous.

- Creates a root window with DWM blur transparency for frosted-glass appearance
- Each plugin gets a `PluginPanel` — a Frame wrapper with drag handles, resize grips, and position management
- Panel positions are managed via a 3×3 grid system, relative anchoring, and stacking
- Focus enforcement hides panels when the game loses focus (alt-tab)
- Resolution scaling adapts UI to non-1080p displays

### Plugin Manager (`core/plugin_manager.py`)

Discovers and manages plugin lifecycle.

- Scans the `plugins/` directory for plugin packages
- Loads plugins via the decorator API (`@plugin`)
- Handles enable/disable toggles
- Applies layout profiles (save/restore panel positions)
- Routes settings tab building

### Journal Monitor (`core/journal.py`)

Reads Elite Dangerous journal files and publishes events.

- `start_async()` — begins polling the journal directory for new files/lines
- `replay_all()` — reads only the **latest** journal file on startup (all plugin state is persisted individually)
- `replay_all_journals(schedule_fn, done_callback)` — reads **all** journal files, chunked via `after()` to avoid UI freeze
- `_resolve_journal_path()` — helper to find the journal directory

### Config (`core/config.py`)

JSON-based configuration with schema validation.

- `DEFAULT_CONFIG` provides defaults for all settings
- Auto-saves on every mutation
- Sections: overlay, api_keys, profiles, per-plugin settings

## Data Flow

```
Elite Dangerous
      │
      ├── Journal.*.log ──→ JournalMonitor ──→ Event Bus ──→ Subscribers (plugins)
      │                                                          │
      └── Status.json ──→ Status parser ──→ Event Bus ───────────┘
                                                                  │
                                                          ┌───────┘
                                                          ▼
                                                    Plugin._update_display()
                                                          │
                                                          ▼
                                                    Overlay panel widgets
```

1. Elite Dangerous writes journal events to `Journal.*.log` and `Status.json` in real-time
2. `JournalMonitor` polls the directory for new lines and publishes them to the `EventBus`
3. Plugins subscribed to matching events receive `(ctx, data)` callbacks
4. Plugins update internal state and call `_update_display()` to refresh overlay widgets
5. The overlay window (with DWM blur) renders the updated text/canvas over the game

On startup:
1. `App.initialize()` creates all components
2. Plugins are loaded via `PluginManager`
3. `replay_all()` reads the latest journal file to seed current state
4. Plugins restore persisted state via `@post_load` handlers
5. Live journal monitoring begins

## Plugin System

See `docs/plugin-development.md` for the full plugin API reference.

Key principles:
- Each plugin is an independent module in `plugins/<name>/plugin.py`
- Decorator API: `@plugin()`, `@on()`, `@post_load` from `core.plugin_api`
- Plugins persist state to `data/` via atomic saves — journal replay is for seeding, not state recovery
- `PluginContext` provides access to theme, config, game state, and overlay helpers
