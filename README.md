
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

EDDiscovery — an extremely influential Elite Dangerous companion application featuring journal parsing, exploration tracking, mapping systems, plugin support, and modular information panels. Its architecture, panel philosophy, and ecosystem helped shape many design decisions behind SPECTR.
SrvSurvey — a fantastic exploration and exobiology-focused tool whose usability and exploration-oriented workflows served as inspiration for several overlay concepts and quality-of-life systems.

Huge respect and appreciation to the developers and contributors behind these projects for helping push the Elite Dangerous tooling ecosystem forward.

---

## 📌 Notes

- Designed for *Elite Dangerous*  
- Not affiliated with Frontier Developments  
- Use at your own risk during gameplay  

---
