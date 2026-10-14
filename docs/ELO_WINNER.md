# Experimental Elo winner predictor

The visible predicted outcome uses elo-winner-v1, independently of the existing
market-adjusted value signal. A draw can be the most likely outcome; a team is
not forced to win. Percentages are estimated outcome probabilities, not a
verified accuracy or confidence of profit. Elo ratings and prior five-match form
are shown in View reasoning. Rank means the historical observed EPL team pool,
including relegated teams, not current league-table position.

## Formula and selection

Start unseen teams at 1500. For rating difference d including home advantage,
x=10^(d/800). Davidson probabilities are home=x/Z, draw=v/Z, away=(1/x)/Z,
where Z=x+v+1/x. Update home by K*(actual-[p_home+.5*p_draw]), and away by
its negative. Actual is 1, .5, or 0 for home win, draw, or away win.
Validation selected K=40, home advantage=50, draw parameter=.75, Elo weight=1
from the preregistered 48-option Elo/blend grid. No lower-division Elo transferred:
league-strength offsets need separate evidence.

2023/24 warms up ratings; 2024/25 selects parameters; 2025/26 audits predictions
before every date's results are learned. All matches on one date are predicted
before any updates from that date. Historical exact publication times are not
verified. Outcomes had already appeared in previous research, so this is an
exploratory retrospective audit, not a pristine validation lockbox.

| Model, 380-match audit | Correct outcome | Log loss | Brier |
|---|---:|---:|---:|
| Existing pure-football model | 48.2% | 1.0474 | .6292 |
| Elo | 48.9% | 1.0240 | .6155 |
| Video-inspired random forest | 49.2% | 1.0301 | .6184 |
| Average historical odds, margin removed | 49.5% | 1.0153 | .6100 |

Approximate 95% paired five-date-block bootstrap interval for Elo minus football
log loss is [-.0518,+.0041], crossing zero. Elo did not beat the market baseline.
RF has worse probability scores despite one additional correct outcome. No
reliability or profitability established. RF remains optional research only; it
is not imported by the VPS tracker. Prior goals/form/Elo features transfer from
the tennis video; its two-outcome accuracy claims do not transfer to football.
No target-match goals, shots, winner columns, odds, or team IDs enter RF features.

To reproduce install `pip install -e '.[research]'`, then run:

```bash
python -m edge.research.elo_study 'E0 (3).csv' 'E0 (2).csv' 'E0 (1).csv'
python -m edge.research.forest_study 'E0 (3).csv' 'E0 (2).csv' 'E0 (1).csv'
```

Frozen configuration and file hashes are in edge/elo_config.json. Results,
including all failed alternatives, are summarized in EXPERIMENTS.md.

## Prospective evidence

Every eligible first Elo forecast is immutable in forecasts-v2-elo.sqlite. Its
probability scores and outcome accuracy use Elo probabilities, not the separate
market-adjusted probabilities. The first Elo forecast with fresh eligible prices
is separately frozen in simulations-v2-elo.sqlite for a $10 paper simulation.
Earlier forecasts-v1/simulations-v1 and paper-v3 remain separate and settle.
No real bets are placed. A later CSV import cannot change previously frozen
predictions. Evidence requires forecasts recorded before kickoff, subsequent
results, all losses retained, calibration versus odds baselines and enough
matches to quantify uncertainty. There is no guaranteed sample size proving
an edge; don't change settings in response to isolated wins or losses.

## Deploy and import your E0 files

First update code on the VPS:

```bash
cd ~/betbot
git pull --ff-only origin edge/restore-data-budget-20261013
sudo bash configs/install-vps.sh
mkdir -p ~/betbot/imports
```

From Windows PowerShell in the folder containing your four E0 CSVs:

```powershell
scp E0*.csv ubuntu@51.222.6.23:~/betbot/imports/
```

Then on the VPS:

```bash
sudo install -d -o edge -g edge -m 700 /var/lib/edge/imports
sudo install -o edge -g edge -m 600 ~/betbot/imports/E0*.csv /var/lib/edge/imports/
cd /opt/edge
sudo -u edge python3 -m edge.csv_results --directory /var/lib/edge/prospective /var/lib/edge/imports
sudo systemctl start edge-tracker.service
```

The importer archives each original CSV privately with its actual receipt time,
normalizes team aliases, maps existing match IDs, skips same-day/future results,
rejects ambiguous mappings, and reports conflicting scores without overwriting.
Imported historical odds never become current quotes. E1/E2/E3/EC are deliberately
rejected by this importer until league-strength adjustments are evaluated.
Hard-refresh the GUI (Ctrl+F5); Refresh data supplies fresh live odds for simulations.
