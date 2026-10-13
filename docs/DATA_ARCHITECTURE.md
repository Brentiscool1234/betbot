# Architecture and data contract

SQLite records are immutable canonical JSON addressed by SHA-256. Dataset
versions hash sorted member hashes plus schema version. Database triggers reject
updates/deletes of records, versions and memberships. Corrected source data is
an additional observation. Ingestion validates the whole batch before writing.
This guards application operations; it cannot stop someone replacing the entire
DB file. Keep private backups and archive checksums.

Each record has match_id, kind, key, effective_at, available_at, observed_at,
ingested_at, source, source_ref (archive SHA-256), availability_basis, payload.
UTC timezone is mandatory. effective <= available <= observed <= ingested.
For observed_only records, available equals observed; no retrospective backdating.
provider_snapshot means the historical provider response evidences availability
at its snapshot time. verified_publication requires supplied independent evidence;
the importer validates timestamps but cannot authenticate that evidence or a
licence. Source onboarding must independently review both before acceptance.

get_state(match_id, as_of, dataset_version, clock='available') filters both
available and effective timestamps. clock='observed' additionally requires actual
local receipt before the cutoff. It then takes the latest observation per
kind/key, with deterministic hash tie-breaking. Explicit dataset versions prevent
new ingestion changing old reproductions. Provenance and source-record hashes are
retained in state and rolling features.

Fixture payload: competition_id, kickoff, home_team, away_team. Source event IDs
are stable identifiers, prefixed with the provider. Provider team names are
currently identifiers; cross-provider mapping and name revisions require explicit
review. Kickoff changes are observations. The quality report excludes T-24h demos
where a later kickoff revision would silently change the prediction horizon.

Odds payload: bookmaker, market='1X2', selection in home/draw/away, decimal_odds>1.
The adapter excludes known exchanges, incomplete markets and in-play quotes.
Bookmaker market update is effective time; historical snapshot is availability.
These are actual timestamps, not artificially assigned T-24h quotes.

Result payload: home_goals, away_goals (nonnegative integers), status='finished'.
Statistics, lineup and availability records may be imported, but there is no
provider adapter or feature extraction for them yet. Do not infer source
publication from the event date. Results obtained today may be labels, but are
unavailable as inputs before their evidenced publication time. Licences and
provenance evidence must accompany a future provider import.

Rolling features require historical results available before prediction time and
exclude current and future fixtures. Missing history yields count=0 and null
means. Unknown injuries/xG/lineups remain missing, not zero. Rolling source IDs
allow audit. Models, calibration, market probabilities and backtests are deferred.

Tests inject late odds, late score publication, future fixtures, and current
results, reject timestamp reversal/backdating and prove deterministic replay,
immutable versions, crash archive recovery, overlap locks and budget enforcement.
