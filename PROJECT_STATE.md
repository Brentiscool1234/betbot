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

## Prospective results and source-sample update

Owner confirmed paid USD 30/month odds plan and deployed OVH VPS: user-provided
logs show successful 20-event collection, healthy check and enabled startup/timer.
This is evidence of initial remote operation; direct SSH/reboot/continuous-day
verification has not been performed by this agent. Backups/notification delivery
remain open.

Added final-score adapter using existing Odds API daysFrom=3 endpoint. Completed
results only; observed availability prevents backdating. Shared lock, persistent
budget, dataset version and replay protect overlap/recovery. --with-results enables
six-hour result polling and results freshness checks. Revised service caps combined
usage at 60/day, 1,500/month within owner-confirmed 20k tier; pilot odds cadence
retained. No new subscription purchase. User must pull/install the update on VPS.

25 tests pass. Live result check stored 4 completed EPL results, cost 2 credits,
quota remaining 19,730. This workspace's scores are prospective and separate from
the 2024 historical dataset. Scores do not supply shots/xG or historical statistics.

Sportmonks current pricing/terms/demo reviewed; request for 5–10 licensed 2024/25
matches, timestamp/revision evidence and exact costs prepared in
 docs/PROVIDER_SAMPLE_REQUEST.md. Request not sent and no trial activated. Provider
credentials/contact response are needed for a licensed historical sample; public
schema demo is insufficient for timestamp acceptance. Phase 1 remains incomplete.

## Experimental prediction/tracker update

Owner explicitly requested formula implementation and match-following guidance.
Experimental independent-Poisson venue model and terminal/scheduled paper tracker
added before full Phase 1 acceptance under that instruction. No real-money staking
or bet-placement integration. Minimum history 50 league results/five home-away
venue results per relevant team; current four observed results yield insufficient
data. Two fresh bookmakers required. Freeze one experimental decision per match,
including no-paper-bet, and append result settlement/Brier/log-loss/ROI separately.
Prediction records include dataset/model/policy/code hashes and source provenance.
Kickoff revisions void the paper record; latest display is not immutable history.
Tracker timer every five minutes reads local data and uses no API credits. Remote
VPS must pull/update; not installed there automatically. Calibration/chronological
market-baseline comparison, sufficient research sample and prospective acceptance
remain open. See docs/PAPER_TRACKER.md for assumptions and interpretation.

Validation for tracker update: 35 tests pass, including future odds/results,
Poisson probability mass, deterministic replay, sparse-history rejection, frozen
decisions, settlement and kickoff-change voiding. Live local scan follows all 20
upcoming events and correctly produces no predictions with only four results.
Installer shell syntax and all five systemd unit checks pass. Paper evaluation
records market-consensus Brier/log-loss alongside the model; no skill claimed.

## Free results bootstrap

Owner requested obtaining historical results and is open to a useful paid source.
Found OpenFootball football.json CC0 dataset; no purchase/token required. Importer
pins revision e6744429ee395bc86f247348c6184bb08d4eb361 and archives raw responses,
licence/checksums and actual receipt. Adds 380+353+45=778 completed results from
2024/25, 2025/26, partial 2026/27 to prospective dataset only; before-receipt
historical predictions cannot access them. 100/100 historical fixture kickoff
cross-checks agree after source London-time interpretation. No scores cross-audit
or publication proof inferred from that match check.

39 tests pass including source names/timezone, future-score rejection, ambiguous/
invalid/duplicate protection, mapping, conflicts and model event deduplication.
Repeated cached import yielded the same dataset version. Local enriched tracker
has enough history for 16/20 upcoming fixtures, four insufficient. No paper
candidates frozen yet (fixtures are outside the <=24h window). No profitability
claim. The current source coverage is partial and lacks statistics/xG/squads.
Model v2 adds cross-source event deduplication/conflict exclusion. User must pull,
install and run bootstrap on VPS. No direct remote bootstrap has been performed.
Source decision/report and exact commands: docs/RESULTS_BOOTSTRAP.md.

Final bootstrap/tracker validation: 40 tests pass; an additional horizon test
prevents displaying paper candidates outside the frozen <=24h decision window.

Tracker display update: paper selections now name the team/outcome, show the
estimated outcome probability explicitly as uncalibrated, and retain quoted odds,
bookmaker and one simulated unit. No-bet decisions show NO BET (paper). This is
a presentation change; model probabilities and frozen decision rules unchanged.

## Browser GUI — 2026-10-14

Owner requested a proper GUI. Added responsive browser match desk, probability
bars, searchable/sortable paper-bet/no-bet/data-needed cards, reasoning dialog,
performance and data-status views. Reads actual tracker/status/results/budget and
bootstrap files through a read-only loopback server; no additional API calls.
Explicit experimental/uncalibrated labels, frozen timestamps and disconnected/
stale indicators retained. Optional local JSON import is labelled a snapshot.

edge-gui.service starts on reboot, binds only127.0.0.1:8765 and uses SSH forwarding
for browser access. No public port, extra hosting bill or remote credential sharing
needed. Installer copies GUI HTML and enables the service. Remote VPS still needs
user pull/install and local tunnel commands from docs/GUI.md. No direct SSH agent
access has been established.

44 tests pass including HTTP/API, empty/malformed report, Host/path protection and
read-only behavior. JS syntax, shell syntax and six systemd units pass. Browser
visual QA unavailable; Sites helpers unavailable, so no hosted Site was registered
or published. Existing VPS interface is the delivered GUI.

GUI HEAD fix: user verified edge-gui.service active but curl -I returned501
because HEAD was unimplemented. Added HEAD support matching GET headers without
body, retaining Host/security checks. This diagnostic error does not establish
that the browser GET or SSH tunnel failed. Focused GUI tests pass.

## Manual data acquisition from GUI

Owner asked for a function that goes looking for data when no bets are shown.
Added explicit Refresh data action separate from Reload view. Asynchronous bounded
job fetches new odds/recent completed scores, resolves latest OpenFootball revision,
rechecks CC0/imports observed history, then recomputes tracker. Shared budgets and
collector locks remain; manual cooldown 5min/process lock prevent duplicate jobs.
Three odds-provider credits estimated per complete refresh. No arbitrary scraper,
paid signup, bet placement or rule override. Historical timestamps never backdated.

GUI service now receives existing API envfile and can write only data directory
under ProtectSystem strict. POST action requires local Host/same-origin header,
CSRF nonce, exact JSON action; browser never receives API credentials. Interrupted
jobs recovered/reported. GUI shows progress/partial failures and next paper window.
50 tests pass; JS syntax, shell and GUI unit checks pass. Remote VPS requires
pull/install and browser reload. Browser visual QA still unavailable here.

Live end-to-end manual refresh verified: job completed, current odds and four
recent results collected, latest CC0 revision checked with 778 cached results
imported/replayed, and tracker recomputed. Existing budget/quota accounting used.

## Automatic consistency and input-coverage report

Owner requests consistently enough data and authorizes up to EUR35/month extra
for a results/statistics source. Added daily latest-CC0 history service/timer,
reboot persistence and bounded retries; history success/failure/staleness in health
and GUI. Tracker writes coverage.json with venue/league deficits and latest known
result ages; GUI lists missing venue samples. No rule weakening or cross-league
score substitution. Existing odds/results schedules and budget caps unchanged.

54 tests now pass (new history overlap, persistent success/failure and coverage
checks). Live history update succeeded with 778 cached results, 16/20 ready.
Hull needs2away/3home, Coventry2home/2away. No guarantee community files cover all
played games or create historical EPL experience for promoted teams. Notifications
and off-server backups remain unresolved. Remote user must pull/install.

Paid candidates reviewed: API-Football Pro USD19/month, free restricted-season
sample account, public terms do not grant third-party commercial rights; account
sample, retention/use-rights and final <=EUR35 checkout total need verification.
Sportmonks EUR29 before tax may exceed cap (e.g.35.09at21%VAT). No new provider
connected, no account/trial/payment activated. Next: user-owned free provider
account/sample, then reviewed adapter. See docs/CONSISTENT_DATA.md.

## Remove artificial cutoff under owner instruction

Owner explicitly rejects the24h restriction. Paper policy v2 now evaluates all
upcoming fixtures once adequate observed history and current confirmed quotes
exist. Thresholds/history/bookmaker requirements retained. Freshness uses actual
quote availability<=90min; unchanged but freshly confirmed prices are usable,
with price-update timestamp preserved separately.

Tracker-v2 displays current assessment rather than overwriting it with an old
frozen decision. Distinct input/decision assessments immutable; first qualifying
candidate alone receives a frozen simulated stake. A previous no-bet cannot block
later candidates. Separate paper-v2.sqlite preserves old paper.sqlite/v1 records
and independently settles both policy cohorts. GUI shows original paper timestamp/
selection separately and removes cutoff copy. Current results are unvalidated
paper candidates, not real-money stakes or confidence of profit.

57 tests pass including early candidates, no-bet to candidate, changed prices
without frozen overwrite and quote receipt/change distinction. Owner policy change
registered before live v2 acquisition. VPS requires usual pull/install/reload.

Live v2 acquisition completed successfully: 12 experimental paper candidates,
4 insufficient-history fixtures and 4 no-value decisions. No timing-gate decisions
remain. This verifies behavior only, not accuracy/calibration/profitability.

## Substantive model research

Owner asks for original high-quality model/formula. Primary literature searched:
Dixon-Coles, dynamic bivariate strengths, hierarchical overshrinkage, odds-based
ratings and logarithmic model/market pooling. Global novelty/performance cannot
be promised. Quarantined dynamic opponent-adjusted learner + low-score correction,
three adaptation scenarios, validation temperature scaling/ensemble implemented.
Custom conservative market-residual/history/disagreement gate is research-only.

Registered split/trials BEFORE comparison:203initial training,177validation,
353chronological2025/26test events, entire-day forecasts before updates. Latest
corrected public records lack historical publication evidence: retrospective
method study NOT verified PIT/backtest/lockbox; production availability unchanged.

Result on325common supportedmatches: candidate logloss1.022883 vs current1.019944,
Brier.613178 vs .611406; paired date-block approximate95% loss-difference interval
[-.015088,+.025361]. Candidate slightly worse, no reliable improvement. Acrossall
353candidatebeatsleague-only1.060533 with1.016824, not market superiority. No suitable
held-out-market quotes, ROI orCLV evaluated. Failed superiority attempt retained.
Active GUI/model unchanged. Report: docs/MODEL_RESEARCH.md; raw/private experiment
results data/research/dynamic-v1/report.json. Research code requires no paid API.
Five new research tests pass: probability/dependence, opponent learning, clock
order/decay, unknown-history residualgate and future-label/calibration isolation.

## Direct market research benchmark

Registered and acquired a bounded historical2025odds sample using existing plan:
13weekly snapshots/130credits,100unique result-matched fixtures. Candidate trained
only from corrected event dates at least3calendar days before each snapshot;
this is hypothetical publication, not production backdating or verifiedPIT.
Fixed validation-derived calibration/weights/residual gate, no test tuning.
Market logloss.952386 vs dynamic.970918 vs fixed residualproposal.949729.
Proposal improvement tiny .002657; approximate95%paired date-block interval
[-.007498,+.002688] crosses0. No proven edge, confidence or ROI. Source horizons
7.07–415.07h; sample incomplete/inspected. Cached replay0calls; charges130retained.
Active model not replaced. Content-addressed experiment reports and all failures
preserved. Six research tests now pass incl bounded research request protection.

Final research verification: 63 total tests pass; comparison/market cached replays
reproduce scores with zero new API calls, research charged/reserved130credits.
Source/code/parent-report hashes and content-addressed versions retained.
