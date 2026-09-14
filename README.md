# Backup Automation Tool

A command-line Python tool that zips one or more folders into timestamped
archives, logs every operation, and prunes backups past a configurable
retention window — with scheduled, unattended execution.

## Features
- Timestamped zip archives (`foldername_YYYYMMDD_HHMMSS.zip`)
- Supports multiple source folders in a single run
- Structured logging to console + file (auditable history of every run)
- Retention policy — automatically deletes archives older than N days
- Config-file mode for scheduled/unattended runs
- Verified working scheduled execution via **cron** (see notes below)

## Usage

Direct CLI:
```bash
python3 backup.py --source ./project1 ./project2 --dest ./backups --retain-days 30
```

Config-file mode (recommended for scheduled jobs):
```bash
python3 backup.py --config backup_config.json
```

Config file format (see `backup_config.example.json`):
```json
{
  "source": ["./project_alpha_", "./project_beta"],
  "dest": "./backups",
  "retain_days": 20,
  "log_file": "backup.log"
}
```

## Scheduling it

### cron (primary method, confirmed working)
```bash
crontab -e
```
Add a line like (daily at 2 AM — adjust the Python path to match your system,
see note below):
```
0 2 * * * cd /full/path/to/backup_tool && /full/path/to/python3 backup.py --config backup_config.json >> cron_debug.log 2>&1
```

**Important — use the correct Python path.** Run `which python3` first and
use its exact output in the crontab line. cron does not use your shell's
`PATH`, so a bare `python3` or the wrong interpreter path (e.g. the system
stub at `/usr/bin/python3` when your real interpreter lives elsewhere, such
as a Homebrew or python.org install under
`/Library/Frameworks/Python.framework/...`) will fail silently. This was
the actual root cause the first time cron appeared not to work — not a
cron problem at all, but a path problem.

### macOS Calendar + Automator (working alternative)
An `.app` built in Automator (a single "Run Shell Script" action running
the same `cd && python3 backup.py ...` command) triggered by a recurring
Calendar event's **Custom → Open File** alert. Verified working on macOS
and useful as a GUI-driven alternative when a command-line scheduler is
inconvenient or blocked.

### launchd (attempted, not resolved)
A `.plist` was written for `~/Library/LaunchAgents/` following the standard
launchd job format. `launchctl bootstrap` consistently failed with
`Bootstrap failed: 5: Input/output error` — including for a bare
minimum test job (`/bin/echo hello`), even after fixing plist syntax
(validated via `plutil -lint`), file ownership, permissions, and confirming
the session was correctly attached to the console user (`stat -f "%Su"
/dev/console` matched `whoami`). Even `sudo launchctl bootstrap` did not
surface a more specific error. This points to a machine-specific launchd
job-database issue rather than anything wrong with the job definition
itself. Documented here rather than silently dropped, since the
troubleshooting process (systematically eliminating syntax, ownership,
permissions, UID scoping, and session identity as causes) is itself the
useful takeaway.

## Automation troubleshooting notes (macOS specifics)
A few macOS-specific issues came up worth knowing about in advance:

- **TCC / privacy permissions**: macOS blocks background processes
  (including cron jobs) from silently reading/writing inside protected
  folders like Desktop, Documents, and Downloads. The first sign of this
  was backups failing with no error at all. Fixed by approving the
  permission prompt when it appeared, and by adding the relevant Python
  interpreter to **System Settings → Privacy & Security → Full Disk
  Access**.
- **Wrong Python path in cron**: see the cron section above — always
  confirm with `which python3` rather than assuming `/usr/bin/python3`.
- **User vs. root crontab**: `crontab -e` and `sudo crontab -e` edit two
  entirely separate schedules. Worth checking both (`crontab -l` and
  `sudo crontab -l`) when a cron job seems to be running from nowhere or
  not running at all.
- **launchd `Input/output error`**: seen consistently across plist
  content changes, permission fixes, and even root-level invocation;
  never fully resolved on this machine. Logged here as a known dead end
  rather than a fixed bug.

## Why this project
Originally built as a hands-on scripting exercise for a cybersecurity
resume. What ended up being the more valuable part was the process of
getting reliable *scheduled* execution working across multiple OS-level
mechanisms, which mirrors real troubleshooting/root-cause-analysis work:

- Automation of a routine operational task (backup hygiene is a common
  SOC/sysadmin responsibility)
- Logging practices relevant to auditability and incident review
- Safe file-handling patterns (path validation, per-folder error handling
  so one failure doesn't kill the whole run)
- Systematic diagnosis of a black-box failure (launchd) by isolating
  variables one at a time: syntax, ownership, permissions, disabled
  state, UID scoping, session identity — a process very similar to
  incident response with limited diagnostic output
- Understanding of OS-level scheduling mechanisms and their different
  permission models (cron, launchd, GUI-triggered automation)

## Practical uses
- Snapshotting a code project before a risky refactor or rebase
- Backing up dotfiles/config files before making changes
- Archiving documents or notes on a recurring schedule
- As a base pattern for security-relevant use cases: pre-incident-response
  evidence preservation, configuration drift baselines, or log retention
  policies (with retention windows mirroring compliance-driven log
  rotation requirements)

## Current limitations / possible extensions
- No offsite/remote copy — a compromised or destroyed machine takes the
  backups with it. Could extend to upload to S3 or similar.
- No integrity verification — a SHA-256 hash of each archive, logged
  alongside it, would let you verify a backup hasn't been altered or
  corrupted.
- No encryption — sensitive folders are currently backed up in plaintext
  zips. `pyzipper` would add password-protected archives.
- No failure alerting — currently only local logging; email/Slack
  notification on failure would close the loop for truly unattended use.