# Experimental Poisson match tracker

The owner explicitly requested a prediction formula and match-following guidance
on 2026-10-13. This permits implementing an experimental baseline before full
Phase 1 acceptance. It does not establish historical-data acceptance, calibration,
incremental information or readiness for real-money recommendations. No wager
placement, bankroll sizing or notification delivery is included.

## Running it

Update the existing VPS checkout, then rerun configs/install-vps.sh. The installer
adds a paper tracker timer every five minutes. The tracker reads local observations
and makes NO provider API calls, so this adds no API subscription/credit charge.

```sh
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
cd /opt/edge
sudo -u edge python3 -m edge.tracker --directory /var/lib/edge/prospective
# Keep terminal display refreshing (Ctrl+C stops only this display):
sudo -u edge python3 -m edge.tracker --directory /var/lib/edge/prospective --watch
```

Inspect background status with `sudo journalctl -u edge-tracker.service -n 30
--no-pager`. Structured latest status is /var/lib/edge/prospective/tracker.json,
mode protected by the service's 0077 umask. Immutable prediction/settlement log is
paper.sqlite; include it in consistent private backups. Trackers need no API key.
The timer refreshes from collected data; it does not make the odds stream live.
Notifications to email/Telegram/etc are not configured. Terminal output is UTC.

## Model formula and minimum history

For a match, use only completed results/fixtures actually observed before the
prediction timestamp; no later retrospective download can leak into this clock.
Exclude the target match and current/future fixture kickoffs.

League baseline = mean home goals and mean away goals across eligible EPL history.
Team rates use at most the latest 20 matches at the relevant venue. A five-match
league prior shrinks each team scoring/conceding mean:

    smoothed_mean = (team_goal_sum + 5 * relevant_league_mean) / (team_matches + 5)
    home_attack = smoothed_home_goals_for / league_home_goals
    home_defence = smoothed_home_goals_against / league_away_goals
    away_attack = smoothed_away_goals_for / league_away_goals
    away_defence = smoothed_away_goals_against / league_home_goals
    lambda_home = league_home_goals * home_attack * away_defence
    lambda_away = league_away_goals * away_attack * home_defence

Independent Poisson score distributions yield H/D/A probabilities. Tail mass is
bounded, then probabilities normalized. Model assumes independent goals and does
not account for squad changes, xG, promotions, schedule strength or score dependence.
Five-match shrinkage and minimum samples are engineering assumptions, NOT
validated confidence levels. No hyperparameter search or calibration is performed.

Require at least 50 observed league results, five home matches for the home team
and five away matches for the away team. Missing histories yield INSUFFICIENT DATA,
never invented averages/predictions. Newly promoted teams can remain unsupported.
With only four results currently verified, there are no usable model suggestions.
Building sufficient venue history may take several months; a reviewed licensed
sample could accelerate research, but not establish historical availability.

## Frozen experimental paper rule

Require at least two complete 1X2 bookmaker quotes no more than 90 minutes old.
Use each bookmaker's proportional vig removal: (1/odds) / sum(1/odds). Average
those probabilities equally for consensus; retain best observed quote per selection.
Quotes are snapshots; availability, account restrictions and actual execution are
not guaranteed. Odds collected hourly near kickoff can still be old/stale.

Model-estimated EV = p * decimal_odds - 1. Raw edge = p - consensus probability.
A paper candidate requires estimated EV >= 5% AND edge >= 3 percentage points.
Take at most one selection per match, maximizing estimated EV; one SIMULATED unit.
These are frozen exploratory thresholds, not a learned or validated betting rule.
Otherwise report NO PAPER BET. No staking optimization or real-money instruction.

Freeze the first eligible decision inside 24h before kickoff in immutable SQLite.
Store probabilities, prices, timestamp, input version/source hashes, model/policy
configuration and code fingerprints. Also freeze eligible NO PAPER BET decisions
so results cannot be cherry-picked. Never change them after later odds/results.
Display frozen timestamp/quote prominently; it is not a current execution quote.
Tracker JSON is a mutable display; authoritative predictions are immutable rows.

After a completed result becomes available, append a separate settlement. Calculate
multiclass Brier score (sum of three squared errors), log loss, the same metrics
for frozen market consensus, and simulated P/L
using recorded prices, not inferred execution. ROI uses settled paper candidates
only. A kickoff revision voids the paper decision; voids do not enter probability
metrics. Results/corrections remain observations; settlements record the first
eligible result and are not revised. No CLV claimed without a closing snapshot.
Current evaluation is prospective experimental evidence; no historical backtest,
lockbox or calibration acceptance implemented. The prospective market comparison
is descriptive only; confidence/significance and calibration remain untested.

## Interpretation

INSUFFICIENT DATA = do not act on a model prediction.
NO PAPER BET = experimental rule does not select a paper candidate.
PAPER CANDIDATE = simulate only; expected value is a model estimate, not proven.

Review calibration, chronological baseline comparison and 8–12 weeks of frozen
paper evidence with adequate sample size before considering real-money use.

## Free history bootstrap and model v2

Use `python -m edge.bootstrap` in the same prospective directory to add reviewed
CC0 EPL results as observed today. See RESULTS_BOOTSTRAP.md for VPS commands,
source coverage and limitations. Local verification now supports model outputs for
16 of 20 upcoming fixtures, while four remain insufficient. Earlier four-result
minimum-data warnings describe the pre-bootstrap state, not the enriched dataset.
Model poisson-venue-v2 deduplicates matching team/date events across source IDs
and excludes conflicting scores. Model assumptions, paper thresholds and missing
calibration remain unchanged. No before-receipt historical model inputs permitted.

Display format: PAPER BET: Team to win (or Draw) | Estimated win probability:
65.0% (uncalibrated) | Odds: 2.10 at bookmaker | 1 simulated unit. The probability
is an outcome estimate, not confidence that the bet is profitable. NO BET (paper)
retains the reason. Display formatting does not change frozen decisions.
