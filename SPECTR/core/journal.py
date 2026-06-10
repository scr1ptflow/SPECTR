import os
import json
import time
import glob
import logging
import threading

# Number of bytes to scan from the end of a journal file for state recovery
_JOURNAL_TAIL_BYTES = 131072  # 128 KB (~2000+ journal entries)


DEFAULT_JOURNAL_PATH = os.path.expanduser(
    r"~\Saved Games\Frontier Developments\Elite Dangerous"
)


def default_journal_path(config_journal_path=None):
    if config_journal_path and os.path.isdir(config_journal_path):
        return config_journal_path
    if os.path.isdir(DEFAULT_JOURNAL_PATH):
        return DEFAULT_JOURNAL_PATH
    return config_journal_path or DEFAULT_JOURNAL_PATH


def read_last_journal_event(journal_dir, event_names):
    """Scan from the end of the latest journal file for the last matching event.
    Returns the parsed event dict, or None."""
    if not os.path.isdir(journal_dir):
        return None
    pattern = os.path.join(journal_dir, "Journal.*.log")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    latest = files[-1]
    try:
        file_size = os.path.getsize(latest)
        with open(latest, "rb") as f:
            chunk_size = min(file_size, _JOURNAL_TAIL_BYTES)
            f.seek(file_size - chunk_size)
            # Skip the first partial line
            f.readline()
            lines = f.readlines()
        # Scan backwards for the last matching event
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event") in event_names:
                return entry
    except (OSError, json.JSONDecodeError):
        pass
    return None

logger = logging.getLogger(__name__)


class JournalMonitor:
    def __init__(self, event_bus, journal_path=None, poll_interval=0.5):
        self.event_bus = event_bus
        self.poll_interval = poll_interval
        self.journal_dir = self._resolve_journal_path(journal_path)
        self._running = False
        self._thread = None
        self._journal_file = None
        self._journal_pos = 0
        self._status_mtime = 0

        if not os.path.isdir(self.journal_dir):
            logger.warning(
                f"Journal directory not found: {self.journal_dir}. "
                "Make sure Elite Dangerous has been run at least once."
            )

    def _resolve_journal_path(self, path):
        if path and os.path.isdir(path):
            return path
        default = os.path.expanduser(
            r"~\Saved Games\Frontier Developments\Elite Dangerous"
        )
        if os.path.isdir(default):
            return default
        return path or default

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

    def start(self):
        self._running = True
        while self._running:
            self._poll()
            time.sleep(self.poll_interval)

    def start_async(self):
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        logger.info("Journal monitor started")

    def stop(self):
        self._running = False
        logger.info("Journal monitor stopped")

    def replay_all(self):
        if not os.path.isdir(self.journal_dir):
            return
        pattern = os.path.join(self.journal_dir, "Journal.*.log")
        files = sorted(glob.glob(pattern))
        count = 0
        for filepath in files:
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
                                logger.debug("Journal: %s", event_type)
                            count += 1
                        except json.JSONDecodeError:
                            pass
            except OSError as e:
                logger.warning(f"Failed to read journal {filepath}: {e}")
        if count:
            logger.info(f"Replayed {count} events from {len(files)} journal files")

    def _poll(self):
        if not os.path.isdir(self.journal_dir):
            return

        latest = self._find_latest_journal()
        if latest and latest != self._journal_file:
            self._journal_file = latest
            self._journal_pos = 0
            logger.info(f"Monitoring journal: {os.path.basename(latest)}")

        if self._journal_file and os.path.exists(self._journal_file):
            try:
                file_size = os.path.getsize(self._journal_file)
            except OSError:
                return
            if file_size < self._journal_pos:
                self._journal_pos = 0

            new_pos, lines = self._tail_file(self._journal_file, self._journal_pos)
            if lines:
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

        status_path = os.path.join(self.journal_dir, "Status.json")
        if os.path.exists(status_path):
            try:
                mtime = os.path.getmtime(status_path)
                if mtime > self._status_mtime:
                    self._status_mtime = mtime
                    with open(status_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.event_bus.publish("status", data)
            except (OSError, json.JSONDecodeError):
                pass
