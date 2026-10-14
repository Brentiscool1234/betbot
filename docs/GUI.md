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

## Refresh data — 2026-10-14 update

The GUI now has two distinct buttons: Reload view reads the latest stored snapshot;
Refresh data requests new observations, then recomputes the tracker. The latter
requires the existing root-only API key file supplied to the GUI service by
systemd, plus write access to /var/lib/edge. No API key appears in browser responses.

Refresh data runs asynchronously: force-collect current EPL UK/1X2 odds, fetch
completed scores with the three-day window, resolve the latest OpenFootball Git
commit, recheck CC0 and archive/import that revision, then run the tracker. Each
stage reports success/failure; a source failure does not prevent the remaining
stages. This is acquisition from already reviewed sources, not unrestricted web
scraping, news extraction, new paid-provider signup or model validation.

Typical Odds API cost is three credits per complete refresh (one odds + two
scores); public source checks use no odds credits. Shared daily/monthly limits
still apply. A persistent process lock prevents overlapping jobs, and a five-minute
cooldown bounds manual repetitions across restarts. Existing collector locks can
cause a stage to report busy/partial; no silent budget or lock override occurs.
Interrupted refreshes are reported after restart. Original archive receipt times
are retained on replay, even if a newer source revision is later imported.

The state-changing endpoint requires same-origin loopback access, a per-server
CSRF nonce from the dashboard, JSON content and an exact action. Arbitrary routes,
URL fetching or data modifications are not exposed. Host checks and SSH tunnel
access remain. This supersedes the earlier entirely read-only description only
for the explicit bounded refresh action; no predictions or settlements are edited.

The interface shows progress, partial failures and the next 24h decision-window
opening. Fresh data does not force a paper bet or bypass a frozen earlier decision,
missing team histories, a stale quote or a signal threshold. Optional imported
JSON snapshots cannot start refresh; reconnect to the VPS first.

Apply with the usual git pull and sudo bash configs/install-vps.sh on the VPS,
then refresh the browser page. No additional subscription required. Browser visual
QA remains unverified; HTTP/security/job and JavaScript syntax checks were run.

## No artificial prediction cutoff — owner update 2026-10-14

Current GUI assesses every upcoming fixture, even several days before kickoff.
The old next-24h-window notice is removed. A fresh qualifying quote/history shows
PAPER BET immediately; data shortages/stale observations/failed thresholds retain
specific no-bet reasons. The price-update and actual availability timestamps are
shown separately in reasoning. Refresh data acquires snapshots; browser Reload
view reads the latest assessment. Neither can force a model to support a bet.

Cards show CURRENT assessments and quotes, not substituted historical paper
snapshots. Original paper decision timestamp is separate in footer/details; a
current no-bet can coexist with an original earlier paper selection. Only the
first qualifying v2 candidate receives one simulated stake. Distinct no-bet
assessments are retained for audit. Metrics cover this v2 candidate cohort; old
policy results remain separately retained and settled. No live wager placement.

The v3 reasoning panel shows market-adjusted probabilities, pure football
probabilities, original Poisson comparison, adjustment weight and scenario EV.
Percentages are estimated outcome probabilities, not validated confidence.
After deployment, hard-refresh the browser and use Refresh data for fresh odds.

## All-match prediction tracking — 2026-10-14

Every eligible model forecast now shows its most likely home/draw/away outcome,
independently of bet-value thresholds. First available prediction per match is
immutable in forecasts-v1.sqlite, including forecasts without odds. Accuracy
and probability scores settle from subsequently observed results. First forecast
with fresh eligible odds is separately frozen in simulations-v1.sqlite for a
fixed $10 simulation, even below value thresholds. Original value-filtered
paper-v3 decisions remain separate. First accuracy forecast and first priced
simulation may differ; both retain timestamps. Rescheduled fixtures are void.
No real wagers are placed; estimated probabilities remain unvalidated.

## Elo winner integration — 2026-10-14

Visible outcome prediction now uses elo-winner-v1, with Elo ratings, historical
EPL pool ranks and prior-five-match form in reasoning. Separate Elo accuracy and
$10 simulation cohorts retain previous-model records. Market-adjusted value checks
remain separate. CSV importer accepts E0 only, actual receipt timestamps, no
backdating; local four-file import contains 1200 scores without conflicts.
Audit: Elo 48.9% vs football 48.2% vs market 49.5% on 380 fixtures. RF 49.2% but
worse probability scores, research only. No proven reliability/financial edge.
See docs/ELO_WINNER.md for formulas, validation limits and deployment/import steps.
