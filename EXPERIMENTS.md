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
