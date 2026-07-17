# AGENTS.md

## Project

**SPECTR** (Elite Bridge) — a ship operating system for Elite Dangerous. Reads the game's journal files, interprets state, and presents it as departmental officer reports.

## Architecture

```
Elite Dangerous → JournalWatcher → EventBus → StateEngine → Services → REST API + WebSocket → Vue Frontend
```

- **Backend (Core)** — owns all game logic. Python, async.
- **Frontend (Console)** — only renders data. Vue 3 + TypeScript.
- Communication: REST API (`/api/v1/*`) + WebSocket (`/ws`).
- 9 departments, each producing a `DepartmentReport` (Officer Report → Recommendations → Details → History).

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+, Starlette, aiosqlite, watchfiles, uvicorn |
| Frontend | Vue 3 (Composition API, `<script setup>`), TypeScript, Pinia, Vue Router, Vite |
| Build | hatchling (Python), Vite (frontend) |
| Lint | ruff (backend), vue-tsc (frontend) |
| Test | pytest + pytest-asyncio |

## Commands

```bash
# Backend
cd backend
.venv/bin/python -m pytest tests/backend/ -v    # run tests
.venv/bin/ruff check backend/                    # lint
.venv/bin/ruff check backend/ --fix             # auto-fix

# Frontend
cd frontend
npx vue-tsc --noEmit                             # typecheck
npx vite build                                   # build (outputs to backend/bridge_core/static/)
npx vite                                         # dev server (proxies API to :8420)
```

## Directory Structure

```
SPECTR/
├── backend/
│   ├── pyproject.toml
│   └── bridge_core/
│       ├── main.py              # Entry point
│       ├── api/server.py        # Starlette app, REST routes, WebSocket
│       ├── state/engine.py      # GameState, StateEngine, event handlers
│       ├── events/bus.py        # EventBus (async pub/sub)
│       ├── journal/             # Parser + file watcher
│       ├── services/            # Department services (one per department)
│       ├── calculations/        # Exploration values, risk, travel stats
│       ├── database/            # SQLite (aiosqlite)
│       ├── plugins/             # Plugin system (BasePlugin + manager)
│       └── config/              # Settings (~/.config/elite-bridge/config.json)
├── frontend/
│   ├── package.json
│   └── src/
│       ├── layouts/MainLayout.vue   # 3-column grid (left rail | content | right rail)
│       ├── components/              # Reusable: ButtonRail, OfficerReport, StatisticCard, etc.
│       ├── pages/                   # One per department + SettingsPage
│       ├── stores/                  # Pinia stores (one per data source)
│       ├── api/                     # ApiClient + TypeScript interfaces
│       ├── router/index.ts          # 10 routes nested under MainLayout
│       └── styles/main.css          # CSS variables, ED orange theme
├── docs/
│   ├── SPEC.md          # Product specification (source of truth)
│   ├── TASKS.md         # Development roadmap
│   ├── DOMAIN.md        # Domain model rules
│   └── domain/*.yaml    # Entity definitions (canonical)
├── plugins/             # Runtime plugins (e.g. news/)
├── tests/backend/       # pytest tests
├── scripts/             # install.sh, start.sh
└── prompt               # AI coding context
```

## Layout

3-column touch-friendly grid:
- **Left rail** (140px): Bridge, Navigation, Ship, Engineering, Commander
- **Center**: Header ("SPECTR") + scrollable content
- **Right rail** (140px): Missions, Exploration, Intelligence, Archive, Settings
- **Bottom**: Status bar (system, ship, credits, timestamp)

## Settings

The Settings page (`/settings`) configures:
- **Journal Path** — path to Elite Dangerous journal directory (contains `Journal.*.log` files)
- **Inara API Key** — personal API key from inara.cz
- **EDSM API Key** — personal API key from edsm.net

Stored in `~/.config/elite-bridge/config.json`. Accessed via `GET/PUT /api/v1/settings`.

## Code Conventions

### Python (backend)
- Type hints everywhere.
- Docstrings on all public functions/classes.
- Functions ≤ 30 lines preferred.
- Use `from __future__ import annotations`.
- No comments unless explaining *why*.
- Follow existing patterns in neighboring files.

### TypeScript/Vue (frontend)
- `<script setup lang="ts">` with Composition API.
- Interfaces in `api/endpoints.ts`, not inline.
- One Pinia store per data source.
- CSS scoped, using CSS variables from `main.css`.
- No comments unless explaining *why*.

### General
- Never invent entities — use `docs/domain/*.yaml`.
- Never add dependencies without justification.
- Never mix game logic into the frontend.
- Keep business logic out of Vue components.
- Backend tests: `tests/backend/test_*.py`.
- Frontend tests: not yet written.

## Department Pattern

Every department follows exactly:

```
Officer Report (summary, status, findings, recommendations)
  → Details (structured data)
    → History (session/cumulative)
```

Services return `DepartmentReport`. Frontend uses `OfficerReport.vue` + `StatisticCard.vue`.

## Key Files

| File | Purpose |
|---|---|
| `backend/bridge_core/state/engine.py` | GameState dataclasses + StateEngine (30+ event handlers) |
| `backend/bridge_core/services/report.py` | DepartmentReport, Finding, Recommendation dataclasses |
| `backend/bridge_core/api/server.py` | All REST endpoints + WebSocket |
| `backend/bridge_core/config/__init__.py` | Settings class (journal_path, inara_api_key, edsm_api_key) |
| `frontend/src/api/endpoints.ts` | All TypeScript interfaces + API functions |
| `frontend/src/layouts/MainLayout.vue` | 3-column layout with ButtonRails |
| `frontend/src/components/OfficerReport.vue` | Reusable report component |
| `docs/SPEC.md` | Authoritative product spec |

## Current Status

**Pre-Alpha.** Backend core (Phase 1) substantially complete. Frontend shell (Phases 2-4) complete. Navigation department is the reference implementation (end-to-end complete). Settings page with journal path and API key configuration. Remaining departments need detail work. See `docs/TASKS.md` for full roadmap.

## Before Coding

1. Read `docs/SPEC.md`, `docs/TASKS.md`, `docs/DOMAIN.md`.
2. Check existing code in the area you're changing.
3. Explain your plan before implementing.
4. After coding, run lint + tests.

## Never

- Commit secrets or API keys.
- Add comments unless explaining non-obvious logic.
- Invent fields not in the domain model.
- Put game logic in Vue components.
- Use `any` type in TypeScript without justification.
- Skip tests for new services or event handlers.
