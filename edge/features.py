"""Versioned rolling goals/points. Missing histories remain explicit."""
from .store import timestamp, digest
VERSION = 'rolling-v1'


def rolling(store, version, match_id, as_of, window=5):
    if window < 1:
        raise ValueError('positive window required')
    cutoff = timestamp(as_of)
    state = store.get_state(match_id, cutoff, version)
    fixtures = [r for r in state if r['kind'] == 'fixture']
    if not fixtures:
        raise ValueError('fixture unavailable at cutoff')
    fixture = fixtures[0]['payload']
    output = {'feature_version': VERSION, 'dataset_version': version, 'as_of': cutoff, 'match_id': match_id}
    match_ids = {r['match_id'] for r in store.records(version)} - {match_id}
    for side in ('home', 'away'):
        team = fixture[side+'_team']
        history = []
        for other in match_ids:
            old = store.get_state(other, cutoff, version)
            fs = [r for r in old if r['kind'] == 'fixture']
            rs = [r for r in old if r['kind'] == 'result']
            if not fs or not rs:
                continue
            f, r = fs[0]['payload'], rs[0]
            if timestamp(f['kickoff']) >= cutoff or timestamp(f['kickoff']) >= timestamp(fixture['kickoff']):
                continue
            if team not in (f['home_team'], f['away_team']):
                continue
            home = team == f['home_team']
            gf, ga = (r['payload']['home_goals'], r['payload']['away_goals']) if home else (r['payload']['away_goals'], r['payload']['home_goals'])
            history.append((timestamp(f['kickoff']), other, gf, ga, digest(r), digest(fs[0])))
        history = sorted(history, reverse=True)[:window]
        output[side] = {'matches': len(history), 'goals_for': sum(x[2] for x in history)/len(history) if history else None,
                        'goals_against': sum(x[3] for x in history)/len(history) if history else None,
                        'points': sum(3 if x[2]>x[3] else 1 if x[2]==x[3] else 0 for x in history)/len(history) if history else None,
                        'source_records': [h for x in history for h in x[4:]]}
    return output
