"""Journal event parser for Elite Dangerous.

Parses JSON-lines journal files into structured JournalEvent objects.
Handles malformed lines gracefully and preserves event ordering.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class JournalEvent:
    """A single parsed journal event."""

    event: str
    timestamp: datetime
    data: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data


def parse_timestamp(ts: str) -> datetime:
    """Parse an Elite Dangerous timestamp string into a datetime."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.now(UTC)


def parse_line(line: str, source_file: str = "") -> JournalEvent | None:
    """Parse a single JSON line into a JournalEvent.

    Returns None for malformed or empty lines.
    """
    line = line.strip()
    if not line:
        return None

    try:
        raw = json.loads(line)
    except json.JSONDecodeError:
        log.debug("Malformed JSON in %s: %s", source_file, line[:100])
        return None

    event_name = raw.get("event", "")
    if not event_name:
        return None

    ts_str = raw.get("timestamp", "")
    timestamp = parse_timestamp(ts_str) if ts_str else datetime.now(UTC)

    return JournalEvent(
        event=event_name,
        timestamp=timestamp,
        data=raw,
        source_file=source_file,
    )


def read_journal(filepath: Path) -> Iterator[JournalEvent]:
    """Yield all events from a journal file, preserving order."""
    if not filepath.exists():
        return

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            event = parse_line(line, source_file=str(filepath))
            if event is not None:
                yield event
