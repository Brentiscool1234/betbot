# Consistent data upkeep and provider decision — 2026-10-14

Owner allows at most EUR 35/month ADDITIONAL for results/statistics, separate from
existing USD30 odds plan and VPS. No new subscription/trial/account purchased.

## Working continuous path

Odds remain on adaptive cadence through the existing provider, completed scores
are captured every six hours with a three-day lookback, and the new history timer
checks the latest reviewed CC0 revision daily at 04:00 UTC with a small randomized
startup delay. Persistent timer catches a missed scheduled run after suspension;
service retries failures up to three starts/hour. It also runs shortly after boot.
This is 06:00 Brussels in summer / 05:00 in winter, plus up to five minutes jitter.
Public history checking uses NO odds API credits. Model/tracker updates use local
records. Existing shared credit caps and locks still apply to paid odds/results.

Failure or age >36h of automatic history success is exposed in the local health
check and GUI; notification delivery remains unconfigured. Keep VPS/clock/disk and
private backups operational. Outages longer than three days may lose scores from
the odds provider unless another source backfills them. Daily history checking
cannot force a community maintainer to publish missing scores or fix errors.

Coverage report lists each match's team venue-history shortfalls, league shortfall,
latest known result ages and model readiness. These are mechanical input gates,
not calibrated confidence or proof of complete data. Source history can be old;
squad/strength changes are not captured by this goals-only prototype.

Local verification: 778 CC0 + four provider results retained; 16/20 model-ready.
Hull away needs two more venue results, Hull home three; Coventry home/away two.
These may be actual source gaps or genuine insufficient recent EPL experience.
Do not substitute Championship goals as if they were EPL goals or lower data
minimums just to obtain a bet. Cross-league priors require a separate validated
model/data decision. Fresh coverage does not override the 24h signal window.

## Install on the existing VPS

```sh
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
sudo systemctl start edge-history.service
sudo journalctl -u edge-history.service -n 10 --no-pager
sudo systemctl list-timers edge-history.timer --no-pager
```

Reload GUI; Data & status now contains automatic history status and venue-gap
counts. Additional APIs are not provisioned or queried by this update.

## Paid-source comparison (public pages checked 2026-10-14)

API-Football: https://www.api-football.com/pricing
Pro advertised USD19/month with 7,500 requests/day and all endpoints/competitions;
free account has 100 requests/day and season restrictions. Candidate for testing
EPL fixtures/results/statistics availability before purchase. Exact account season
entitlement, total converted EUR cost/tax and quota/renewal conditions require
checkout/API verification; do not assert it fits EUR35 unconditionally.
Terms https://www.api-football.com/terms permit projects and prohibit raw resale,
but explicitly do NOT grant third-party competition commercial/publication rights.
Confirm suitability for our private immutable research/retention use and any later
public product separately; do not treat paid access as all needed rights. No
historical publication/version evidence established from these public terms.

Sportmonks: https://www.sportmonks.com/football-api/plans-pricing/
Starter advertised EUR29/month before applicable VAT, five selectable leagues,
with a paid-plan trial that converts to billing. For example 21% VAT would yield
EUR35.09, ABOVE the user's EUR35 ceiling; user's actual tax rate is not inferred.
Historical/advanced-data extras can add cost. Do not subscribe if final total
exceeds the cap. Existing sample/timestamp/retention request remains applicable.

## Next source onboarding step

Create a free API-Football account, then verify available EPL seasons and sample
fixtures before deciding on Pro. Do not send API credentials in chat. Paid data
is NOT currently connected: account credentials, sample coverage and use-rights
review are still needed for a concrete integration. No purchase/payment flow is
available or attempted from this workspace. Additional budget authorizes a bounded
provider selection, not fabricated account access or an unverified fee.

Once a source passes review: implement a names/IDs mapping with conflict tests,
private raw archives and receipt-only availability; import full EPL result seasons
and collect daily. Add fixture statistics separately with explicit source/time
provenance; do not claim the current model uses shots/lineups until tested.
Measure one week of coverage/latency/cost before expanding endpoints. Validate the
model against market baseline and frozen paper results rather than relying on
training count or high reported win probability.
