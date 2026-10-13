# Project state — 2026-10-13

Current phase: Milestones 0–1 and prospective odds collection. Phase 1 INCOMPLETE.
The previous conversation's uncommitted code/data were absent from both local
checkout and GitHub; rebuilt using the original EDGE_MASTER_SPEC.md.

Completed: immutable SQLite observations and content-addressed dataset membership,
explicit provider-availability/local-observation clocks, JSONL import and CLI,
rolling result features with explicit missing values, historical adapter and
adaptive locked collector, crash replay/checksums, budget reservations and health
checks, Ubuntu VPS/systemd deployment files and installer.

Validation: 20 tests pass. Replay of all 12 archives reproduced dataset hash and
all 100 historical state hashes. Observation-clock queries returned no 2024 states
from 2026 receipt. Installer shell syntax and systemd unit verification pass.
Remote installation/reboot behavior has not been tested on a VPS.

Historical dataset: 100 fixtures, 9,277 records, 12 weekly 2024 snapshots; dataset
2a01c8d921dd530778f390f9d793a8464459e5bd6e5eb7b5d757e648644f31b6.
120 API credits spent restoring history; one live request cost 1 credit. Provider
reported 19,733 remaining after the historical run. Reruns use caches/no API call.
Live dataset: 20 provider-covered upcoming events; initial success 2026-10-13
15:16:07 UTC. Check data/prospective/status.json for current runtime freshness.

Known data gaps: no historical results/statistics/publication evidence. Maximum
historical odds age at T-24h is 248.1h. No exact closing horizons. Unknown injuries,
lineups and xG remain missing. Team names require cross-provider mapping review.
Football-Data automated/data-training restrictions prohibit the proposed CSV use;
no result CSV downloaded. The Odds API terms permit retention/research and forbid
standalone redistribution. Keep raw archives private.

Costs: prospective defaults 20 credits/day, 400/calendar month; 100-credit quota
reserve. Budget pauses intentionally reduce coverage. Public odds plan is USD
30/month for 20k credits; actual account bill not verified. VPS EUR 5–10/month is
an estimate. Licensed statistics cost and owner total budget remain unknown.

No external always-on host, backup destination or alert delivery is configured.
Cloud processes do not establish continuity between tasks. VPS installer is ready
for a selected server; inject the real key there, preserve private data and verify
first success/reboot/health. See docs/OPERATIONS.md.

Model versions: none. Experiments: none. Financial edge: unproven.
Next approved work: connect selected VPS, monitor one week of usage/coverage,
obtain a licensed results/statistics sample and publication evidence, review full
Phase 1 acceptance. Do not start ML/dashboard/wagering before the gate passes.

## Low-cost pilot update
Owner requested 20/month total hosting + odds; EUR assumed. Free 500-credit odds
tier plus small VPS recommended. Defaults now 20 credits/day and 400/month; pilot
cadence 6h normally, hourly within 6h. No paid subscription cancelled or host
purchased. Owner must verify account renewal and free-tier eligibility. Existing
historical archives remain reusable; no further historical downloads proposed.
