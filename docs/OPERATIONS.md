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

Default limits are 60 credits/day and 1,500/month. Change service command limits
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
