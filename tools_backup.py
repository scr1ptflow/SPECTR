import argparse
import gzip
import glob
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "config.json"
DEFAULT_BACKUP_DIR = PROJECT_DIR / "backups" / "journals"
MANIFEST = "manifest.json"


def die(msg: str):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def read_config() -> dict:
    if not CONFIG_PATH.exists():
        die(f"config.json not found at {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        return json.load(f)


def find_journal_dir() -> str:
    cfg = read_config()
    path = cfg.get("journal_path", "")
    if not path or not os.path.isdir(path):
        die("journal_path in config.json is missing or does not exist")
    return path


def find_journals(directory: str) -> list[Path]:
    files = sorted(glob.glob(os.path.join(directory, "Journal.*.log")))
    return [Path(f) for f in files]


def load_manifest(backup_dir: Path) -> dict:
    mf = backup_dir / MANIFEST
    if mf.exists():
        with open(mf) as f:
            return json.load(f)
    return {}


def save_manifest(backup_dir: Path, manifest: dict):
    with open(backup_dir / MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)


def cmd_backup(backup_dir: Path):
    src = Path(find_journal_dir())
    backup_dir.mkdir(parents=True, exist_ok=True)
    journals = find_journals(str(src))
    if not journals:
        print("No journal files found.")
        return

    manifest = load_manifest(backup_dir)
    copied = 0
    skipped = 0
    raw_bytes = 0
    comp_bytes = 0

    for j in journals:
        s = j.stat()
        key = j.name
        entry = manifest.get(key)
        if entry and entry["mtime_ns"] == s.st_mtime_ns and entry["size"] == s.st_size:
            skipped += 1
            if "compressed_size" in entry:
                comp_bytes += entry["compressed_size"]
            raw_bytes += s.st_size
            continue

        gz_path = backup_dir / (key + ".gz")
        with open(j, "rb") as fin, gzip.open(gz_path, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        gz_stat = gz_path.stat()

        manifest[key] = {
            "mtime_ns": s.st_mtime_ns,
            "size": s.st_size,
            "compressed_size": gz_stat.st_size,
        }
        raw_bytes += s.st_size
        comp_bytes += gz_stat.st_size
        copied += 1

    save_manifest(backup_dir, manifest)

    ratio = (1 - comp_bytes / raw_bytes) * 100 if raw_bytes else 0
    print(
        f"Backed up {copied} journal(s) ({skipped} skipped) "
        f"— saved {ratio:.0f}% space ({raw_bytes/1e6:.1f} MB → {comp_bytes/1e6:.1f} MB)"
    )


def cmd_restore(backup_dir: Path):
    if not backup_dir.is_dir():
        die(f"Backup directory not found: {backup_dir}")
    manifest = load_manifest(backup_dir)
    if not manifest:
        print("No backup manifest found.")
        return
    dst = Path(find_journal_dir())
    restored = 0
    skipped = 0
    for name, entry in manifest.items():
        gz_path = backup_dir / (name + ".gz")
        if not gz_path.exists():
            print(f"  Warning: {gz_path} missing from backup, skipping")
            continue
        dst_path = dst / name
        if dst_path.exists():
            ds = dst_path.stat()
            if ds.st_mtime_ns == entry["mtime_ns"] and ds.st_size == entry["size"]:
                skipped += 1
                continue
        with gzip.open(gz_path, "rb") as fin, open(dst_path, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        os.utime(dst_path, ns=(entry["mtime_ns"], entry["mtime_ns"]))
        restored += 1
    print(f"Restored {restored} journal(s) to {dst} ({skipped} already current)")


def cmd_list(backup_dir: Path):
    manifest = load_manifest(backup_dir)
    if not manifest:
        print("No backup manifest found.")
        return
    src = Path(find_journal_dir())
    total_raw = 0
    total_comp = 0
    for name in sorted(manifest):
        e = manifest[name]
        orig = src / name
        if orig.exists() and orig.stat().st_mtime_ns == e["mtime_ns"] and orig.stat().st_size == e["size"]:
            status = "ok"
        elif orig.exists():
            status = "changed"
        else:
            status = "missing"
        gz_path = backup_dir / (name + ".gz")
        gz_size = gz_path.stat().st_size if gz_path.exists() else e.get("compressed_size", 0)
        total_raw += e["size"]
        total_comp += gz_size
        print(
            f"  {name}  ({e['size']/1e6:.1f} MB → {gz_size/1e6:.1f} MB, "
            f"{gz_size/e['size']*100:.0f}%)  — {status}"
        )
    ratio = (1 - total_comp / total_raw) * 100 if total_raw else 0
    print(
        f"Total: {len(manifest)} file(s), {total_raw/1e6:.1f} MB → "
        f"{total_comp/1e6:.1f} MB ({ratio:.0f}% compression)"
    )


def main():
    parser = argparse.ArgumentParser(description="Backup or restore Elite Dangerous journals (gzip compressed)")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list"],
        help="Action to perform",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(DEFAULT_BACKUP_DIR),
        help=f"Backup directory (default: {DEFAULT_BACKUP_DIR})",
    )
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir)

    if args.action == "backup":
        cmd_backup(backup_dir)
    elif args.action == "restore":
        cmd_restore(backup_dir)
    elif args.action == "list":
        cmd_list(backup_dir)


if __name__ == "__main__":
    main()
