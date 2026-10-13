"""Content-addressed immutable observations and immutable dataset membership."""
import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('timezone required')
    return t.astimezone(timezone.utc).isoformat(timespec='microseconds')


def now():
    return datetime.now(timezone.utc).isoformat()


def validate(record):
    r = dict(record)
    for field in ('match_id', 'kind', 'key', 'source', 'source_ref', 'availability_basis'):
        if not isinstance(r.get(field), str) or not r[field]:
            raise ValueError('missing '+field)
    if r['availability_basis'] not in ('provider_snapshot', 'observed_only', 'verified_publication'):
        raise ValueError('unsupported availability evidence')
    for field in ('effective_at', 'available_at', 'observed_at', 'ingested_at'):
        r[field] = timestamp(r[field])
    if not r['effective_at'] <= r['available_at'] <= r['observed_at'] <= r['ingested_at']:
        raise ValueError('invalid timestamp ordering')
    if r['availability_basis'] == 'observed_only' and r['available_at'] != r['observed_at']:
        raise ValueError('cannot backdate observed-only information')
    p = r.get('payload')
    if not isinstance(p, dict):
        raise ValueError('payload must be an object')
    if r['kind'] == 'fixture':
        for field in ('home_team', 'away_team', 'competition_id', 'kickoff'):
            if not p.get(field):
                raise ValueError('missing fixture field '+field)
        timestamp(p['kickoff'])
        if p['home_team'] == p['away_team']:
            raise ValueError('identical teams')
    elif r['kind'] == 'odds':
        price = p.get('decimal_odds')
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 1:
            raise ValueError('invalid decimal odds')
        if p.get('selection') not in ('home', 'draw', 'away') or not p.get('bookmaker'):
            raise ValueError('invalid odds selection/bookmaker')
    elif r['kind'] == 'result':
        for field in ('home_goals', 'away_goals'):
            if type(p.get(field)) is not int or p[field] < 0:
                raise ValueError('invalid goals')
        if p.get('status') != 'finished':
            raise ValueError('non-final result')
    elif r['kind'] not in ('statistics', 'lineup', 'availability'):
        raise ValueError('unsupported record kind')
    canonical(r)
    return r


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(dataset TEXT REFERENCES datasets(id),
          record TEXT REFERENCES records(id), PRIMARY KEY(dataset,record));
        ''')
        for table in ('records', 'datasets', 'members'):
            for operation in ('UPDATE', 'DELETE'):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'immutable data'); END")

    def close(self):
        self.db.close()

    def ingest(self, records, parent=None):
        validated = [validate(r) for r in records]
        ids = set()
        if parent:
            self.records(parent)  # reject unknown versions
            ids.update(x[0] for x in self.db.execute('SELECT record FROM members WHERE dataset=?', (parent,)))
        ids.update(digest(r) for r in validated)
        version = digest({'schema': 1, 'records': sorted(ids)})
        with self.db:
            for r in validated:
                self.db.execute('INSERT OR IGNORE INTO records VALUES (?,?)', (digest(r), canonical(r)))
            self.db.execute('INSERT OR IGNORE INTO datasets VALUES (?,?)', (version, now()))
            self.db.executemany('INSERT OR IGNORE INTO members VALUES (?,?)', [(version, i) for i in sorted(ids)])
        return version

    def records(self, version):
        if not self.db.execute('SELECT 1 FROM datasets WHERE id=?', (version,)).fetchone():
            raise ValueError('unknown dataset version')
        return [json.loads(row[0]) for row in self.db.execute('SELECT r.body FROM records r JOIN members m ON m.record=r.id WHERE m.dataset=? ORDER BY r.id', (version,))]

    def get_state(self, match_id, as_of, version, clock='available'):
        if clock not in ('available', 'observed'):
            raise ValueError('clock must be available or observed')
        cutoff = timestamp(as_of)
        latest = {}
        for r in self.records(version):
            if r['match_id'] != match_id or r['available_at'] > cutoff or r['effective_at'] > cutoff:
                continue
            if clock == 'observed' and r['observed_at'] > cutoff:
                continue
            key = (r['kind'], r['key'])
            order = (r['available_at'], r['effective_at'], r['observed_at'], digest(r))
            if key not in latest or order > latest[key][0]:
                latest[key] = (order, r)
        return [latest[k][1] for k in sorted(latest)]
