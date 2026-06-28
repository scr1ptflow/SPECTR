import argparse
import json
import os
import sys

from . import __version__
from .reader import get_missions, _read_journal_dir

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(DIR, "config.json")


def cmd_list(args):
    journal_dir = args.journal_dir or _read_journal_dir(CONFIG_PATH)
    if not journal_dir:
        print("Error: journal directory not found.")
        sys.exit(1)

    data = get_missions(journal_dir)

    if args.json:
        json.dump({"ok": True, **data}, sys.stdout, indent=2)
        print()
        return

    for label, key in [("Active", "active"), ("Failed", "failed"), ("Complete", "complete")]:
        items = data[key]
        if not items:
            continue
        print(f"\n  {label} Missions")
        print(f"  {'─' * (len(label) + 10)}")
        for m in items:
            name = m.get("name", "?")
            print(f"    {name}")
            if m.get("destination_system"):
                print(f"      Destination: {m['destination_system']} / {m.get('destination_station', '?')}")
            p = m.get("progress")
            if p and p.get("target"):
                print(f"      {p.get('type', 'Progress')}: {p.get('current', 0)} / {p['target']}")
            if m.get("expires"):
                rem = m.get("remaining")
                if rem is not None:
                    d = int(rem // 86400)
                    h = int((rem % 86400) // 3600)
                    if d:
                        expiry = f"{d}d {h}h"
                    elif h:
                        expiry = f"{h}h"
                    else:
                        expiry = "< 1h"
                    print(f"      Expires: {expiry}")
                else:
                    print(f"      Expires: {m['expires']}")
            if m.get("reward"):
                print(f"      Reward: {m['reward']:,} CR")
            print()

    total = len(data["active"]) + len(data["failed"]) + len(data["complete"])
    if total == 0:
        print("  No missions found.")


def main():
    parser = argparse.ArgumentParser(
        prog="missions",
        description="Monitor Elite Dangerous missions",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--journal-dir", "-j", help="Journal directory")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
