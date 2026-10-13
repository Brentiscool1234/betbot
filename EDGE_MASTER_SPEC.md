# EDGE --- Master Project Specification

**Project:** EDGE --- Sports Market Intelligence Engine\
**Version:** 0.1 --- Proof-of-Concept Specification\
**Initial scope:** Football (soccer) → English Premier League →
pre-match 1X2 market → simulation/paper mode only\
**Primary purpose:** Research whether a point-in-time sports prediction
system can produce calibrated probabilities containing information not
already reflected in the betting market.

------------------------------------------------------------------------

## 1. Mission

Build a rigorous sports-market research engine that:

1.  Reconstructs exactly what information was available before a
    historical sporting event.
2.  Estimates Home / Draw / Away probabilities.
3.  Converts bookmaker odds into vig-adjusted market probabilities.
4.  Measures disagreement between EDGE and the market.
5.  Estimates whether EDGE's own disagreement is historically reliable.
6.  Tests all hypotheses using chronological, out-of-sample evaluation.
7.  Runs prospectively in frozen paper-prediction mode before any claim
    of useful edge is made.

The system is **not** successful merely because a historical backtest
shows profit.

The first research question is:

> Can EDGE produce well-calibrated probabilities that contain repeatable
> information not already reflected in market prices?

If the answer is no, the project must be capable of proving that clearly
and cheaply.

------------------------------------------------------------------------

## 2. Core Philosophy

EDGE must be built as a falsifiable research system, not as a system
designed to manufacture attractive backtests.

The priority order is:

1.  Point-in-time data integrity
2.  Reproducibility
3.  Probability quality and calibration
4.  Out-of-sample performance
5.  Closing-line value / market information
6.  Simulated financial performance
7.  Product UI

A beautiful dashboard with contaminated historical data is worthless.

------------------------------------------------------------------------

## 3. Non-Negotiable Engineering Rules

1.  **No future information may enter a historical prediction.**
2.  Every prediction must be reproducible from immutable/versioned
    inputs.
3.  Every dataset, feature definition, model, calibration method and
    experiment must be versioned.
4.  Failed experiments must remain recorded.
5.  Never repeatedly optimize against the final lockbox dataset.
6.  Never present training ROI as evidence that the system works.
7.  Remove bookmaker margin before comparing model and market
    probabilities.
8.  Probability calibration matters more than simple winner accuracy.
9.  Historical predictions must never be edited after their prediction
    timestamp.
10. The system must be capable of demonstrating that the hypothesis
    fails.
11. Do not silently change definitions or filters after seeing results.
12. Do not use random train/test splits for the core evaluation.
13. All feature calculations must respect event time.
14. Missing data must be represented explicitly rather than silently
    replaced with future-known values.
15. Research notebooks are exploratory only; production logic belongs in
    tested modules.

------------------------------------------------------------------------

## 4. V1 Scope

### Included

-   Sport: association football
-   Competition: English Premier League
-   Market: pre-match 1X2
-   Historical research
-   Point-in-time feature generation
-   Multiple independent probability models
-   Probability calibration
-   Model ensemble
-   Market probability engine
-   Edge calculation
-   Reliability/meta-model research
-   Walk-forward backtesting
-   Experiment registry
-   Paper prediction mode
-   Research dashboard

### Explicitly excluded from initial proof of concept

-   Real-money wagering
-   Automatic bet placement
-   In-play betting
-   Parlays/accumulators
-   Multiple sports
-   Multiple leagues unless needed for training research
-   Player props
-   LLM-based match prediction
-   Social sentiment
-   Unstructured news extraction
-   Consumer mobile application
-   Complex deep-learning models unless simpler models justify further
    work

Do not expand scope without an explicit project decision.

------------------------------------------------------------------------

## 5. High-Level Architecture

``` text
DATA SOURCES
    ↓
INGESTION
    ↓
RAW / IMMUTABLE DATA
    ↓
POINT-IN-TIME RECONSTRUCTION
    ↓
FEATURE ENGINE
    ↓
┌─────────────────────────────┐
│     PREDICTION MODELS       │
│                             │
│ Elo / rating                │
│ Poisson / xG                │
│ Gradient boosting           │
│ Bayesian (later if useful)  │
└─────────────────────────────┘
    ↓
CALIBRATION
    ↓
ENSEMBLE
    ↓
MODEL PROBABILITIES
    ↓
MARKET PROBABILITY ENGINE
    ↓
EDGE / EV CALCULATION
    ↓
RELIABILITY / META MODEL
    ↓
SIGNAL RESEARCH
    ↓
WALK-FORWARD BACKTEST
    ↓
PAPER PREDICTIONS
    ↓
RESEARCH DASHBOARD
```

Components must be modular. A data provider, model or calibration
technique should be replaceable without rewriting unrelated components.

------------------------------------------------------------------------

## 6. Phase 1 --- Historical Data Foundation

**This is the first implementation phase. Do not start ML before this
phase passes acceptance testing.**

### 6.1 Required match fields

Where legally/licensably available:

``` text
match_id
competition_id
season
kickoff_timestamp_utc
home_team_id
away_team_id
final_home_goals
final_away_goals
match_status
source
source_updated_at
ingested_at
```

### 6.2 Historical team/match statistics

Examples:

``` text
goals
xg
shots
shots_on_target
possession
corners
cards
home_away
```

Store raw source records where practical before deriving features.

### 6.3 Squad information

Where historically reliable and timestamped:

``` text
lineups
player_availability
injuries
suspensions
expected_lineups
confirmed_lineups
```

Do not use retrospectively corrected availability information unless the
system can prove it existed before the prediction timestamp.

### 6.4 Odds

For every available bookmaker snapshot:

``` text
match_id
bookmaker
market
selection
decimal_odds
odds_timestamp_utc
source
ingested_at
```

Desired research horizons include:

``` text
T-7d
T-24h
T-6h
T-1h
close
```

Actual timestamps are preferable to artificially bucketed timestamps.
Buckets can be derived later.

### 6.5 Point-in-time API

The data layer must support the conceptual operation:

``` python
get_state(match_id, as_of_timestamp)
```

It must return only information that was available at or before
`as_of_timestamp`.

This requirement is fundamental.

------------------------------------------------------------------------

## 7. Suggested Data Model

Exact implementation may change after investigation, but preserve the
concepts.

``` text
competitions
seasons
teams
players
matches

raw_match_events
raw_team_statistics
raw_player_status
raw_lineups

bookmakers
odds_snapshots

feature_snapshots
model_versions
predictions
market_probabilities
signals

experiments
backtest_runs
paper_predictions
results
```

Important timestamps should generally include both:

``` text
effective_at
observed_at / published_at
ingested_at
```

when the source makes those distinctions possible.

------------------------------------------------------------------------

## 8. Data Leakage Defense

Temporal leakage is the largest technical risk in this project.

Examples of forbidden leakage:

-   final score used indirectly in pre-match features
-   end-of-season table position used for an earlier fixture
-   injury status updated after kickoff
-   lineup data published after the prediction timestamp
-   statistics calculated using the current match
-   closing odds used as input to a T-24h prediction
-   season aggregates calculated using future matches
-   target-derived transformations fitted across the full dataset
-   calibration fitted using test-period labels
-   hyperparameters selected based on lockbox performance

### Mandatory automated leakage tests

Tests should verify at minimum:

1.  No feature row has source information newer than prediction time.
2.  Rolling statistics exclude the current and future matches.
3.  T-24h predictions cannot access T-1h or closing odds.
4.  Preprocessing/scalers/calibration are fitted only on permitted
    training data.
5.  Re-running a historical prediction from the same dataset/model
    version produces the same output.
6.  Known intentionally injected future values cause tests to fail.

Create adversarial leakage fixtures specifically to prove the guardrails
work.

------------------------------------------------------------------------

## 9. Feature Engine

Features must be deterministic, versioned and reproducible.

### 9.1 Team strength

Candidates:

``` text
elo_rating
elo_difference
rolling_points_5
rolling_points_10
rolling_goals_for
rolling_goals_against
rolling_xg
rolling_xga
rolling_xg_difference
home_strength
away_strength
opponent_adjusted_form
```

Opponent-adjusted features are preferable to naive form where justified.

### 9.2 Schedule

``` text
days_since_last_match
matches_last_7_days
matches_last_14_days
rest_difference
fixture_congestion
```

### 9.3 Squad

Only if historical timestamp quality is acceptable:

``` text
players_unavailable
likely_starters_unavailable
estimated_missing_player_value
goalkeeper_status
estimated_starting_xi_strength
```

### 9.4 Market

``` text
opening_market_probability
current_market_probability
home_price_movement
draw_price_movement
away_price_movement
bookmaker_dispersion
consensus_probability
```

Do not allow market-derived features into a supposedly
market-independent model without labeling the model accordingly.

------------------------------------------------------------------------

## 10. Market Probability Engine

For decimal odds:

``` text
raw_implied_probability = 1 / decimal_odds
```

For a three-way market, raw probabilities normally sum to more than 1
because of bookmaker margin.

Implement at least one documented vig-removal method and make the method
configurable/versioned.

Store:

``` text
raw_implied_probability
vig_adjusted_probability
consensus_probability
vig_method
market_timestamp
```

Consensus should be based on multiple eligible bookmakers when
available.

Do not assume a single bookmaker is ground truth.

------------------------------------------------------------------------

## 11. Baseline Prediction Models

Start simple.

### Model A --- Elo / rating model

Purpose:

-   transparent baseline
-   team-strength estimation
-   difficult to overcomplicate

Required output:

``` text
P(Home)
P(Draw)
P(Away)
```

### Model B --- Poisson / xG model

Estimate expected scoring rates:

``` text
lambda_home
lambda_away
```

Derive scoreline distribution and then:

``` text
P(Home)
P(Draw)
P(Away)
```

### Model C --- Gradient boosting

Preferred candidates:

-   LightGBM
-   XGBoost
-   CatBoost

Use engineered pre-match features.

Output calibrated multiclass probabilities.

### Model D --- Bayesian model

Optional after the initial baselines are operational.

Do not add complexity simply because it sounds sophisticated.

------------------------------------------------------------------------

## 12. Calibration

A probability model must be judged as a probability model.

Track:

``` text
Brier Score
Log Loss
Expected Calibration Error
Reliability / calibration curves
```

Investigate calibration techniques such as:

-   isotonic regression
-   Platt-style calibration where applicable
-   multiclass calibration approaches

Calibration models must themselves obey chronological training
boundaries.

Example expectation:

If a large set of predictions is assigned approximately 70%, the event
should occur roughly 70% of the time if the probabilities are well
calibrated.

------------------------------------------------------------------------

## 13. Ensemble

Retain all individual model predictions.

Example record:

``` text
elo_home_probability
poisson_home_probability
gbm_home_probability
bayesian_home_probability
ensemble_home_probability
```

Initial ensemble weighting should be derived from validation
performance, not arbitrary intuition.

Dynamic weighting is a later experiment.

Never overwrite constituent predictions with ensemble results.

------------------------------------------------------------------------

## 14. EDGE Calculation

For each selection:

``` text
raw_edge_pp = model_probability - market_probability
```

Example:

``` text
EDGE model: 0.64
Market:     0.55
Raw edge:   +0.09 / +9 percentage points
```

For decimal odds:

``` text
estimated_ev = (model_probability * decimal_odds) - 1
```

This is **model-estimated EV**, not proven real-world expected return.

Label it accordingly everywhere.

------------------------------------------------------------------------

## 15. Reliability / Meta Model

The primary prediction model asks:

> What is the probability of this outcome?

The reliability layer asks:

> Historically, when EDGE looked like this, how trustworthy was the
> disagreement?

Candidate inputs:

``` text
raw_edge
estimated_ev
model_disagreement
ensemble_variance
data_completeness
prediction_horizon
sample_size
market_dispersion
odds_movement
historical_calibration
team_data_depth
feature_missingness
```

Potential output:

``` text
reliability_score = 0–100
```

Do not create a cosmetic confidence score.

The score must be empirically derived and itself validated out of
sample.

If a defensible 0--100 mapping cannot be created, expose the underlying
uncertainty metrics instead.

------------------------------------------------------------------------

## 16. Chronological Evaluation

Random splitting is prohibited for the primary research result.

Use walk-forward evaluation.

Example:

``` text
TRAIN:      2020–2022
VALIDATE:   2023
TEST:       2024
```

Then:

``` text
TRAIN:      2020–2023
VALIDATE:   2024
TEST:       2025
```

Reserve the newest appropriate period as a **LOCKBOX**.

The lockbox must not be used for routine feature selection,
hyperparameter tuning or model selection.

Record every access/evaluation against it.

------------------------------------------------------------------------

## 17. Backtesting Engine

For each historical prediction timestamp:

``` text
1. Freeze simulation clock.
2. Load point-in-time state.
3. Generate permitted features.
4. Load frozen model version.
5. Produce probabilities.
6. Load odds available at that exact point in time.
7. Compute vig-adjusted market probabilities.
8. Compute model-market disagreement.
9. Compute reliability information.
10. Apply the pre-registered signal rule.
11. Record the simulated decision.
12. Advance time.
13. Resolve the outcome only after the event.
14. Compare available price with later closing market where possible.
```

### Required metrics

``` text
number_of_predictions
number_of_signals
Brier Score
Log Loss
calibration
simulated_win_rate
simulated_ROI
average_model_edge
average_estimated_EV
closing_line_value
maximum_drawdown
average_odds
sample_size
```

Performance should be segmentable by:

``` text
season
model
prediction_horizon
selection_type
odds_bucket
edge_bucket
reliability_bucket
team
data_quality
```

------------------------------------------------------------------------

## 18. Closing-Line Value

CLV is an important diagnostic because short-term realized results are
noisy.

Define the exact CLV formula in code/documentation and keep it
consistent.

Store:

``` text
available_price_at_prediction
closing_price
available_implied_probability
closing_implied_probability
clv_metric
```

Positive historical ROI without evidence that the system obtains
information ahead of the market should be treated skeptically.

CLV is not proof of profitability either; it is one diagnostic among
several.

------------------------------------------------------------------------

## 19. Experiment Registry

Every meaningful experiment must be registered.

Suggested schema:

``` text
experiment_id
created_at
created_by
hypothesis
dataset_version
feature_version
model_version
calibration_version
parameters
training_period
validation_period
test_period
prediction_horizon
signal_rule
Brier
LogLoss
CalibrationError
CLV
SimulatedROI
MaxDrawdown
SampleSize
status
notes
```

Failed experiments must not be deleted.

Where practical, register the hypothesis and intended evaluation
**before** running the final test.

------------------------------------------------------------------------

## 20. Overfitting Detection

Create diagnostics for:

-   train → validation deterioration
-   validation → test deterioration
-   parameter sensitivity
-   number of attempted experiments
-   sample size
-   season stability
-   team stability
-   edge-bucket stability
-   calibration deterioration
-   reliance on a tiny number of extreme wins
-   feature importance instability

A model such as:

``` text
Training ROI:    +30%
Validation ROI:  +14%
Test ROI:         -4%
```

must be treated as failed/overfit unless a legitimate pre-existing
explanation exists.

Do not rationalize failure after observing the result.

------------------------------------------------------------------------

## 21. Paper Prediction Mode

After a candidate model and signal policy pass historical gates:

1.  Freeze code.
2.  Freeze feature definitions.
3.  Freeze model weights.
4.  Freeze signal rules.
5.  Run prospectively.
6.  Timestamp every prediction.
7.  Never edit predictions after publication/storage.

Store:

``` text
prediction_id
match_id
prediction_timestamp
model_version
dataset_version
probabilities
available_odds
market_probabilities
raw_edge
estimated_ev
reliability
signal_decision
closing_odds
result
```

Recommended initial prospective evaluation window: approximately 8--12
weeks, subject to sample-size requirements.

The objective is not to force a positive result. It is to see whether
historical findings survive reality.

------------------------------------------------------------------------

## 22. Dashboard --- Later Phase

Do not prioritize this before the research engine works.

### Match view

Example:

``` text
Arsenal vs Chelsea

Model:
Home 63.4%
Draw 21.0%
Away 15.6%

Market:
Home 55.1%
Draw 25.0%
Away 19.9%

Raw home edge:
+8.3pp

Reliability:
89/100

Model agreement:
4/5

Data quality:
98/100

Status:
RESEARCH SIGNAL
```

All displayed numbers must be traceable to stored records.

### Research dashboard

Include:

``` text
cumulative simulated P/L
CLV over time
Brier Score over time
Log Loss
calibration plots
drawdown
edge-bucket performance
reliability-bucket performance
model comparison
season comparison
experiment comparison
sample sizes
```

Always distinguish:

``` text
TRAIN
VALIDATION
TEST
LOCKBOX
PAPER/LIVE
```

Never blend them into one attractive headline number.

------------------------------------------------------------------------

## 23. AI / LLM Layer --- Phase 2 Only

Do not use an LLM as the primary probability engine in V1.

A later AI layer may process timestamped unstructured information such
as:

``` text
injury reports
suspensions
press conferences
rotation comments
fitness updates
travel disruption
weather reports
```

The AI should convert source material into structured candidate
observations.

Example:

``` json
{
  "player_id": "example",
  "status": "doubtful",
  "estimated_start_probability": 0.25,
  "source_timestamp": "2026-10-07T10:30:00Z",
  "source_confidence": 0.91
}
```

Every derived observation must retain provenance and publication time.

The effect of AI-derived features must be tested as a separate
experiment against the structured-data baseline.

------------------------------------------------------------------------

## 24. Suggested Technology

The team may propose alternatives.

Reasonable initial stack:

``` text
Python
FastAPI

PostgreSQL
TimescaleDB optional

Polars and/or Pandas
DuckDB for research workloads where useful
NumPy
scikit-learn
LightGBM / XGBoost / CatBoost

MLflow or equivalent experiment/model tracking
Optuna only with strict validation boundaries

Docker

React / Next.js for later dashboard
```

Infrastructure should remain simple until scale requires otherwise.

------------------------------------------------------------------------

## 25. Suggested Repository Layout

``` text
edge/
├── AGENTS.md
├── README.md
├── EDGE_MASTER_SPEC.md
├── PROJECT_STATE.md
├── DECISIONS.md
├── EXPERIMENTS.md
│
├── configs/
├── ingestion/
│   ├── fixtures/
│   ├── statistics/
│   ├── odds/
│   ├── injuries/
│   └── lineups/
│
├── database/
├── point_in_time/
│
├── features/
│   ├── team_strength.py
│   ├── form.py
│   ├── xg.py
│   ├── schedule.py
│   ├── squad.py
│   └── market.py
│
├── models/
│   ├── elo/
│   ├── poisson/
│   ├── gradient_boost/
│   ├── bayesian/
│   └── ensemble/
│
├── calibration/
├── market/
├── reliability/
├── backtesting/
├── experiments/
├── paper/
├── api/
├── dashboard/
├── notebooks/
└── tests/
```

------------------------------------------------------------------------

## 26. Project Documentation Files

### `AGENTS.md`

Contains permanent instructions for coding agents:

-   read this specification before major changes
-   preserve point-in-time integrity
-   never weaken leakage tests merely to make tests pass
-   add tests for every important data transformation
-   document assumptions
-   do not silently expand scope
-   do not claim model success from training results
-   update project state after completed milestones

### `PROJECT_STATE.md`

Maintain:

``` text
Current phase
Completed components
In-progress work
Known bugs
Known data-quality problems
Current model versions
Current dataset version
Next approved tasks
Blocked decisions
```

### `DECISIONS.md`

Architecture decision log.

Each entry:

``` text
Date
Decision
Alternatives considered
Reason
Consequences
```

### `EXPERIMENTS.md`

Human-readable index of experiments in addition to the machine-readable
experiment registry.

Never rewrite history to remove failed experiments.

------------------------------------------------------------------------

## 27. Development Milestones

Indicative only; data availability may materially change timing.

### Milestone 0 --- Investigation

-   Confirm data providers.
-   Confirm licensing.
-   Confirm historical timestamp depth.
-   Confirm odds history availability.
-   Document costs and limitations.
-   Identify fields that cannot reliably be reconstructed historically.

**Deliverable:** data feasibility report.

### Milestone 1 --- Point-in-Time Data

-   Database
-   ingestion
-   EPL fixtures/results
-   timestamped odds
-   historical statistics
-   point-in-time query
-   leakage test suite

**Deliverable:** reproducible historical dataset.

### Milestone 2 --- Baselines

-   Elo
-   Poisson
-   market baseline
-   probability evaluation

**Deliverable:** baseline research report.

### Milestone 3 --- ML

-   feature engine
-   gradient boosting
-   calibration
-   chronological validation

**Deliverable:** model comparison report.

### Milestone 4 --- Ensemble + Edge

-   ensemble
-   market consensus
-   edge/EV engine

**Deliverable:** model-vs-market report.

### Milestone 5 --- Backtesting

-   walk-forward simulator
-   CLV
-   ROI
-   drawdown
-   segmentation

**Deliverable:** untouched-test report.

### Milestone 6 --- Reliability Research

-   meta-features
-   reliability model
-   out-of-sample validation

**Deliverable:** evidence showing whether reliability filtering adds
genuine value.

### Milestone 7 --- Paper Mode

-   frozen model
-   automated pre-match predictions
-   immutable logging
-   closing odds/results collection

**Deliverable:** prospective paper record.

### Milestone 8 --- Product Layer

Only after research gates justify continuation.

------------------------------------------------------------------------

## 28. Go / No-Go Gates

### Gate 1 --- Data integrity

Can historical state be reconstructed reliably?

If **NO:** stop or change data strategy.

### Gate 2 --- Probability quality

Do models produce useful, reasonably calibrated probabilities on unseen
periods?

If **NO:** redesign or stop.

### Gate 3 --- Incremental information

Is there credible evidence the model adds information beyond the market
baseline?

If **NO:** stop before building a consumer product.

### Gate 4 --- Out-of-sample robustness

Does the effect survive untouched chronological data?

If **NO:** reject the hypothesis/model.

### Gate 5 --- Prospective validation

Does a frozen version retain useful calibration/market information in
paper mode?

If **NO:** do not productize the claimed edge.

Only after passing these gates should significant product-development
resources be committed.

------------------------------------------------------------------------

## 29. Phase 1 Acceptance Criteria

The first engineering milestone is complete only when:

1.  At least 100 historical EPL matches can be reconstructed for
    demonstration.
2.  Each demonstration match has a stable unique identifier.
3.  Odds snapshots retain their actual timestamps.
4.  `get_state(match_id, timestamp)` or equivalent works.
5.  Features generated at T-24h cannot access later source records.
6.  Rolling features cannot access the current/future match.
7.  The same dataset version + code version + timestamp reproduces the
    same state.
8.  Automated leakage tests exist.
9.  At least one adversarial leakage test deliberately injects future
    data and proves the system rejects/ignores it.
10. Data provenance is documented.
11. Missing-data behavior is documented.
12. A short data-quality report lists known limitations.

Do not proceed to complex ML simply because data has been downloaded.

------------------------------------------------------------------------

## 30. First Codex Assignment

**Do not build the full application.**

Start with Milestone 0 and Milestone 1 only.

### Task

1.  Read `EDGE_MASTER_SPEC.md` completely.
2.  Create or inspect the repository structure.
3.  Produce a concise technical plan for the point-in-time data
    architecture.
4.  Identify assumptions, data-provider dependencies, licensing risks
    and fields that may be impossible to reconstruct historically.
5.  Propose the database schema.
6.  Propose the timestamp/provenance strategy.
7.  Define the leakage-test strategy.
8.  Do not begin prediction-model development yet.
9.  After the plan is approved, implement the minimum data pipeline
    required to reconstruct at least 100 historical EPL matches at
    specified pre-match timestamps.
10. Add automated tests proving later information cannot leak backward.

### Definition of done

The project must be able to answer:

> "Given match X and timestamp T before kickoff, reconstruct the data
> state that EDGE was legally allowed to know at T."

and provide provenance for the returned information.

If that cannot be demonstrated reliably, stop and report the blockers
rather than faking completeness.

------------------------------------------------------------------------

## 31. Instructions to Coding Agents

When working on EDGE:

-   Treat this document as the product/research source of truth unless a
    later recorded decision explicitly supersedes it.
-   Challenge assumptions when they threaten validity.
-   Prefer boring, testable engineering over impressive complexity.
-   Never optimize a metric by weakening data-integrity constraints.
-   Never introduce a future-known field into historical features.
-   State uncertainty rather than inventing data.
-   Keep changes small and reviewable.
-   Add tests before/with critical transformations.
-   Preserve raw data wherever practical.
-   Make derived data reproducible.
-   Use UTC internally unless there is a documented reason not to.
-   Pin/version important dependencies and schemas.
-   Log model and dataset versions with every prediction.
-   Treat unexpectedly strong historical performance as suspicious until
    independently verified.
-   If a result looks too good to be true, actively search for leakage
    before celebrating it.

------------------------------------------------------------------------

## 32. Ultimate Success Criterion

EDGE is not successful because it has:

-   a sophisticated model,
-   a high historical win rate,
-   an attractive dashboard,
-   an AI explanation,
-   or a profitable-looking training backtest.

EDGE succeeds only if rigorous chronological and prospective testing
provides credible evidence that its probability estimates contain
repeatable information beyond the market baseline.

The research process is allowed to conclude that no such edge exists.

That outcome is preferable to shipping a false one.
