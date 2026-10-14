# Experiments

No prediction experiments registered. Phase 1 is incomplete. Prior conversation
asserted tests/data existed but they were not persisted in the available checkout;
2026-10-13 restoration and current report establish the available state.
All failed future experiments must be retained; final lockbox access must be logged.

## poisson-venue-v1 / paper-rule-v1 — registered 2026-10-13

Status: implemented, unvalidated; no real-data predictions yet due to sparse history.
Hypothesis: venue-smoothed independent Poisson probabilities may add information
over proportional-vig market consensus. Scope: prospective EPL 1X2, paper only.
Parameters: min league 50, min relevant team venue 5, team window 20, prior 5;
EV >=5%, edge >=3pp, two quotes within90min, first eligible decision within24h,
one simulated unit and one decision per match. Code/config/dataset hashes are
recorded with predictions. No threshold tuning on future results authorized.
Compare model and recorded market Brier/log loss; log every eligible no-bet and
candidate. Kickoff revisions void paper records. Synthetic tests prove technical
behavior only. Prospectively collect 8–12 weeks after sufficient input history,
then review sample size/calibration. No untouched historical test/lockbox defined
for this prototype; no model-success claim.

2026-10-13 model version poisson-venue-v2 adds event deduplication and conflict
exclusion for the CC0 forward bootstrap. Frozen signal thresholds unchanged;
no real-data forecasts settled or rule tuned. Input history now contains 778
additional results available from receipt onward. Archive/source/code/version
hashes remain part of each future prediction. Community coverage gaps and
unvalidated/calibration limits remain. No historical backtest using backdated labels.

## paper-rule-v2 — owner-authorized timing change 2026-10-14

Owner explicitly removed the arbitrary 24-hour gate. Any future fixture with
adequate point-in-time history and freshly confirmed complete quotes is evaluated.
Thresholds unchanged: >=5% model-estimated EV and >=3pp market disagreement,
two bookmakers, one simulated unit. Quote freshness uses evidenced availability
within90min, retaining actual bookmaker update time separately. Price unchanged
does not imply quote unobserved. No post-outcome threshold tuning performed.
Display is always current assessment; all distinct input/decision assessments
are immutable. Freeze only first qualifying paper candidate per match in separate
paper-v2.sqlite. Earlier non-bet assessments do not permanently prevent a later
candidate. Recorded stake/quote is never changed by subsequent display updates.
Old paper.sqlite remains a separate policy cohort and settles independently.
No real-money readiness, calibration or profit claim. Code/model/dataset/policy
hashes remain recorded. This rule change precedes live acquisition under v2.

## dynamic-opponent-research-v1 — registered before comparison 2026-10-14

Owner requests substantive original model research, superseding earlier restriction
on bounded experimental model research. No promise of novelty/profit or replacement
of active v2. Investigate online opponent-adjusted attack/defence, time decay and
Dixon-Coles low-score dependence; existing literature explicitly acknowledged.
Three configurations only: learning rates .01/.03/.06 with shrinkage half-lives
365/180/90 days. First 200 completed2024/25 matches initial training; remaining
2024/25 validation; all353 available2025/26 matches chronological test. No2026/27
outcome evaluations. Validation chooses temperature from .8/1/1.2/1.4 and derives
ensemble weights exp(-validation logloss). Record all attempts; no ROI tuning.

Data was observed in2026. This is a quarantined retrospective method comparison
on latest corrected community results, NOT verified historical point-in-time or
an untouched final lockbox. All same-day forecasts precede updates; no result of
the forecast event enters its state. Prior venue Poisson and league-only baselines
use identical temporal training boundaries. Primary metric log loss, secondary
Brier. Bootstrap uncertainty by blocks of consecutive matchdays, fixed seed.
Declare failures. Historical market-odds coverage is insufficient for this held-out
season; no market incremental-information or profitable-betting claim possible.

Proposed prospective research layer: conservative log-probability residual against
actual market consensus, capped with model-disagreement and team-depth shrinkage.
Not a calibrated posterior/credible confidence interval. Unknown team history
makes market-residual weight zero. Strict positive model-estimated EV must survive
all ensemble members for a robust research signal. No active GUI/signals replaced
until out-of-sample calibration, market comparison and prospective evidence justify.

### dynamic-opponent-research-v1 result — retain failed superiority attempt

203train/177validation/353test; common venue-supported325. Candidate logloss
1.022883 vs venue1.019944, Brier.613178 vs .611406; bootstrap loss-difference95%
[-.015088,+.025361]. No superiority established; NOT promoted. Acrossall353,
logloss1.016824 vs league-only1.060533 does not establish market edge. T=.8for all
three, weights .324240/.336538/.339223. No test-market snapshots, CLV or ROI.
Source corrected/observed2026: retrospective methods evidence only, not PIT.
Report includes all12validation attempts; no further tuning against inspectedtest.

## retrospective-market-study-v1 — registered before odds acquisition

Fixed already-inspected candidate/settings; no post-test tuning. Acquire weekly EPL
UK1X2 historical snapshots from2025-08-08T12Z, at most20requests/approx200credits,
stop at100result-matched unique fixtures. Freeze each match's first complete
available quote, exclude exchanges. Match by audited aliases/teams/Londondate,
reject ambiguity. Model uses corrected results only from dates at least3calendar
days before snapshot (conservative publication assumption, NOT source evidence).
Calibration/ensemble weights fixed from2024validation. Compare dynamic candidate,
current venue baseline (where supported), market consensus and fixed research
residual proposal on identical samples. Report matched sample/quote-age/horizons;
no selection on wins/ROI and no ROI claim. This reuses inspected result dates, so
is exploratory retrospective market benchmarking, NOT an untouched lockbox or
verified PIT. Price snapshot times are provider evidence; results availability
is assumed in this separate study and never backdated in production.

### retrospective-market-study-v1 result

100mapped fixtures from13snapshots,130credits. Candidate logloss .970918, market
.952386, fixed residual proposal .949729. Proposal-minus-market approximate95%
paired date-block interval[-.007498,+.002688]; no reliable superiority. On73common
venue matches, venue.980986 / candidate.975247 / market.965486 / proposal.962568.
Horizon7.07–415.07h, maximum sampled update-age.089h. No ROI/CLV/execution claim.
Historical result publication is an assumption, not evidence; exploratory study
only. Fixed hypothesis retained, no tuning on these outcomes. Raw archives,
source hashes, charge ledger and content-addressed reports kept privately.

### prospective-market-dynamic-v1 — experimental deployment

Owner authorized prospective integration on 2026-10-14. Freeze live_config.json
settings from the prior registered research; no tuning on prospective outcomes.
Observed-only eligible results, fresh two-book consensus and original Poisson
comparison are retained. Separate first-qualifying-selection paper-v3 cohort,
with original price/model/hash frozen. Report selection bias in summary metrics.
Retrospective improvements remain inconclusive; no profitable-model claim.

## elo-winner-v1 registered 2026-10-14
Owner requests winner predictor and Elo integration. Football-data E0 CSVs:
2023/24 warmup, 2024/25 parameter selection, 2025/26 chronological audit.
2025/26 results were previously inspected in earlier experiments: this is a
retrospective audit, not a pristine lockbox. Never use target-match statistics.
Fixed grid K={20,40}, home advantage={50,80}, Davidson draw parameter={.55,.75,1}.
Blend Elo probabilities with existing pure-football forecast weights {0,.25,.5,1}.
Choose minimum validation log loss, then freeze for audit; report accuracy,
Brier/log loss and market baseline, approximate paired date-block intervals.
No odds or test labels for fitting. No revenue claim or forced team winner when
draw is most likely. Production learns only observed eligible past results.

## video-inspired-forest-v1 registered 2026-10-14
Transcript suggests Elo, prior form and tree ensembles. Football three-way
classification differs from tennis two-way. Fixed RandomForest grid 200 trees,
max_depth={3,6}, min_samples_leaf=20, random_state=20261014, temperature={.8,1,1.2}.
Features: pre-match Elo probabilities/rating difference and prior 5/10-match
points/goals for/goals against plus history depth. No target statistics, IDs or
odds inputs. Fit 2023/24; select configuration on 2024/25; refit through 2024/25,
audit 2025/26 once. Earlier Elo configuration already selected on 2024/25;
validation is development evidence, not independent proof. All models compared
on same fixtures. No RF production deployment without stronger evidence.

### Elo and forest results

{
  "elo": {
    "status": "retrospective audit, previously inspected outcomes; prospective reliability unverified",
    "source_hashes": {
      "E0 (3).csv": "b2e057b0ed959f198b0f63d2391c01239f3608e6de5db68edab3f88e04d07ff3",
      "E0 (2).csv": "d0c8ce4a96d886cf60cf101f570f4a3893844226f91c7bd769eb568c49edbfa4",
      "E0 (1).csv": "3e3a8352f9ada6789c508d6ca184424421fed56a30400904a4a327c583407e62"
    },
    "config": {
      "k": 40,
      "home_advantage": 50,
      "draw_parameter": 0.75,
      "blend_weight": 1
    },
    "validation_log_loss": 0.9953688926698301,
    "test": {
      "candidate": {
        "matches": 380,
        "accuracy": 0.48947368421052634,
        "log_loss": 1.0239778871538305,
        "brier": 0.6155179802920082
      },
      "football": {
        "matches": 380,
        "accuracy": 0.48157894736842105,
        "log_loss": 1.0473659461047817,
        "brier": 0.6292129322635722
      },
      "elo": {
        "matches": 380,
        "accuracy": 0.48947368421052634,
        "log_loss": 1.0239778871538305,
        "brier": 0.6155179802920082
      },
      "market": {
        "matches": 380,
        "accuracy": 0.49473684210526314,
        "log_loss": 1.0152523829672504,
        "brier": 0.610024736352888
      }
    },
    "candidate_minus_football_logloss_approx95_interval": [
      -0.051814112327840944,
      0.004145308966977401
    ],
    "historical_publication": "assumed by calendar ordering; exact availability not verified",
    "rank_scope": "Premier League only; lower-division strength not calibrated",
    "grid_attempts": 48
  },
  "forest": {
    "status": "retrospective exploratory audit, previously inspected outcomes",
    "source_hashes": {
      "E0 (3).csv": "b2e057b0ed959f198b0f63d2391c01239f3608e6de5db68edab3f88e04d07ff3",
      "E0 (2).csv": "d0c8ce4a96d886cf60cf101f570f4a3893844226f91c7bd769eb568c49edbfa4",
      "E0 (1).csv": "3e3a8352f9ada6789c508d6ca184424421fed56a30400904a4a327c583407e62"
    },
    "sklearn_version": "1.8.0",
    "selected_depth": 3,
    "temperature": 1.2,
    "validation_log_loss": 1.0083538292373118,
    "test": {
      "forest": {
        "matches": 380,
        "accuracy": 0.4921052631578947,
        "log_loss": 1.0300930688191527,
        "brier": 0.618443864447205
      },
      "elo": {
        "matches": 380,
        "accuracy": 0.48947368421052634,
        "log_loss": 1.0239778871538305,
        "brier": 0.6155179802920082
      },
      "market": {
        "matches": 380,
        "accuracy": 0.49473684210526314,
        "log_loss": 1.0152523829672504,
        "brier": 0.610024736352888
      }
    },
    "features": [
      "elo_home",
      "elo_draw",
      "elo_away",
      "elo_rating_difference",
      "home_5_count",
      "home_5_points",
      "home_5_goals_for",
      "home_5_goals_against",
      "away_5_count",
      "away_5_points",
      "away_5_goals_for",
      "away_5_goals_against",
      "home_10_count",
      "home_10_points",
      "home_10_goals_for",
      "home_10_goals_against",
      "away_10_count",
      "away_10_points",
      "away_10_goals_for",
      "away_10_goals_against"
    ],
    "attempts": [
      [
        1.0309587723624125,
        3,
        0.8
      ],
      [
        1.012506956213762,
        3,
        1
      ],
      [
        1.0083538292373118,
        3,
        1.2
      ],
      [
        1.0337891083935684,
        6,
        0.8
      ],
      [
        1.0135987448322141,
        6,
        1
      ],
      [
        1.0084701887196417,
        6,
        1.2
      ]
    ],
    "publication": "assumed calendar ordering, not verified PIT"
  }
}
