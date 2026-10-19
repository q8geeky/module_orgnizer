"""Headless preview / batch front end for the safe Civitai model organizer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from organizer_core import organize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview categorization by SHA-256; moves require --apply --yes.")
    parser.add_argument("folder", type=Path, help="Folder containing model files")
    parser.add_argument("--recursive", action="store_true",
                        help="Scan nested folders, preserving their relative paths")
    parser.add_argument("--offline", action="store_true",
                        help="Use existing local SHA-256 cache; make no HTTP calls")
    parser.add_argument("--apply", action="store_true", help="Actually move resolved files")
    parser.add_argument("--yes", action="store_true", help="Confirm intended file moves")
    parser.add_argument("--json", action="store_true", help="Print structured JSON summary")
    args = parser.parse_args(argv)
    if args.apply and not args.yes:
        parser.error("--apply requires --yes (preview runs without either flag)")
    events = []
    def progress(event):
        index, total, path, status = event
        if args.json:
            events.append(dict(index=index, total=total, file=path, status=status))
        else:
            print(f"[{index}/{total}] {path}: {status}")
    try:
        stats = organize(args.folder, dry_run=not args.apply,
                         recursive=args.recursive, offline=args.offline,
                         on_progress=progress)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    if args.json:
        print(json.dumps(dict(dry_run=not args.apply, recursive=args.recursive,
                              offline=args.offline, stats=stats, events=events),
                         indent=2))
    else:
        print("Summary:", ", ".join(f"{k}={v}" for k,v in stats.items()))
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
