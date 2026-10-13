# Persistent collection and VPS setup

Recommended host: small VPS with Ubuntu 24.04, Python 3.12+, persistent disk,
clock synchronization and private backups. The workspace watcher only runs while
this task is active; it does not establish unattended coverage between tasks.
No external host or notification delivery is currently configured.

The included service runs as user edge, restarts after failure/reboot and retains
records in /var/lib/edge/prospective. Root-owned source goes in /opt/edge. A health
timer checks freshness, budget pause, free disk and quota every five minutes.
Failed health checks appear in systemd/journal; add an external uptime monitor
or your chosen notification sink to get alerts when you are away.

## Install on your chosen VPS

Copy the private source bundle and existing data to the server. Do not put raw
archives in a public repository. Extract source to any temporary install folder.
Run the installer once to create the root-only secret file, set the API key
locally with sudoedit, then rerun:

```sh
sudo bash configs/install-vps.sh
sudoedit /etc/edge/collector.env
sudo bash configs/install-vps.sh
sudo journalctl -u edge-collector.service --since today --no-pager
sudo systemctl start edge-health.service
sudo systemctl status edge-health.service --no-pager
```

collector.env must contain ODDS_API_KEY= followed by the actual credential,
entered on the VPS. Never paste credentials into chat. Cloud proxy placeholders
are not portable API credentials. Secret-file ownership is root and mode 600.
Installer needs root; collector does not. Installer changes only EDGE-specific
paths/user/units, and starts/restarts the EDGE service. Never run it in a generic
workspace thinking this provisions a remote host. No DNS or public ports needed.

## Migrate data

Stop the source watcher before taking a consistent SQLite backup. Prefer Python's
sqlite3.Connection.backup or stop all writers before copying the full directory
(including WAL files). Transfer privately. On the VPS:

```sh
sudo systemctl stop edge-collector.service
# Copy the complete prospective directory into /var/lib/edge/prospective.
sudo chown -R edge:edge /var/lib/edge
sudo chmod -R go-rwx /var/lib/edge
sudo systemctl start edge-collector.service
```

Preserve archives, status.json, edge.sqlite, budget.json and budget-status.json.
Do not run both a workspace and VPS watcher against the same API budget without
an explicit separate allocation. Locks only coordinate processes sharing a local
directory. Keep historical archives private in a separate research backup.

## Budget and quota

Default limits are 20 credits/day and 400/month. Change service command limits
only after owner budget approval. --force bypasses cadence, never budget limits.
Failed requests retain their estimated charge. Unknown quota headers do not prove
unlimited credits. Quota-reserve pauses persist for that UTC calendar month;
provider billing periods may differ. Verify a renewed plan and resume by updating
the ledger with the verified new quota, or wait for the next monthly reset.
Do not delete counters merely to bypass a cap. Historical research uses its own
bounded command and is not included in the prospective monthly ledger.

## Monitoring, backup and acceptance

Check journal entries and data freshness; silence alone does not prove success.
Archive checksums are validated on replay. Make a private nightly off-server
backup using a consistent database backup and test restoring it. No automatic
backup destination is configured. Set host-specific backup and notification
services after selecting the VPS provider. Check actual disk growth after one week.

Before calling deployment complete: verify first success, quota, persistent files,
health check, restart/reboot survival and a full day of uninterrupted coverage.
Preserve an incident/gap log. This cloud task cannot verify those remote checks
without access to the selected server.

## Results collection update — 2026-10-13

The owner confirmed an existing USD 30/month odds subscription and supplied VPS
logs showing odds collection and enabled health timer working. No direct SSH
connection from this workspace has been established. The revised service command
adds --with-results: final EPL scores from the last three days are polled every
six hours using the same lock, data directory, immutable dataset and budget ledger.
Unfinished/live scores are ignored. No shots, xG or lineups are collected.

Combined default limits now 60 credits/day and 1,500/month, within the confirmed
20k-credit plan, keeping pilot odds cadence. This supersedes the earlier free-tier
20/day, 400/month deployment advice. Results normally add 240 credits/30 days;
actual quota headers remain authoritative. Other API clients share your credits.
No subscription change or new invoice is incurred by this code update.

Update the existing VPS checkout without copying or showing secrets:

```sh
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
sudo journalctl -u edge-collector.service -n 15 --no-pager
sudo systemctl start edge-health.service
sudo journalctl -u edge-health.service -n 5 --no-pager
```

The existing root-only /etc/edge/collector.env is reused. Expect a results log
entry containing stream=results, status=collected and completed_events (zero can
be normal when no recent matches are covered). The results-enabled marker causes
health to flag stale/missing results as well as odds. On restart, the watcher
checks both schedules; an existing odds next_due is preserved.

Standalone check (run as the service user with the key supplied by the service,
not by copying credentials into command history): python -m edge.scores.
Do not use arbitrary directories: odds and results must share one persistent
ledger/database. Legacy collectors without --with-results remain odds-only.
