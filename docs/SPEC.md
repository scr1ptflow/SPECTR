# SPEC.md

# Elite Bridge

**Version:** 0.1

---

# Vision

Elite Bridge is a **ship operating system** for **Elite Dangerous**.

It is **not** another companion app.

It is **not** another dashboard.

It is **not** another journal viewer.

The goal is to make the player feel like they are sitting on the bridge of a real spaceship.

Every screen represents a department aboard the ship.

Every department behaves like an officer reporting to the captain.

The application exists to improve **situational awareness**, not simply expose game data.

---

# Design Philosophy

Traditional Elite Dangerous tools display information.

Elite Bridge **interprets** information.

Instead of presenting tables and statistics immediately, every department produces a concise operational report.

The application answers:

> **Captain, what do you need to know right now?**

Only after this report should detailed information be available.

---

# Core Principles

## 1. Reports Before Data

Every department starts with:

```
Officer Report

↓

Recommendations

↓

Detailed Information

↓

History
```

Raw data is never the landing page.

---

## 2. Departments

Every major system belongs to a department.

Departments are independent.

Each department owns its own responsibilities.

Departments communicate through the backend only.

---

## 3. Immersion

The application should feel like software installed aboard a spaceship.

Avoid:

* spreadsheets
* giant tables
* configuration-heavy interfaces
* Windows-like dialogs

Prefer:

* reports
* status panels
* operational summaries
* console layouts
* readable typography

---

## 4. Situational Awareness

The interface should reduce decision making.

The player should understand the current situation within a few seconds.

---

## 5. Recommendations

Every department should answer:

* What happened?
* Does it matter?
* What should I do next?

Recommendations are one of the application's defining features.

---

# Department Pattern

Every department follows exactly the same structure.

```
Department

↓

Officer Report

↓

Recommendations

↓

Detailed Views

↓

Historical Information
```

This consistency should exist throughout the application.

---

# Officer Reports

Officer reports should resemble professional military or spaceflight briefings.

Good reports are:

* concise
* objective
* actionable
* easy to scan

Reports should avoid unnecessary numbers.

Numbers belong in the detailed views.

Example:

```
Engineering Report

Hull integrity remains excellent.

Frame Shift Drive requires maintenance.

Power reserves are healthy.

Recommendation:

Schedule repairs before beginning another expedition.
```

---

# Status Levels

Every department exposes one operational status.

```
GREEN
Operating normally.

BLUE
Information available.

YELLOW
Attention recommended.

ORANGE
Action should be taken soon.

RED
Immediate action required.
```

The Bridge page aggregates these statuses.

---

# Departments

---

## Bridge

Purpose

Provide the captain with an overview of the entire ship.

Responsibilities

* Summarize every department
* Display ship-wide alerts
* Show current location
* Show current mission
* Display operational status

The Bridge never replaces department pages.

It summarizes them.

---

## Navigation

Purpose

Everything related to stellar navigation.

Responsibilities

* Current system
* System evaluation
* Planetary data
* Stations
* Fleet carriers
* Route information
* Cartographic estimates
* Exploration opportunities

Officer Question

> "Where are we, and what is worth doing here?"

---

## Engineering

Purpose

Monitor the ship.

Responsibilities

* Modules
* Integrity
* Power
* Heat
* Fuel
* Repair suggestions
* Engineering materials

Officer Question

> "Can the ship safely continue?"

---

## Laboratory

Purpose

Scientific analysis.

Responsibilities

* Exobiology
* Samples
* Estimated payouts
* Biological discoveries
* Research progress

Officer Question

> "What scientific opportunities exist?"

---

## Operations

Purpose

Monitor current activities.

Responsibilities

* Missions
* Cargo
* SRV
* Fighters
* Limpets
* Objectives

Officer Question

> "What are we currently doing?"

---

## Tactical

Purpose

Assess danger.

Responsibilities

* Hostile ships
* Interdictions
* Combat
* Crime
* Security
* Threat assessment

Officer Question

> "Are we safe?"

---

## Communications

Purpose

Incoming information.

Responsibilities

* GalNet
* Mission messages
* Powerplay
* News

Officer Question

> "What information requires attention?"

---

## Commander

Purpose

Commander information.

Responsibilities

* Credits
* Reputation
* Rank
* Powerplay
* Statistics

Officer Question

> "What is the commander's current status?"

---

## Archive

Purpose

Historical information.

Responsibilities

* Expeditions
* Previous sessions
* Statistics
* Discoveries
* Flight history

Officer Question

> "What have we accomplished?"

---

## Intelligence

Purpose

Interpret information from every other department.

Responsibilities

* Predictions
* Recommendations
* Efficiency analysis
* Maintenance forecasts
* Risk analysis

Officer Question

> "What should we do next?"

---

# Reports

Every report should attempt to generate:

Current Situation

Important Findings

Recommendations

Operational Status

Example

```
Navigation Report

Current Position

Dryau Ausms KG-Y d756

Findings

12 bodies detected.

2 Earth-like Worlds.

4 landable planets.

Recommendation

Perform Full Spectrum Scan.

Estimated exploration value:

24.8 million credits.

Status

GREEN
```

---

# Detailed Views

Reports are summaries.

Detailed views contain:

* tables
* graphs
* timelines
* module information
* statistics
* historical records

Detailed views should never replace reports.

---

# History

Every department maintains history.

Examples

Navigation

* visited systems
* routes
* expeditions

Engineering

* repairs
* module failures

Laboratory

* discoveries
* biological samples

Operations

* missions

Archive

* sessions

History transforms Elite Bridge into a persistent ship computer rather than a live dashboard.

---

# Alerts

Departments may generate alerts.

Examples

Engineering

```
Frame Shift Drive integrity below 85%.
```

Navigation

```
Unscooped fuel star detected.
```

Laboratory

```
High-value biological species discovered.
```

Operations

```
Mission expires in 20 minutes.
```

Alerts should appear on the Bridge.

---

# Intelligence

The Intelligence department is unique.

It owns no data.

Instead, it analyzes every other department.

Examples

```
Nearest repair station:

41 ly
```

```
Current route contains two neutron stars.
```

```
Estimated expedition value exceeds one billion credits.
```

```
Recommended to return to inhabited space.
```

This department should become increasingly intelligent as Elite Bridge evolves.

---

# User Experience

The application should always feel:

Professional

Minimal

Fast

Immersive

Readable

Useful

The user should never feel overwhelmed.

---

# Long-Term Goal

Elite Bridge should become the operating system players wish Elite Dangerous had built into every ship.

It should replace dozens of disconnected utilities with a single coherent bridge experience.

The application should be equally useful for:

* explorers
* traders
* miners
* combat pilots
* exobiologists
* fleet carrier owners

Every feature added in the future should reinforce the core philosophy:

> **Provide situational awareness through intelligent departmental briefings, allowing the commander to make informed decisions quickly while maintaining the feeling of commanding a living starship.**
