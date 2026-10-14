#!/usr/bin/env bash
# Run from an extracted EDGE source bundle on your Ubuntu 24.04 VPS.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Run with sudo on the selected VPS.' >&2
  exit 1
fi
EDGE_SOURCE_DIR=$(cd -- "$(dirname -- "$0")/.." && pwd)
python3 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
if [[ ! -f /etc/edge/collector.env ]]; then
  install -d -m 700 /etc/edge
  install -m 600 /dev/null /etc/edge/collector.env
  echo 'Enter ODDS_API_KEY=your_actual_key using sudoedit /etc/edge/collector.env, then rerun.' >&2
  exit 1
fi
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/edge/collector.env')
assert p.stat().st_uid==0 and p.stat().st_mode & 0o077 == 0, 'Secret file must be owned by root with mode 600'
assert any(line.startswith('ODDS_API_KEY=') and line.split('=',1)[1].strip() for line in p.read_text().splitlines()), 'ODDS_API_KEY must be set'
PY
if ! id edge >/dev/null 2>&1; then
  useradd --system --user-group --no-create-home --shell /usr/sbin/nologin edge
fi
install -d -m 755 /opt/edge /opt/edge/edge
install -m 644 "$EDGE_SOURCE_DIR"/edge/*.py /opt/edge/edge/
install -d -m 755 /opt/edge/edge/research
install -m 644 "$EDGE_SOURCE_DIR"/edge/research/*.py /opt/edge/edge/research/
install -m 644 "$EDGE_SOURCE_DIR"/edge/research/live_config.json /opt/edge/edge/research/live_config.json
install -m 644 "$EDGE_SOURCE_DIR"/edge/elo_config.json /opt/edge/edge/elo_config.json
install -m 644 "$EDGE_SOURCE_DIR"/edge/gui.html /opt/edge/edge/gui.html
install -d -o edge -g edge -m 700 /var/lib/edge /var/lib/edge/prospective
for unit in edge-collector.service edge-health.service edge-health.timer edge-tracker.service edge-tracker.timer edge-gui.service edge-history.service edge-history.timer; do
  install -m 644 "$EDGE_SOURCE_DIR/configs/$unit" /etc/systemd/system/
done
systemd-analyze verify /etc/systemd/system/edge-collector.service /etc/systemd/system/edge-health.service /etc/systemd/system/edge-health.timer /etc/systemd/system/edge-tracker.service /etc/systemd/system/edge-tracker.timer /etc/systemd/system/edge-gui.service /etc/systemd/system/edge-history.service /etc/systemd/system/edge-history.timer
systemctl daemon-reload
systemctl enable edge-collector.service edge-health.timer edge-tracker.timer edge-gui.service edge-history.timer
systemctl restart edge-collector.service edge-health.timer edge-tracker.timer edge-gui.service edge-history.timer
systemctl --no-pager status edge-collector.service
