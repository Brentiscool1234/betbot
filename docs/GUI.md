# EDGE browser GUI

A read-only dashboard served on the existing VPS, using the collector/tracker's
actual local data. No extra hosting subscription, API calls, bets, or paid data
source is introduced. It does not re-train models, place bets or change frozen
paper decisions. Browser access is through a private SSH tunnel. It binds ONLY
127.0.0.1:8765; do not open port 8765 publicly.

## Install/update — in your VPS terminal

```sh
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
sudo systemctl is-active edge-gui.service
```

Expected: active. The service automatically starts after reboot. If it fails,
inspect `sudo journalctl -u edge-gui.service -n 20 --no-pager`.
The existing API secret file remains separate; the GUI never reads it.

## Open — on YOUR COMPUTER, not inside the VPS terminal

Open a new Terminal/PowerShell window on your computer and run:

```sh
ssh -N -L 8765:127.0.0.1:8765 ubuntu@51.222.6.23
```

Use your existing SSH authentication. No output after login is normal for a
forward-only session. Leave that window open. In a browser on the same computer,
open http://localhost:8765 . Ctrl+C closes the tunnel, not the VPS services.
If your computer already uses port 8765, change the FIRST 8765 to 8766 and open
http://localhost:8766; the VPS service port remains 8765.

## Interface

- Match desk: search, sort by kickoff/model probability, and filter paper bets,
  no-bet decisions and insufficient histories. H/D/A bars show uncalibrated
  estimates; missing probabilities remain absent rather than zero.
- Match details: model versus market probabilities, expected goals, team/league
  history counts, exclusions, eligible bookmakers and frozen prediction ID/time.
- Paper results: actual stored model/market Brier/log-loss, simulated P/L/ROI and
  settled/void counts. No settled sample shows no performance claim.
- Data & status: odds/results receipt, expected cadence, provider credit balance,
  usage counters, history source and dataset version. Stale/disconnected data is
  explicitly labelled. No implied live betting price or confidence-of-profit.

The browser polls a read-only local API every 15 seconds. The underlying tracker
normally updates every five minutes; odds/results collection retains its own
cadence. Faster browser refresh does not obtain fresher bookmaker quotes. Frozen
paper decisions retain their original timestamp/quote.

Optional JSON import: Data & status > Import tracker JSON. Imported data is clearly
labelled a snapshot with no live connection; automatic API refreshing pauses until
Refresh reconnects successfully. Import processing happens only in the browser.
No user JSON file is uploaded to another service.

## Security/verification

Loopback binding, Host validation, read-only routes, no CORS, and traversal
rejection keep this service scoped to authenticated SSH/local access. No public
Internet authentication, DNS/TLS or mobile remote exposure has been provisioned.
Raw archives, credentials and environment variables are never endpoints. The
Python stdlib server is appropriate to this private single-user research use,
not a hardened public deployment.

HTTP tests verify HTML/API responses, empty/malformed-data behavior, read-only
routes and protections. JavaScript syntax and six systemd units validate. Browser
visual QA was unavailable in this environment; no screenshot or device-tested
layout is claimed. Sites publishing helpers were unavailable, so no hosted Site
was created/published; the GUI is delivered with the existing VPS application.
