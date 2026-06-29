import argparse
import json
import sys

from . import journal, edsm, checkers
from webui._utils import find_journal_dir, read_config


def main():
    parser = argparse.ArgumentParser(
        prog="lrs",
        description="Long Range Sensor — find services near your current system",
    )
    sub = parser.add_subparsers(dest="command")

    chk = sub.add_parser("check", help="Run service checks")
    chk.add_argument(
        "--checks", nargs="+",
        choices=list(checkers.list_checkers()) + ["all"],
        default=["all"],
        help="Checks to run (default: all)",
    )
    chk.add_argument("--journal-dir", help="Override journal directory")
    chk.add_argument("--radius", type=int, default=100,
                     help="Search radius in light-years")
    chk.add_argument("--ship-size", choices=["S", "M", "L"], default="L",
                     help="Your ship's max landing pad size (default: L)")
    chk.add_argument("--json", action="store_true",
                     help="Output raw JSON")

    args = parser.parse_args()

    if args.command != "check":
        parser.print_help()
        return 1

    config = read_config()
    journal_dir = args.journal_dir or config.get("journal_path") or ""
    if not journal_dir:
        journal_dir = find_journal_dir()
    if not journal_dir:
        print("error: journal directory not configured — set journal_path in config.json or use --journal-dir")
        return 1

    jfile = journal.get_latest_journal(journal_dir)
    if not jfile:
        print("error: no journal files found in", journal_dir)
        return 1

    system = journal.read_current_system(jfile)
    if not system:
        print("error: could not determine current system")
        return 1

    api_key = config.get("edsm", {}).get("api_key") or None
    client = edsm.EdsmClient(api_key=api_key)

    sys_info = client.system_info(system)
    if not sys_info:
        print(f"error: could not look up system '{system}' on EDSM")
        return 1

    coords = sys_info.get("coords")
    if not coords:
        print(f"error: no coordinates available for '{system}'")
        return 1

    cx, cy, cz = coords["x"], coords["y"], coords["z"]
    print(f"Current system: {system}")
    print(f"Coordinates:    ({cx:.2f}, {cy:.2f}, {cz:.2f})")
    print()

    which = args.checks
    if "all" in which:
        which = list(checkers.list_checkers().keys())

    for name in which:
        desc = checkers.list_checkers()[name]
        print(f"── {desc} ──")

        print("  Searching...")
        results = run_check_safe(name, system, client, radius=args.radius, ship_size=args.ship_size)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("  Nothing found within range\n")
            else:
                labels = {"planetary": "Planetary", "station": "Station", "carrier": "Carrier"}
                for r in results:
                    label = labels.get(r["category"], r["category"])
                    arrival = r.get("distance_to_arrival_ls", 0)
                    if arrival:
                        arrival = round(arrival) if arrival > 100 else round(arrival, 1)
                        arrival_str = f", {arrival} Ls"
                    else:
                        arrival_str = ""
                    pad = r.get("max_pad", "")
                    print(f"  {label:10s} {r['station']} @ {r['system']}  ({r['distance_ly']} LY, pad {pad}{arrival_str})")
                print()

    return 0


def run_check_safe(name, system, client, radius, ship_size):
    try:
        return checkers.run_check(name, system, client, radius=radius, ship_size=ship_size)
    except edsm.EdsmError as e:
        print(f"  EDSM API error: {e}")
        return []
    except Exception as e:
        print(f"  Error running '{name}': {e}")
        return []


if __name__ == "__main__":
    sys.exit(main())
