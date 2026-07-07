import json
import os
import glob

_CURRENT_SYSTEM_EVENTS = {"Location", "FSDJump", "CarrierJump", "Docked"}


def get_latest_journal(journal_dir):
    if not journal_dir or not os.path.isdir(journal_dir):
        return None
    pattern = os.path.join(journal_dir, "Journal.*.log")
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None


def _scan_file_for_system(journal_file):
    """Scan a single journal file and return the last known system, or None."""
    system = None
    with open(journal_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") not in _CURRENT_SYSTEM_EVENTS:
                continue
            for key in ("StarSystem", "System", "SystemName"):
                if key in event:
                    system = event[key]
                    break
    return system


def read_current_system(journal_file):
    if not journal_file:
        return None
    system = _scan_file_for_system(journal_file)
    if system:
        return system
    # Latest file has no location event yet (e.g. new session, just Fileheader).
    # Fall back to previous journals in reverse chronological order.
    jdir = os.path.dirname(journal_file)
    pattern = os.path.join(jdir, "Journal.*.log")
    files = sorted(glob.glob(pattern), reverse=True)
    for f in files:
        if f == journal_file:
            continue
        system = _scan_file_for_system(f)
        if system:
            return system
    return None
