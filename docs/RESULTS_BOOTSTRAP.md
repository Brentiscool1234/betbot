# Free EPL results bootstrap — 2026-10-13

Source: https://github.com/openfootball/football.json
Licence: https://github.com/openfootball/football.json/blob/master/LICENSE.md
The repository declares CC0 1.0 Universal. We verified and archive the full
licence at pinned source revision e6744429ee395bc86f247348c6184bb08d4eb361.
No account, API token, paid subscription or automated trial is required.
Source is community-maintained, not a licensed commercial provider with an SLA.
The public dedication provides a usable free basis, not a guarantee of accuracy.

## Install on the existing VPS

```sh
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
cd /opt/edge
sudo -u edge python3 -m edge.bootstrap --directory /var/lib/edge/prospective
sudo -u edge python3 -m edge.tracker --directory /var/lib/edge/prospective
```

If bootstrap reports collector busy, retry it shortly. Downloads are public and
need no API key. The importer uses the same collector lock and advances the
common immutable dataset while preserving odds cadence and freshness. Cached
pinned responses are reusable; repeating the command does not duplicate rows or
rewrite receipt timestamps. The source licence is checked on each invocation.

## Verified local import

| Source season | Completed results imported | Unfinished/missing scores skipped |
| --- | ---: | ---: |
| 2024/25 | 380 | 0 |
| 2025/26 | 353 | 27 |
| 2026/27 | 45 | 335 |

Total 778 additional results, plus four already observed through the Odds API.
The current source-season completion coverage ends at 20 September 2026 in the
pinned snapshot; the Odds API continues collecting more recent scores. There are
also gaps in 2025/26. Future/same-day source scores are never imported as completed
labels; missing times are skipped, invalid scores/ambiguous mappings rejected.
All 100 archived 2024 fixture team/date keys and kickoff times agreed with the
source after Europe/London wall-time interpretation in a separate cross-check.
This checks fixture alignment, not every final score or publication timestamp.

The local tracker now has sufficient technical sample counts for 16 of the 20
upcoming provider fixtures. Four remain insufficient because of venue history.
This count is not a prediction-success or calibration metric. Dates/coverage and
source versions vary; the VPS must perform its own import and report counts.

## Integrity and limitations

Every imported observation uses actual cached response receipt for effective,
available, observed and ingested times. No result is backdated to kickoff or a
past source publication. Thus these observations can support forward paper
predictions, but historical predictions made before receipt cannot use them.
The 2024 historical odds-only database is left unchanged; full historical Phase 1
acceptance and publication-proof/statistics requirements remain incomplete.

Archive envelope includes pinned source URL/revision, full licence, raw response,
receipt and SHA-256 content identity. Cross-provider names use an explicit alias
mapping (e.g. AFC Bournemouth/Bournemouth); fixtures map by teams and London
calendar date. Known provider IDs/kickoffs are preserved. Ambiguity stops import.
For unmapped fixtures, stable IDs hash season/teams/date. Source time is interpreted
as Europe/London, with that basis retained; it is not invented UTC source evidence.

Existing provider final-score disagreement causes the bootstrap fixture/result
to be skipped and counted as a conflict. Model v2 also deduplicates different
IDs for the same team/date event and excludes conflicting scores. Duplicate source
rows and invalid scores are rejected. No silent fuzzy team-name matching.

There are no shots, xG, lineups or injury statistics. Poisson independence, small
venue samples, changing squads and older team history remain material model limits.
No real-money readiness, calibrated probabilities or profitability is established.
The tracker can calculate probabilities sooner; paper candidates still require
fresh quotes, a <=24h window and the frozen exploratory rule. It may correctly
show NO PAPER BET despite having a model prediction.

## Paid provider decision

The owner is open to a subscription if useful. Public Sportmonks starter pricing
is EUR 29/month before applicable VAT, with trial auto-billing and separate extras.
No subscription/trial or support contact has been activated. The prepared sample
request remains appropriate for shots/statistics, verified revision/publication
history and exact storage/model-use rights. Choose a paid source after evaluating
those requirements and the extra monthly budget; no purchase is needed for this
initial forward goals-based baseline.
