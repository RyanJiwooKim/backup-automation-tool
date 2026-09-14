# Backup Automation Tool

A command-line Python tool that zips one or more folders into timestamped
archives, logs every operation, and prunes backups past a configurable
retention window.

## Features
- Timestamped zip archives (`foldername_YYYYMMDD_HHMMSS.zip`)
- Supports multiple source folders in a single run
- Structured logging to console + file (auditable history of every run)
- Retention policy — automatically deletes archives older than N days
- Config-file mode for scheduled/unattended runs (cron, Task Scheduler)

## Usage

Direct CLI:
```bash
python backup.py --source ./project1 ./project2 --dest ./backups --retain-days 30
```

Config-file mode (recommended for scheduled jobs):
```bash
python backup.py --config backup_config.json
```

Config file format (see `backup_config.example.json`):
```json
{
  "source": ["./project1", "./project2"],
  "dest": "./backups",
  "retain_days": 30,
  "log_file": "backup.log"
}
```

## Scheduling it

**Linux/macOS (cron)** — run daily at 2 AM:
```bash
crontab -e
# add:
0 2 * * * /usr/bin/python3 /path/to/backup.py --config /path/to/backup_config.json
```

**Windows (Task Scheduler)**:
Create a Basic Task -> Trigger: Daily -> Action: Start a program ->
`python.exe` with arguments `backup.py --config backup_config.json`.

## Why this project
This was built as a hands-on scripting exercise for a cybersecurity resume,
demonstrating:
- Automation of routine operational tasks (backup hygiene is a common SOC/
  sysadmin responsibility)
- Logging practices relevant to auditability and incident review
- Safe file-handling patterns (path validation, error handling per-folder
  so one failure doesn't kill the whole run)
- CLI tool design with `argparse` and config-driven execution suitable for
  scheduled/unattended jobs

## Possible extensions
- Encrypt archives with a password (e.g., via `pyzipper`) to demonstrate
  data-at-rest protection
- SHA-256 hash each archive and log the hash, for integrity verification
- Send a Slack/email alert on backup failure
- Upload completed archives to S3 or another remote store
