# SPECTR — Agent Guide

## Project Structure
- `main.py` — Entry point for `python main.py`
- `spectr/__main__.py` — Entry point for `python -m spectr`
- `spectr/app.py` — Textual App class (CSS styles, tab registry, panel switching)
- `spectr/config.py` — JSON config at `~/.config/spectr/config.json`
- `spectr/journal.py` — JournalReader: reads Elite journal files, tracks ranks/progress, exobiology, squadron, powerplay
- `spectr/inara.py` — InaraClient: fetches commander profile from Inara API (`/inapi/v1/`)
- `spectr/ui/sidebar.py` — Left sidebar with vertical tab buttons
- `spectr/ui/panels.py` — One PanelBase subclass per tab

## Conventions
- Panel classes extend `PanelBase(Static)`, placed in `panels.py`
- Each panel is registered in `TAB_PANELS` dict in `app.py` and has a matching sidebar entry in `TAB_ITEMS` in `sidebar.py`
- Use `self.app.journal` / `self.app.config` to access shared state from panels
- Tab switching uses direct `self.app._show_panel()` calls from sidebar (no message passing)
- All panels are pre-mounted in `compose()`; `.hidden` CSS class toggles visibility
- CSS lives in `app.py` as a class attribute on `SpectrApp`
- Run: `./run.sh` (auto-creates venv if missing)

## Key Data Flow
- **Ranks & Progress** — Primary source is journal `Rank` / `Progress` events; Inara API merged as fallback
- **Credits** — Journal `LoadGame.Credits`; overridden by Inara if available
- **Squadron** — Journal `LoadGame.SquadronName`
- **Powerplay** — Journal `Powerplay` event (power, rank, merits)
- **InaraClient** — Uses `header` block with `appName`/`appVersion`/`APIkey`/`commanderName`, events with `eventName`/`eventTimestamp`/`eventData`. Endpoint: `https://inara.cz/inapi/v1/`

## Style
- No comments in code
- No emoji in output
- Names: snake_case for methods/vars, PascalCase for classes
- Imports: `from __future__ import annotations` at top
