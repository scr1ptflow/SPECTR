import os
import json
import glob
import logging
import threading
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

_DEFAULT_JOURNAL_PATH = os.path.expanduser(
    r"~\Saved Games\Frontier Developments\Elite Dangerous"
)


def _resolve_journal_path(path):
    if path and os.path.isdir(path):
        return path
    if os.path.isdir(_DEFAULT_JOURNAL_PATH):
        return _DEFAULT_JOURNAL_PATH
    return path or _DEFAULT_JOURNAL_PATH


class _JournalEventHandler(FileSystemEventHandler):
    """Handles journal file modifications and Status.json changes."""

    def __init__(self, monitor):
        super().__init__()
        self._monitor = monitor

    def on_modified(self, event):
        if event.is_directory:
            return
        self._monitor._handle_file_change(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._monitor._handle_file_change(event.src_path)


class JournalMonitor:
    def __init__(self, event_bus, journal_path=None, poll_interval=0.5):
        self.event_bus = event_bus
        self.journal_dir = self._resolve_journal_path(journal_path)
        self._running = False
        self._observer = None
        self._journal_file = None
        self._journal_pos = 0
        self._file_positions = {}
        self._status_mtime = 0
        self._poll_interval = poll_interval
        self._status_thread = None
        self._health_thread = None
        self._handler = None

        if not os.path.isdir(self.journal_dir):
            logger.warning(
                f"Journal directory not found: {self.journal_dir}. "
                "Make sure Elite Dangerous has been run at least once."
            )

    def _resolve_journal_path(self, path):
        return _resolve_journal_path(path)

    def _find_latest_journal(self):
        if not os.path.isdir(self.journal_dir):
            return None
        pattern = os.path.join(self.journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        return files[-1] if files else None

    def _tail_file(self, filepath, pos):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                f.seek(pos)
                lines = f.readlines()
                return f.tell(), lines
        except (OSError, UnicodeDecodeError):
            return pos, []

    def _handle_file_change(self, filepath):
        basename = os.path.basename(filepath)

        if basename == "Status.json":
            self._poll_status()
            return

        if not basename.startswith("Journal.") or not basename.endswith(".log"):
            return

        pos = self._file_positions.get(filepath, 0)
        try:
            file_size = os.path.getsize(filepath)
        except OSError:
            return
        if file_size < pos:
            pos = 0

        new_pos, lines = self._tail_file(filepath, pos)
        if lines:
            self._file_positions[filepath] = new_pos
            if filepath == self._journal_file:
                self._journal_pos = new_pos
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self.event_bus.publish("journal", data)
                    event_type = data.get("event", "")
                    if event_type:
                        self.event_bus.publish(f"journal:{event_type}", data)
                        logger.debug("Journal: %s", event_type)
                except json.JSONDecodeError:
                    pass

    def _poll_status(self):
        status_path = os.path.join(self.journal_dir, "Status.json")
        if not os.path.exists(status_path):
            return
        try:
            mtime = os.path.getmtime(status_path)
            if mtime > self._status_mtime:
                self._status_mtime = mtime
                with open(status_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.event_bus.publish("status", data)
        except (OSError, json.JSONDecodeError):
            pass

    def _status_poll_loop(self):
        """Fallback polling for Status.json in case watchdog misses mtime changes."""
        while self._running:
            self._poll_status()
            time.sleep(self._poll_interval)

    def start(self):
        self._running = True

        latest = self._find_latest_journal()
        if latest:
            self._journal_file = latest
            try:
                self._journal_pos = os.path.getsize(latest)
            except OSError:
                self._journal_pos = 0
            self._file_positions[latest] = self._journal_pos
            logger.info(f"Monitoring journal: {os.path.basename(latest)}")

        self._handler = _JournalEventHandler(self)
        self._start_observer()

        self._status_thread = threading.Thread(target=self._status_poll_loop, daemon=True)
        self._status_thread.start()

        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()

    def _start_observer(self):
        """Start the watchdog observer. Called on start and on recovery."""
        if not os.path.isdir(self.journal_dir):
            return
        self._observer = Observer()
        try:
            self._observer.schedule(self._handler, self.journal_dir, recursive=False)
            self._observer.start()
            logger.info("Journal watchdog started")
        except Exception as e:
            logger.error(f"Failed to start journal watchdog: {e}")
            self._observer = None

    def _health_check_loop(self):
        """Restart the watchdog observer if it crashes."""
        while self._running:
            time.sleep(5)
            if not self._running:
                return
            if self._observer is not None and not self._observer.is_alive():
                logger.warning("Journal watchdog died, restarting...")
                try:
                    self._observer.stop()
                    self._observer.join(timeout=2)
                except Exception:
                    pass
                self._start_observer()

    def start_async(self):
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()

    def stop(self):
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
        if self._status_thread:
            self._status_thread.join(timeout=2)
            self._status_thread = None
        if self._health_thread:
            self._health_thread.join(timeout=2)
            self._health_thread = None
        logger.info("Journal monitor stopped")

    def replay_all_journals(self, schedule_fn=None, done_callback=None):
        """Replay all journal files.
        
        If schedule_fn is provided, processes one file per tick to avoid
        blocking the UI. Otherwise runs synchronously.
        done_callback is called after the last file (only with schedule_fn).
        """
        if not os.path.isdir(self.journal_dir):
            if done_callback:
                done_callback()
            return
        pattern = os.path.join(self.journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        if not files:
            if done_callback:
                done_callback()
            return
        self._replay_total = 0
        if schedule_fn:
            self._replay_all_chunked(files, 0, schedule_fn, done_callback)
        else:
            for filepath in files:
                self._replay_file(filepath)

    def _replay_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self.event_bus.publish("journal", data)
                        event_type = data.get("event", "")
                        if event_type:
                            self.event_bus.publish(f"journal:{event_type}", data)
                        self._replay_total += 1
                    except json.JSONDecodeError:
                        pass
        except OSError as e:
            logger.warning(f"Failed to read journal {filepath}: {e}")

    def _replay_all_chunked(self, files, idx, schedule_fn, done_callback=None):
        if idx >= len(files):
            logger.info(f"Full replay done: {self._replay_total} events from {len(files)} files")
            self._replay_total = 0
            if done_callback:
                done_callback()
            return
        self._replay_file(files[idx])
        pct = (idx + 1) / len(files) * 100
        logger.info(f"Replay: {idx+1}/{len(files)} files ({pct:.0f}%) — {self._replay_total} events so far")
        schedule_fn(10, lambda: self._replay_all_chunked(files, idx + 1, schedule_fn, done_callback))

    def replay_all(self):
        if not os.path.isdir(self.journal_dir):
            return
        pattern = os.path.join(self.journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        if not files:
            return
        # Only read the latest journal file — all plugins persist state
        # individually and recover current system via tailing the last 16KB.
        filepath = files[-1]
        count = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self.event_bus.publish("journal", data)
                        event_type = data.get("event", "")
                        if event_type:
                            self.event_bus.publish(f"journal:{event_type}", data)
                        count += 1
                    except json.JSONDecodeError:
                        pass
        except OSError as e:
            logger.warning(f"Failed to read journal {filepath}: {e}")
        if count:
            logger.info(f"Replayed {count} events from {filepath}")
