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


def read_current_system(journal_file):
    if not journal_file:
        return None
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
