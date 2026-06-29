"""Journal file watcher and recorder."""

import json
import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .store import Store
from .formatter import print_progress

logger = logging.getLogger(__name__)


class Recorder:
    """Watches the ED journal directory and records all events."""

    def __init__(self, store: Store, journal_dir: Path, status_interval: float = 5.0):
        self.store = store
        self.journal_dir = journal_dir
        self._positions: dict[str, tuple[int, int]] = {}
        self._status_interval = status_interval
        self._last_status_read = 0.0
        self._observer = Observer()

    def catch_up(self):
        """Read all existing journal files."""
        files = sorted(self.journal_dir.glob("Journal.*.log"), key=lambda p: p.stat().st_mtime)
        total = len(files)
        for i, jf in enumerate(files, 1):
            before = self.store.get_stats()["events"]
            self._read_journal(jf)
            after = self.store.get_stats()["events"]
            print_progress(i, total, suffix=f"files · {after - before} events")
        if total:
            total_events = self.store.get_stats()["events"]
            print_progress(total, total, suffix=f"files · {total_events} total events")

    def watch(self):
        """Start watching for file changes."""
        handler = _JournalEventHandler(self)
        self._observer.schedule(handler, str(self.journal_dir), recursive=False)
        self._observer.start()
        logger.info("Watching %s", self.journal_dir)

    def stop(self):
        self._observer.stop()
        self._observer.join()

    def _read_journal(self, fpath: Path):
        fname = str(fpath)
        try:
            size = fpath.stat().st_size
            byte_pos, line_num = self._positions.get(fname, (0, 1))
        except FileNotFoundError:
            self._positions.pop(fname, None)
            return

        if size <= byte_pos:
            return

        try:
            with fpath.open("r", encoding="utf-8") as f:
                f.seek(byte_pos)
                for line in f:
                    line = line.rstrip("\n\r")
                    if not line:
                        line_num += 1
                        continue
                    try:
                        data = json.loads(line)
                        ts = data.get("timestamp", "")
                        event = data.get("event", "")
                        self.store.insert_event(ts, event, line, fname, line_num)
                    except json.JSONDecodeError:
                        pass
                    line_num += 1
                self._positions[fname] = (f.tell(), line_num)
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Error reading %s: %s", fname, e)

    def _read_status(self):
        now = time.time()
        if now - self._last_status_read < self._status_interval:
            return
        self._last_status_read = now

        status_file = self.journal_dir / "Status.json"
        if not status_file.exists():
            return

        try:
            raw = status_file.read_text(encoding="utf-8")
            data = json.loads(raw)
            ts = data.get("timestamp", "")
            self.store.insert_status(ts, raw)
        except (json.JSONDecodeError, OSError):
            pass


class _JournalEventHandler(FileSystemEventHandler):
    def __init__(self, recorder: Recorder):
        self.recorder = recorder

    def _is_journal(self, name: str) -> bool:
        return name.startswith("Journal.") and name.endswith(".log")

    def on_modified(self, event):
        path = Path(event.src_path)
        name = path.name
        if self._is_journal(name):
            self.recorder._read_journal(path)
        elif name == "Status.json":
            self.recorder._read_status()

    def on_created(self, event):
        path = Path(event.src_path)
        name = path.name
        if self._is_journal(name):
            self.recorder._read_journal(path)
