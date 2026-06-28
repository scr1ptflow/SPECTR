import argparse
import os
import sys

from . import __version__
from .reader import get_ship_data, read_journal_dir, CATEGORY_LABELS

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(DIR, "config.json")

BAR_WIDTH = 20


def _bar(value: float | None, width: int = BAR_WIDTH) -> str:
    if value is None:
        return " " * width
    filled = round(value * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _pct(value: float | None) -> str:
    if value is None:
        return " N/A"
    return f"{value * 100:5.1f}%"


def cmd_show(args):
    journal_dir = args.journal_dir or read_journal_dir(CONFIG_PATH)
    if not journal_dir:
        print("Error: journal directory not found. Set --journal-dir or ED_JOURNAL_DIR.")
        sys.exit(1)

    data = get_ship_data(journal_dir)
    if not data["modules"] and not data["ship"]:
        print("No ship data found (no Loadout event in latest journal).")
        sys.exit(1)

    ship_name = data["ship"] or "Unknown Ship"
    print(f"\n  {ship_name}\n")

    shield = data["shield_health"]
    hull = data["hull_health"]

    shield_via_status = data["shield_health"] is not None
    if shield_via_status:
        print(f"  Shield  [{_bar(shield)}]  {_pct(shield)}")
    elif data["shield_gen"]:
        sg = data["shield_gen_health"]
        print(f"  Shield  [{_bar(sg)}]  {_pct(sg)}")
    else:
        print(f"  Shield  [{' '*BAR_WIDTH}]  no shield gen")
    print(f"  Hull    [{_bar(hull)}]  {_pct(hull)}")

    sv = data.get("ship_value")
    rb = data.get("rebuy")
    cr = data.get("credits")
    ec = data.get("economy")
    cv = data.get("cargo_value")
    if sv is not None:
        print(f"  Value   {sv:>12,} Cr")
    if rb is not None:
        print(f"  Rebuy   {rb:>12,} Cr")
    if cr is not None:
        print(f"  Wallet  {cr:>12,} Cr")
    if cv is not None:
        print(f"  Cargo   {cv:>12,} Cr")
    if ec:
        print(f"  Economy {ec}")
    print()

    categories = {}
    for m in data["modules"]:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m)

    for cat in ("hardpoints", "utility", "core", "optional", "other"):
        items = categories.get(cat)
        if not items:
            continue
        label = CATEGORY_LABELS.get(cat, cat)
        print(f"  {'── ' + label + ' ──':─<40}")
        for m in items:
            bar = _bar(m["health"])
            pct = _pct(m["health"])
            rating = f" ({m['rating']})" if m.get("rating") else ""
            print(f"  {m['name'][:30]:30s}{rating}  [{bar}]  {pct}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="ship_status",
        description="View ship hull, shields, and module health",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--journal-dir", "-j", help="Journal directory (auto-detected if omitted)")
    parser.set_defaults(func=cmd_show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
