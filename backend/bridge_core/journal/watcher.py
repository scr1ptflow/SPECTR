"""Journal file watcher — monitors the journal directory for new events.

Uses watchfiles to detect changes and incrementally reads new journal data.
Handles file rotation, crash recovery, and deduplication.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from watchfiles import awatch

from bridge_core.events.bus import Event, EventBus
from bridge_core.journal.parser import JournalEvent, parse_line, read_journal

log = logging.getLogger(__name__)


class JournalWatcher:
    """Watches Elite Dangerous journal files and publishes events to the bus.

    Responsibilities:
    - Detect new journal files (game rotates journals)
    - Read journals incrementally (track file positions)
    - Publish each parsed event to the EventBus
    - Ignore duplicate events
    - Preserve event order
    """

    def __init__(self, journal_path: str, bus: EventBus) -> None:
        self.journal_path = Path(journal_path).expanduser() if journal_path else Path("")
        self.bus = bus
        self._file_positions: dict[str, int] = {}
        self._seen_events: set[str] = set()
        self._running = False

    def _find_latest_journal(self) -> Path | None:
        """Find the most recent journal file."""
        if not self.journal_path.exists():
            return None
        journals = sorted(self.journal_path.glob("Journal.*.log"), reverse=True)
        return journals[0] if journals else None

    def _find_all_journals(self) -> list[Path]:
        """Find all journal files, newest first."""
        if not self.journal_path.exists():
            return []
        return sorted(self.journal_path.glob("Journal.*.log"), reverse=True)

    def _read_incremental(self, filepath: Path) -> list[JournalEvent]:
        """Read only new lines from a journal file since last read."""
        key = str(filepath)
        last_pos = self._file_positions.get(key, 0)

        if not filepath.exists():
            return []

        events = []
        try:
            with open(filepath, encoding="utf-8") as f:
                f.seek(last_pos)
                for line in f:
                    event = parse_line(line, source_file=key)
                    if event is not None:
                        event_key = f"{event.event}:{event.timestamp.isoformat()}"
                        if event_key not in self._seen_events:
                            self._seen_events.add(event_key)
                            events.append(event)
                self._file_positions[key] = f.tell()
        except OSError as exc:
            log.warning("Failed to read %s: %s", filepath, exc)

        return events

    def _scan_existing(self) -> list[JournalEvent]:
        """On startup, scan all existing journals to rebuild state.

        Reads from oldest to newest to preserve chronological order.
        """
        journals = self._find_all_journals()
        journals.reverse()  # oldest first

        all_events = []
        for journal in journals:
            for event in read_journal(journal):
                event_key = f"{event.event}:{event.timestamp.isoformat()}"
                if event_key not in self._seen_events:
                    self._seen_events.add(event_key)
                    all_events.append(event)
            self._file_positions[str(journal)] = journal.stat().st_size

        return all_events

    async def run(self) -> None:
        """Main watcher loop. Call from the application runner."""
        self._running = True
        log.info("Journal watcher started for: %s", self.journal_path)

        if not self.journal_path.exists():
            log.warning("Journal path does not exist: %s", self.journal_path)
            log.info("Waiting for journal path to appear...")

        # Initial scan of existing journals
        initial_events = self._scan_existing()
        if initial_events:
            log.info("Loaded %d historical events from journals.", len(initial_events))
            for event in initial_events:
                await self._publish_event(event)

        # Watch for changes
        async for changes in awatch(
            self.journal_path,
            stop_event=asyncio.Event() if not self._running else None,
        ):
            if not self._running:
                break

            for change_type, path_str in changes:
                path = Path(path_str)
                if not path.name.startswith("Journal.") or not path.name.endswith(".log"):
                    continue

                if change_type.value == 2:  # modified or created
                    new_events = self._read_incremental(path)
                    for event in new_events:
                        await self._publish_event(event)

    async def _publish_event(self, event: JournalEvent) -> None:
        """Publish a journal event to the bus."""
        topic = f"journal.{event.event.lower()}"
        await self.bus.publish(Event(
            topic=topic,
            data=event.data,
            timestamp=event.timestamp,
            source="journal",
        ))

    def stop(self) -> None:
        """Signal the watcher to stop."""
        self._running = False
