# Model research and first comparison — 2026-10-14

## Finding

An original implementation is not evidence of a novel scientific method or an
exploitable betting edge. Literature search found prior work covering dynamic
attack/defence ratings, low-score dependence, hierarchical shrinkage, odds-based
ratings and model/market probability pooling. The first candidate implemented here
DOES NOT demonstrate improvement over the current venue baseline on a matched
chronological test subset. It has not been promoted into the active GUI.

## Primary research reviewed

1. Dixon & Coles (1997), modelling football scores and betting-market inefficiencies.
   https://academic.oup.com/jrsssc/article-abstract/46/2/265/6990546
   Motivates recency and special treatment of low-scoring joint outcomes. It is
   established work, not a new EDGE invention or evidence about today's markets.
2. Baio & Blangiardo (2010), Bayesian hierarchical football models.
   https://discovery.ucl.ac.uk/16040/1/16040.pdf
   Discusses pooling and the risk of shrinking extreme teams too far to average.
   Our implementation does not reproduce their full posterior/mixture model.
3. Koopman & Lit (2015; 2012 preprint), dynamic bivariate Poisson forecasting.
   https://research.vu.nl/ws/files/3167073/12099.pdf
   Models changing strengths and score dependence with a state-space approach.
   Our simpler online residual updates are NOT their inference algorithm.
4. Wunderlich & Memmert (2018), betting odds rating system.
   https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0198668
   Uses betting-market forecasts as an information source. Market consensus must
   be a strong explicit benchmark, not treated as an opponent we already beat.
5. Pitcan (2026 preprint), structural forecasts versus closing prices.
   https://arxiv.org/abs/2608.11505
   Illustrates that useful probabilistic football models need not add information
   beyond prices. Recent preprint, not independent verification of our approach.

The search cannot establish nobody uses a particular combination; private models
are not searchable. No global novelty, proprietary secret or profitability claim.

## Concrete candidate implemented

The existing model compares recent venue scoring averages but not opponents.
Research candidate uses separate attack A_i and defensive weakness D_i states:

    log lambda_home(t) = mu_home(t) + A_home(t) + D_away(t)
    log lambda_away(t) = mu_away(t) + A_away(t) + D_home(t)

States decay toward zero between appearances:

    A_i(t) = 2^(-days_since_update / H) * A_i(previous)
    D_i(t) = 2^(-days_since_update / H) * D_i(previous)

After a completed match, update attack/defence from observed-goal minus
expected-goal residuals, clipped to +/-3. Team learning rate is eta/sqrt(1+n/20).
Home/away league intercepts update more slowly; intensities bounded [0.15,5] for
stability. These bounds, robust residuals and initial1.5/1.2 goal priors are
explicit engineering assumptions, not parameters discovered to be optimal.

Joint score probabilities:

    P(H=x,A=y) = Pois(x;lambda_home) * Pois(y;lambda_away) * tau(x,y)
    tau(0,0) = 1 - lambda_home*lambda_away*rho
    tau(0,1) = 1 + lambda_home*rho
    tau(1,0) = 1 + lambda_away*rho
    tau(1,1) = 1 - rho
    otherwise tau = 1

A restricted online rho update uses the low-score correction derivative,
regularized toward zero and bounded[-0.1,0]. Goal-strength updates remain robust
Poisson residual updates; this is a heuristic/quasi-likelihood learner, not exact
joint maximum likelihood or a Bayesian posterior. Probability mass normalizes;
no five-goal truncation disguises tail mass.

Three adaptation scenarios, registered before results:
eta=.01/H=365days; eta=.03/H=180days; eta=.06/H=90days.
Multiclass temperature scaling from validation probabilities:

    calibrated p_k = p_k^(1/T) / sum_j p_j^(1/T)

T chosen from .8,1,1.2,1.4 on validation only; ensemble weights proportional to
exp(-validation_log_loss). All12 attempts retained, no tuning on test ROI.

## Proposed custom market-residual research layer

This is implemented as a research-only function, NOT a deployed betting signal.
Let m be same-time vig-adjusted consensus, f the dynamic calibrated ensemble,
n the smaller team-history count, and U the largest outcome-probability range
across adaptation scenarios:

    g = 0.25 * n/(n+20) * exp(-4*U)
    r_k = clip(log(f_k/m_k), -0.5, +0.5)
    q_k = m_k * exp(g*r_k) / sum_j [m_j*exp(g*r_j)]

This is a constrained logarithmic probability pool with a history/disagreement
gate. Pooling is established; the exact chosen gate is a testable implementation
choice, not a proven novelty or learned confidence score. Unknown history gives
g=0, so the model contributes no residual information. The constants require
prospective validation and may be rejected; no suitable held-out market data is
available to fit them now. Operationally this layer is NOT active.

A conservative research-screening quantity is min_s(q_s,k*odds_k-1) across model
scenarios. It is a scenario minimum, NOT a confidence/credible interval or proof
of positive real-world EV. Disagreement and lower counts can justify abstention.
No bankroll/real-money staking or guaranteed profit is derived from it.

## Actual evaluation performed

Pinned CC0 OpenFootball source revision:
e6744429ee395bc86f247348c6184bb08d4eb361.
Initial training: first2002024/25 events extended to end of the same calendar day,
thus203matches, ending14January2025. Validation: remaining1772024/25 events.
Test: all353 completed2025/26 events available in this incomplete source snapshot.
2026/27 outcomes NOT evaluated. Forecast an entire match date before updating
from any results on that date, including the target. Test models learn from earlier
test dates as a prequential walk-forward procedure; calibration and weights frozen
from validation. No random train/test split.

IMPORTANT: these are latest corrected records downloaded in2026 with unknown
historical publication times. This is a quarantined RETROSPECTIVE METHOD STUDY,
not a verified historical point-in-time replay, untouched lockbox or profit backtest.
We did NOT change available_at in the production store to simulate earlier access.
Source dates/coverage may contain errors/gaps. Outcomes were already potentially
accessible before registration; test is temporal holdout, not a secured lockbox.

All353test events:

| Model | Log loss (lower better) | Multiclass Brier | Top-label ECE,10bins |
| --- | ---: | ---: | ---: |
| Research dynamic ensemble | 1.016824 | 0.609052 | 0.050180 |
| League-only scoring baseline | 1.060533 | 0.641773 | 0.044054 |

The current venue baseline can only predict325of those353 matches under its
history rules, so the meaningful baseline comparison uses identical325 events:

| Model | Log loss | Multiclass Brier | Top-label ECE,10bins |
| --- | ---: | ---: | ---: |
| Research dynamic ensemble | 1.022883 | 0.613178 | 0.044603 |
| Current venue baseline | 1.019944 | 0.611406 | 0.050649 |

Research minus current log loss = +0.002939 (slightly WORSE).
Paired circular block bootstrap over five consecutive match dates,500resamples,
seed20261014: approximate95% interval [-0.015088,+0.025361]. The range crosses0;
no reliable superiority shown. This interval is a dependent-sample diagnostic,
not proof of statistical significance or an uncertainty interval for a single bet.
ECE values are descriptive and unstable in samples of this size; lower ECE alone
does not override worse proper scoring-rule performance.

All validation-selected T were0.8; scenario weights .324240/.336538/.339223.
This selection sharpens forecasts and may be season-specific; no optimality claim.
All attempts/source hashes/predictions are stored privately in
 data/research/dynamic-v1/report.json. Source hashes and replay settings are retained.

At the initial353-match comparison, no suitable same-time market snapshots for
the full held-out2025/26 cohort had been collected. A subsequent100-match
exploratory market study is reported below.
The older100match weekly odds sample is NOT evidence on this test season; verified market
incremental-information, ROI, CLV, execution costs and profitability not established.

## Decision and next evidence needed

Do NOT replace the active baseline with this candidate based on these results.
Do NOT try dozens more configurations on the same inspected test and advertise
that as a discovery. Preserve this failed superiority attempt in the registry.
The existing baseline also remains unvalidated against the betting market.

The largest useful improvements are likely data and falsifiable testing:
1. Activate a reviewed <=EUR35/month results/statistics feed after account sample,
   retention/use-rights, season coverage and final price verification. No paid feed
   is currently connected; shots/xG/lineups are not fabricated or used yet.
2. Freeze a model/feature/market-residual proposal BEFORE prospective outcomes and
   collect same-time quotes, all assessments, corrections and eventual results.
3. Compare directly with vig-adjusted market on exactly the same cohorts/horizons.
4. Fit any market-residual/calibration coefficients on earlier validation ONLY;
   allow zero football weight to win if market is better. Keep a future lockbox.
5. Require calibration, paired uncertainty, adequate sample size and stability
   across periods/teams before promoting a model or claiming positive net value.

A distinct useful contribution might be disciplined residual screening with
uncertainty and availability, not a magical new score-distribution formula.
That is a research hypothesis, not a completed profitable product.

## Reproduce without changing active GUI

From repository checkout (not /opt/edge minimal service install):

    python -m edge.research.compare
    python -m unittest discover -s tests -p test_research.py -v

The research module only writes its separate data/research directory and never
imports its retrospectively ordered probabilities into active predictions.
No runtime API key or new subscription required. Archived reports and failed
experiments must not be deleted after later iterations.

## Subsequent direct market benchmark — fixed hypothesis, not a new lockbox

To replace the missing market benchmark with actual data, registered a fixed
sampling plan before acquisition: weekly UK/EPL1X2 snapshots from8August2025,
first complete quotes with at least two eligible books per mapped fixture,
stop100result-matched unique fixtures, at most20requests/approx200credits. Existing
candidate weights/temperatures and residual formula fixed; no selection on wins.
Acquired13snapshots using130credits from the existing Odds API plan. Cached replay
uses zero further credits. Separate research ledger retains charges/reservations.

Forecasts use corrected result records from calendar dates at least three days
before each snapshot. That is a conservative HYPOTHETICAL publication delay, not
proof of historical availability; no production timestamps were backdated. Prices
have actual provider snapshot and bookmaker update timestamps. This remains an
exploratory retrospective market study on inspected seasons, not verified PIT,
untouched final lockbox or evidence of tradable profit.

| Same100 fixtures and snapshot horizon | Log loss | Brier | Top-label ECE,10bins |
| --- | ---: | ---: | ---: |
| Dynamic ensemble alone | 0.970918 | 0.577314 | 0.139788 |
| Bookmaker consensus | 0.952386 | 0.561443 | 0.091841 |
| Fixed conservative residual proposal | 0.949729 | 0.559952 | 0.069029 |

Candidate-minus-market log loss +0.018532 (worse), approximate paired block95%
interval[-0.034351,+0.072377]. Proposal-minus-market -0.002657 (slightly better),
interval[-0.007498,+0.002688], crosses0. Do not sell this as proven superiority.
The relative descriptive log-loss improvement is approximately0.28%, not28%,
not28percentage points, and not expected betting ROI.

On73fixtures where the venue baseline had enough history:

| Model | Log loss | Brier |
| --- | ---: | ---: |
| Current venue baseline | 0.980986 | 0.580036 |
| Dynamic ensemble alone | 0.975247 | 0.580684 |
| Market consensus | 0.965486 | 0.570647 |
| Conservative residual proposal | 0.962568 | 0.569107 |

Snapshot-to-kickoff horizons range7.07–415.07hours. First available weekly prices
are not exactT-24h or closing odds. Maximum price-update age in this particular
sample was0.089hours; do not generalize that freshness to every provider quote.
Large horizon variation and the small sample limit what can be inferred.
No payouts, execution, CLV, market fees or taxes studied. Individual probability
ECE and scenario disagreement are not validated confidence that a bet pays.

### Research conclusion after the market test

The pure football model did not beat market probabilities in this sample. The
conservative residual formulation is a reasonable hypothesis to freeze for future
paper comparison, with market weight permitted to dominate and even reject the
football contribution. It is not yet justified as an active replacement or an
exclusive novel invention. Active GUI model remains unchanged.

Reproduce cached comparison with `python -m edge.research.market_study`. Requires
initial compare report; bounds1–100fixtures/1–20requests are enforced, new calls
reserve10credits each against a separate200-credit/day/month research ledger.
Unexpected provider cost can overshoot by one receipt; no purchase/upgrade occurs.
Registered source hashes must match. Reports are archived by content hash under
reports/ as well as the mutable latest report pointers; retain failures/replays.
