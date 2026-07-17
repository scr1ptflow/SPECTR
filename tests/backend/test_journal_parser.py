"""Tests for the journal parser."""

from datetime import datetime, timezone

from bridge_core.journal.parser import JournalEvent, parse_line, parse_timestamp, read_journal
from pathlib import Path
import tempfile


def test_parse_timestamp_utc():
    ts = parse_timestamp("2024-01-15T10:30:00Z")
    assert ts.year == 2024
    assert ts.month == 1
    assert ts.hour == 10
    assert ts.tzinfo == timezone.utc


def test_parse_timestamp_with_millis():
    ts = parse_timestamp("2024-01-15T10:30:00.123Z")
    assert ts.year == 2024
    assert ts.microsecond == 123000


def test_parse_line_valid():
    line = '{"timestamp":"2024-01-15T10:30:00Z","event":"FSDJump","StarSystem":"Sol"}'
    event = parse_line(line, source_file="test.log")
    assert event is not None
    assert event.event == "FSDJump"
    assert event.get("StarSystem") == "Sol"
    assert event.source_file == "test.log"


def test_parse_line_empty():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_line_malformed_json():
    assert parse_line("not json") is None
    assert parse_line("{broken") is None


def test_parse_line_no_event_field():
    line = '{"timestamp":"2024-01-15T10:30:00Z","data":"no event"}'
    assert parse_line(line) is None


def test_journal_event_getitem():
    event = JournalEvent(
        event="Test",
        timestamp=datetime.now(timezone.utc),
        data={"key": "value"},
    )
    assert event["key"] == "value"
    assert event.get("missing", "default") == "default"
    assert "key" in event
    assert "missing" not in event


def test_read_journal_from_file():
    content = (
        '{"timestamp":"2024-01-15T10:00:00Z","event":"LoadGame","Commander":"TestCmdr"}\n'
        '{"timestamp":"2024-01-15T10:01:00Z","event":"Location","StarSystem":"Sol"}\n'
        'bad line\n'
        '{"timestamp":"2024-01-15T10:02:00Z","event":"FSDJump","StarSystem":"Alpha Centauri"}\n'
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        f.write(content)
        f.flush()
        events = list(read_journal(Path(f.name)))

    assert len(events) == 3
    assert events[0].event == "LoadGame"
    assert events[1].event == "Location"
    assert events[2].event == "FSDJump"
    assert events[2].get("StarSystem") == "Alpha Centauri"


def test_read_journal_nonexistent():
    events = list(read_journal(Path("/nonexistent/file.log")))
    assert events == []
