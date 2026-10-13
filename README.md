# EDGE / betbot

EPL point-in-time data research and pre-match odds collection. Python 3.12+,
standard library only. No prediction models or wagering.

```sh
python -m unittest discover -s tests -v
python -m edge.collect
python -m edge.collect --watch
python -m edge.health
python -m edge.historical
```

Supply `ODDS_API_KEY` through environment settings; never commit it.
Historical downloads use a fixed weekly 2024 plan, cache private response
archives and stop at 100 eligible fixtures or 20 requests. Each historical
request costs approximately 10 credits; live UK/1X2 requests approximately 1.

CLI state reconstruction:

```sh
python -m edge.cli --db data/historical/edge.sqlite quality DATASET_VERSION
python -m edge.cli --db data/historical/edge.sqlite state DATASET_VERSION MATCH_ID AS_OF_UTC
python -m edge.cli --db data/historical/edge.sqlite features DATASET_VERSION MATCH_ID AS_OF_UTC
python -m edge.cli --db data/historical/edge.sqlite import licensed-records.jsonl --parent DATASET_VERSION
```

Read [architecture](docs/DATA_ARCHITECTURE.md), [source review](docs/DATA_FEASIBILITY.md),
[costs](docs/FINANCIAL_FEASIBILITY.md), [historical report](docs/HISTORICAL_DATA_REPORT.md)
and [VPS operations](docs/OPERATIONS.md).

Phase 1 is incomplete: licensed results and statistics with historical
publication evidence remain missing. Do not treat fixture/odds coverage as
full acceptance or evidence of a profitable model.

## Completed results and sample request

The VPS service now uses `python -m edge.collect --watch --with-results` to gather
completed EPL scores every six hours using the existing Odds API allowance.
Results use actual receipt availability; live scores cannot become final labels.
See [VPS update steps](docs/OPERATIONS.md) and the
[prepared historical sample request](docs/PROVIDER_SAMPLE_REQUEST.md).
No new statistics subscription or trial has been activated.
