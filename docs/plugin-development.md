# Plugin Development Guide

## Structure

```
plugins/
  my_plugin/
    __init__.py
    plugin.py
```

## Decorator API

```python
@plugin(
    name="My Plugin",
    version="1.0.0",
    description="Shows something useful",
    position="top",
    width=300,
    height=100,
    journal_events=["FSDJump", "Location"],
    status_events=True,
    settings_tab="My Plugin",
)
class MyPlugin:

    def create(self, ctx):
        self._lbl = ctx.add_label(text="Hello")

    @on("journal:FSDJump")
    def on_jump(self, ctx, data):
        self._lbl.config(text=data.get("StarSystem", ""))

    def build_settings(self, parent, overlay, config):
        tk.Label(parent, text="Settings here").pack()
```

## Lifecycle

1. **`create(ctx)`** — called once when the plugin is loaded. Build overlay panel widgets via `ctx.add_label()`, `ctx.add_canvas()`, `ctx.add_frame()`. This is where you set up the visual panel that appears over the game.
2. **`@on("journal:EventName")`** — subscribe to specific Elite Dangerous journal events. Handlers receive `(ctx, data)` where `data` is the parsed JSON event. Also supports `@on("status")` for status flag updates.
3. **`@post_load`** — runs after all event subscriptions are set up. Use for state restoration from disk, starting poll loops, or initializing data that depends on the event bus.
4. **`build_settings(parent, overlay, config)`** — populate the Settings tab for this plugin. Called when the user opens the settings window and clicks on the plugin's tab.

## Settings-Only Plugins

A plugin that has `settings_tab` but no `create` method gets no overlay panel — it only appears in the Settings window. Useful for tools like materials inventory or codex trackers that show data in the settings UI rather than as a game overlay.

## PluginContext (ctx)

Plugins receive a `PluginContext` object in every lifecycle method and event handler:

| Attribute | Description |
|-----------|-------------|
| `ctx.event` | Current event name being handled |
| `ctx.font` | Scaled UI font tuple, e.g. `("Consolas", 11)` |
| `ctx.font_small` | Smaller font for secondary text |
| `ctx.bg` | Background color from config |
| `ctx.fg` | Foreground color from config |
| `ctx.accent` | Accent color from config |
| `ctx.config` | Global Config object |
| `ctx.game` | Game state tracker (system info, body data) |
| `ctx.status` | Parsed Status.json flags (GuiFocus, fuel, etc.) |
| `ctx.overlay` | Overlay instance (for scheduling, resizing) |
| `ctx.pcfg` | This plugin's config section dict |
| `ctx.win` | PluginPanel wrapper (tkinter frame with drag/resize) |
| `ctx.parent` | The tkinter container Frame for this plugin's widgets |
| `ctx.scale_factor` | Resolution scale factor relative to 1920×1080 |

## Helper Methods

| Method | Description |
|--------|-------------|
| `ctx.add_label(text, ...)` | Add a text label to the panel |
| `ctx.add_canvas(width, height, ...)` | Add a canvas widget for custom drawing |
| `ctx.add_frame(...)` | Add a container Frame |
| `ctx.set_visible(bool)` | Toggle this plugin's panel visibility |
| `ctx.schedule(ms, callback)` | Schedule a callback after N milliseconds (wraps `tk.after`) |
| `ctx.notify(message, level)` | Show a toast notification (levels: `info`, `success`, `warning`, `error`) |
| `ctx.set_width(pixels)` | Resize the panel width |
| `ctx.resize()` | Re-apply the panel's position/size after a width change |

## Decorator Parameters

The `@plugin()` decorator accepts:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Display name for Settings and tabs |
| `version` | str | required | Plugin version string |
| `description` | str | "" | Short description |
| `position` | str | "top" | Default position in the 3×3 grid |
| `width` | int | 300 | Panel width in pixels |
| `height` | int | 150 | Panel height in pixels |
| `journal_events` | list | [] | Journal events to subscribe to (e.g. `["FSDJump", "Scan"]`) |
| `status_events` | bool | False | Subscribe to status flag updates |
| `dynamic` | bool | False | Auto-hide panel when no relevant content |
| `settings_tab` | str | None | Name of this plugin's Settings tab (None = no settings tab) |
| `relative_to` | str | None | Anchor this panel below/above another plugin by name |
| `relative_pos` | str | "bottom" | `"bottom"` or `"top"` for relative positioning |

## Scaling

Base resolution: **1920×1080**

```
scale_factor = min(screen_w / 1920, screen_h / 1080)
```

All UI elements should use `ctx.scale_factor` or the scaled `ctx.font` tuple to render correctly on non-1080p displays. Font sizes are automatically scaled when accessed via `ctx.font`.

## Overlay Features

- **Drag & Drop** — grab a panel's title bar to reposition it anywhere on screen
- **Resize** — drag the bottom-right corner grip to resize panels
- **Lock** — toggle lock per plugin in Settings to prevent accidental moves/resizes
- **Dynamic mode** — per-plugin auto-hide when no relevant content is showing (combat → hides when not in combat, target info → hides when no target, etc.)
- **Relative Positioning** — use `relative_to="Other Plugin"` and `relative_pos="bottom"` to anchor a panel relative to another
- **Stacking** — panels placed sequentially with 2px gap, non-overlapping (used by Compass, Bio Scanner)
- **Toast notifications** — `ctx.notify("message", "info")` (levels: `info`, `success`, `warning`, `error`)
- **Load All Journals** — Settings button to replay full journal history on demand (panels hidden during replay to prevent visual flicker)

## Example: Minimal Plugin

```python
# plugins/hello/plugin.py
from core.plugin_api import plugin, on, post_load

@plugin(
    name="Hello",
    version="1.0.0",
    description="Displays current system",
    position="top",
    width=300,
    height=60,
    journal_events=["FSDJump", "Location"],
    status_events=True,
)
class HelloPlugin:

    def create(self, ctx):
        self._lbl = ctx.add_label(text="System: —", anchor="w", fg=ctx.accent)

    @on("journal:FSDJump", "journal:Location")
    def on_location(self, ctx, data):
        self._lbl.config(text=f"System: {data.get('StarSystem', '—')}")

    @on("status")
    def on_status(self, ctx, data):
        self._lbl.config(fg=ctx.accent if ctx.status.gui_focus == 0 else "#666666")
```

## Example: Plugin with Settings Tab

```python
# plugins/my_settings_plugin/plugin.py
from core.plugin_api import plugin, on
import tkinter as tk

@plugin(
    name="My Settings Plugin",
    version="1.0.0",
    description="Plugin with settings",
    settings_tab="My Plugin",
)
class MyPlugin:

    def build_settings(self, parent, overlay, config):
        tk.Label(parent, text="Configure me here").pack()
        tk.Button(parent, text="Save", command=lambda: None).pack()
```

## Best Practices

- Persist state to disk via `_save_state()` / `_load_state()` — don't rely on journal replay to reconstruct state (startup only reads the latest journal file)
- Use atomic saves (write to `.tmp` then `os.replace`) for data files
- Guard widget updates in `try/except tk.TclError` blocks so leftover callbacks don't crash after plugin unload
- Call `_update_display()` (or equivalent) only when display data actually changes — avoid rebuilding route/settings widgets on every event
- Use `ctx.schedule()` instead of `tk.after()` directly for proper cleanup
- Settings-only plugins (no `create` method) skip overlay panel creation — set `_settings_only = True` implicitly by omitting `create`
