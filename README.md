
# **SPECTR**  
### *Spatial Perception Environmental Command Terminal Readout*

---

SPECTR is a lightweight overlay system designed for **Elite Dangerous**, providing modular real-time informational readouts directly over gameplay.

It is built around a plugin-based architecture, allowing each system to independently render contextual cockpit data without overwhelming the interface.

---

## 🧩 Plugin System Overview

Each plugin operates as an independent module responsible for a specific data domain.

---

### 📊 Core Plugins

| Plugin | Version | Position | Description |
|--------|--------|----------|-------------|
| **Bio Scanner** | 1.0.0 | center-top | Shows species name + 3-pip scan gauge per body from ScanOrganic journal events |
| **Codex Bingo** | 1.0.0 | embedded in Settings tab | Codex exploration tracker with TreeView grouped by region/category, tracks per-commander discoveries via Canonn API |
| **Combat Tracker** | 1.0.0 | bottom-center | Tracks kills, bounty (CR), combat bonds (CR) per session. Auto-hides when not in combat. Persists stats to file |
| **Compass** | 1.0.0 | center-top | 180° surface compass with heading, bearing to target, altitude/lat/lon. Auto-shows near surface |
| **Exobiology Tracker** | 1.0.0 | center-right | Predicts bio life per body using planet data + EDSM. Color-codes known (green) / new (red) from CodexEntry events |
| **Jump Tracker** | 1.0.0 | center-top (configurable) | Next jump destination, route progress bar, star class, distance remaining, neutron/refuel warnings |
| **Materials Tracker** | 1.0.0 | embedded in Settings tab | Tracks Raw/Manufactured/Encoded material counts from journal events. Persists to file |
| **Plugin Manager** | 1.0.0 | standalone Settings window | Tabbed settings: toggle plugins on/off, compass target input, Codex/Materials embedded UIs, API key config, hide-on-unfocus toggle |
| **Target Info** | 1.0.0 | center-left | Dynamic panel: system info + route, and one of ship target (hull/shield/subsystem), FSS signal (threat/time), or body (gravity/temp/atmo/materials) |

---

## 🧠 Design Philosophy

SPECTR is designed to behave like a **layered cockpit intelligence system**:

- Each plugin is self-contained  
- No single monolithic HUD  
- Information appears only when relevant  
- Priority is given to readability over density  

The goal is to enhance awareness without overwhelming the pilot.

---

## ⚡ Performance Overhead

SPECTR is designed to keep performance impact minimal by:

- Updating modules only when relevant events occur  
- Avoiding unnecessary per-frame computations where possible  
- Rendering only visible UI layers  

---

## ⚠️ Status

This project is currently in active development.

Expect:
- ongoing plugin changes  
- experimental systems  
- occasional instability  

---

## 🛠️ Tech Stack

- Python (core implementation)

---

## 🤖 Vibe Coded™

Yes — this project is *vibe coded*.

It runs on intuition, late-night engineering decisions, and an unhealthy amount of:

> “this should probably work”

---

🙏 Acknowledgements

SPECTR would not exist in its current form without the incredible work done by the Elite Dangerous community over the years.

Several systems, ideas, workflows, and interface concepts were inspired by — or directly studied from — existing community tools developed by passionate commanders and developers.

Special thanks to:

**[EDDiscovery](https://github.com/EDDiscovery/EDDiscovery)** — an extremely influential Elite Dangerous companion application featuring journal parsing, exploration tracking, mapping systems, plugin support, and modular information panels. Its architecture, panel philosophy, and ecosystem helped shape many design decisions behind SPECTR.

**[SrvSurvey](https://github.com/njthomson/SrvSurvey)** — a fantastic exploration and exobiology-focused tool whose usability and exploration-oriented workflows served as inspiration for several overlay concepts and quality-of-life systems.

**[EDMarketConnector (EDMC)](https://github.com/EDCD/EDMarketConnector)**
A widely used community tool for exporting Elite Dangerous journal and market data to external services. Its plugin-based architecture and extensibility model directly influenced SPECTR’s plugin system design, particularly the separation of data ingestion, processing, and external integration concerns.

Huge respect and appreciation to the developers and contributors behind these projects for helping push the Elite Dangerous tooling ecosystem forward.

---

## 📌 Notes

- Designed for *Elite Dangerous*  
- Not affiliated with Frontier Developments  
- Use at your own risk during gameplay  

---

## 🔌 Plugin Development Guide

### Structure

```
plugins/
└── my_plugin/            # folder name doesn't matter
    └── plugin.py         # must be named plugin.py
```

### Minimal plugin

```python
from core.plugin_base import Plugin


class MyPlugin(Plugin):
    name = "My Plugin"          # unique — used for config, enable/disable
    version = "1.0.0"
    description = "Shows something useful"

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        self.overlay = overlay
        self.pcfg = config.plugin_config(self.name)   # per-plugin settings

        pos = self.pcfg.get("window_position", "top")
        self.win = overlay.create_plugin_window(
            self.name, position=pos, width=300, height=100,
        )
        parent = self.win.container

        font = (
            config.get("overlay", "font_family", default="Consolas"),
            self.overlay._scaled_font_size,   # auto-scaled for resolution
        )
        bg = config.get("overlay", "bg_color", default="#010101")
        fg = config.get("overlay", "fg_color", default="#e0e0e0")

        self.label = tk.Label(
            parent, text="Hello", font=font, bg=bg, fg=fg, anchor=tk.W,
        )
        self.label.pack(fill=tk.X)

        event_bus.subscribe("journal:MyEvent", self._handler)

    def on_unload(self):
        self.event_bus.unsubscribe("journal:MyEvent", self._handler)

    def on_event(self, event, data):
        self.label.config(text=data.get("SomeField", ""))
        self.overlay.resize_plugin(self.name)

### Key points

| Thing | How |
|---|---|
| **Font size** | Use `self.overlay._scaled_font_size` — scales with resolution |
| **Scaling widgets** | Multiply hardcoded sizes by `self.overlay._scale_factor` (e.g. `round(26 * sf)`) |
| **Dynamic hide** | `self.pcfg.get("dynamic", False)` → show/hide via `win.attributes("-alpha", 1.0/0.0)` |
| **Position** | Read from config: `self.pcfg.get("window_position", "top")` — 3×3 grid |
| **Panel auto-height** | Call `self.overlay.resize_plugin(self.name)` after content changes |
| **Config persist** | `self.pcfg.get(key, default)` / `config.plugin_config(self.name)[key] = val` |
| **Events** | `"status"` for Status.json, `"journal:EventName"` for journal entries |
| **Live reload** | Toggle in Settings; manager calls `on_load` / `on_unload` |

### Scaling

Target resolution is **1920×1080**. On other resolutions `_scale_factor = min(screen_w/1920, screen_h/1080)`. Panel dimensions in `create_plugin_window` scale automatically; internal canvas/pip sizes must be scaled manually (`round(n * sf)`).

---
