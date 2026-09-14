 #!/usr/bin/env python3
"""
backup.py — Timestamped folder backup automation tool.

Zips one or more source folders into timestamped archives, logs every
operation, and optionally prunes old backups past a retention window.

Usage:
    python backup.py --source ./project1 ./project2 --dest ./backups
    python backup.py --source ./project1 --dest ./backups --retain-days 7
    python backup.py --config backup_config.json
"""

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path


def setup_logging(log_file: Path) -> None:
    """Configure logging to both console and a persistent log file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def make_timestamp() -> str:
    """Return a filesystem-safe timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_folder(source: Path, dest_dir: Path) -> Path:
    """
    Zip a single source folder into dest_dir with a timestamped name.
    Returns the path to the created archive.
    """
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {source}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = make_timestamp()
    archive_name = f"{source.name}_{timestamp}"
    archive_base_path = dest_dir / archive_name  # shutil adds the extension

    logging.info("Starting backup: %s -> %s.zip", source, archive_base_path)
    start = time.time()

    # shutil.make_archive handles the zipping; base_dir=source.name with
    # root_dir=source.parent keeps paths inside the zip clean/relative.
    archive_path_str = shutil.make_archive(
        base_name=str(archive_base_path),
        format="zip",
        root_dir=str(source.parent),
        base_dir=source.name,
    )

    elapsed = time.time() - start
    archive_path = Path(archive_path_str)
    size_mb = archive_path.stat().st_size / (1024 * 1024)

    logging.info(
        "Backup complete: %s (%.2f MB) in %.2fs",
        archive_path.name, size_mb, elapsed
    )
    return archive_path


def prune_old_backups(dest_dir: Path, retain_days: int) -> None:
    """Delete .zip files in dest_dir older than retain_days."""
    if retain_days <= 0:
        return

    cutoff = time.time() - (retain_days * 86400)
    removed = 0

    for zip_file in dest_dir.glob("*.zip"):
        if zip_file.stat().st_mtime < cutoff:
            logging.info("Pruning old backup: %s", zip_file.name)
            zip_file.unlink()
            removed += 1

    logging.info("Pruning complete. %d old archive(s) removed.", removed)


def load_config(config_path: Path) -> dict:
    """Load source/dest/retention settings from a JSON config file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zip folders into timestamped backup archives."
    )
    parser.add_argument(
        "--source", nargs="+", help="One or more source folder paths to back up."
    )
    parser.add_argument(
        "--dest", help="Destination folder where backup zips are stored."
    )
    parser.add_argument(
        "--retain-days", type=int, default=0,
        help="Delete backups older than N days (0 = keep forever)."
    )
    parser.add_argument(
        "--config", help="Path to a JSON config file (overrides other flags)."
    )
    parser.add_argument(
        "--log-file", default="backup.log", help="Path to the log file."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.config:
        config = load_config(Path(args.config))
        sources = [Path(p) for p in config["source"]]
        dest = Path(config["dest"])
        retain_days = config.get("retain_days", 0)
        log_file = Path(config.get("log_file", args.log_file))
    else:
        if not args.source or not args.dest:
            print("Error: --source and --dest are required unless --config is used.")
            return 1
        sources = [Path(p) for p in args.source]
        dest = Path(args.dest)
        retain_days = args.retain_days
        log_file = Path(args.log_file)

    setup_logging(log_file)
    logging.info("=== Backup run started ===")

    exit_code = 0
    for source in sources:
        try:
            backup_folder(source, dest)
        except Exception as e:
            logging.error("Failed to back up %s: %s", source, e)
            exit_code = 1

    if retain_days > 0:
        prune_old_backups(dest, retain_days)

    logging.info("=== Backup run finished ===")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
