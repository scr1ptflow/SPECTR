# SPECTR — Cleanup TODO

## Status
- [x] = done
- [-] = skipped/not applicable

---

## Critical

- [x] BUG-01: Fix worker thread race conditions — stop/disconnect old workers before creating new ones in DashboardPanel, LocationPanel, ScannerPanel, EngineeringPanel
- [x] BUG-02: Fix Powerplay merge using `not rank`/`not merits` — use sentinel None instead of 0 (journal.py:370-377)
- [x] BUG-03: Fix double `get_latest_event("Loadout")` call in ScannerPanel (panels.py:1411)
- [x] BUG-04: Fix FUIPanel hardcoded orange border — use per-panel accent color (widgets.py:64-67)
- [x] BUG-05: Fix InaraClient recreated every refresh — make it persistent per panel (panels.py:428-437)
- [x] BUG-06: Restore per-tab accent colors in sidebar (CYAN/BLUE/PURPLE etc.) (main_window.py:32-43)

## Medium — Performance

- [x] PERF-01: Add get_latest_events() batch method to JournalReader for single-pass multi-event lookup
- [-] PERF-02: Scanner parallel HTTP requests for nearby systems — skipped, requires async architecture
- [-] PERF-03: Optimize _collect_log_events — skipped, 200-entry cap is sufficient
- [x] PERF-04: Make EDSM cache persistent across panels via shared client on MainWindow

## Medium — Thread Safety

- [x] THREAD-01: Guard worker signal handlers via _stop_worker() which disconnects before stop
- [x] THREAD-02: Guard ServerStatusChecker.check() against re-entrancy

## Low — Redundancy

- [x] REDUN-01: Extract _clear_layout() to module-level shared utility
- [x] REDUN-02: Move DEFAULT_CONFIG import to top of panels.py
- [x] REDUN-03: Extract button style boilerplate to _toggle_btn_style() helper

## Low — Dead Code

- [x] DEAD-01: Remove FUIPanel._accent, set_accent() dead code
- [x] DEAD-02: Remove FUIAnnunciator._flash (set but never read)
- [x] DEAD-03: Remove unused FUIContinuousBar class
- [x] DEAD-04: Remove JournalReader._current_file unused attribute
- [-] DEAD-05: Unused color imports in main_window.py — now all used after per-tab colors restored

## Low — Other Bugs

- [x] BUG-04b: Fix SettingsPanel placeholder-to-value silent conversion
- [x] BUG-06b: Fix MissionCompleted zero-reward display

## Low — Cleanup

- [x] Clean up Optional imports — replaced with X | None in journal.py, inara.py, edsm.py, species.py
- [x] Update AGENTS.md and README.md with all changes
