"""A data gate, never a model-performance claim."""
from datetime import datetime, timedelta
from collections import defaultdict
from .store import timestamp, digest
from .features import rolling


def report(store, version):
    records = store.records(version)
    fixtures = {}
    for r in records:
        if r['kind'] == 'fixture':
            mid = r['match_id']
            if mid not in fixtures or (r['available_at'],digest(r)) > (fixtures[mid]['available_at'],digest(fixtures[mid])):
                fixtures[mid] = r
    demos = []
    stale = []
    for mid, fixture in sorted(fixtures.items()):
        kickoff = timestamp(fixture['payload']['kickoff'])
        cutoff = timestamp((datetime.fromisoformat(kickoff)-timedelta(hours=24)).isoformat())
        state = store.get_state(mid, cutoff, version)
        available_fixture = next((r for r in state if r['kind']=='fixture'), None)
        if not available_fixture or timestamp(available_fixture['payload']['kickoff']) != kickoff:
            continue  # a later reschedule must not silently redefine historical horizons
        by_book = defaultdict(set)
        for r in state:
            if r['kind'] == 'odds':
                by_book[r['payload']['bookmaker']].add(r['payload']['selection'])
        books = [b for b,selections in by_book.items() if selections == {'home','draw','away'}]
        if not books:
            continue
        odds = [r for r in state if r['kind']=='odds' and r['payload']['bookmaker'] in books]
        oldest = min(r['effective_at'] for r in odds)
        age = (datetime.fromisoformat(cutoff)-datetime.fromisoformat(oldest)).total_seconds()/3600
        stale.append(age)
        demos.append({'match_id':mid,'kickoff':kickoff,'as_of':cutoff,'bookmakers':len(books),
                      'state_hash':digest(state),'max_odds_age_hours':round(age,2)})
    return {'schema_version':1,'dataset_version':version,'records':len(records),'unique_matches':len(fixtures),
            't24_demonstrations':len(demos),'historical_results':sum(r['kind']=='result' for r in records),
            'historical_statistics':sum(r['kind']=='statistics' for r in records),
            'maximum_odds_age_hours':round(max(stale,default=0),2),'demonstrations':demos,
            'phase1_status':'incomplete: result/statistics/publication coverage requires independent acceptance',
            'limitations':['Weekly historical quotes can be stale; exact T-24h prices are not guaranteed.',
                          'Odds provider coverage does not guarantee all EPL fixtures.',
                          'Unknown injuries, lineups and statistics remain missing.',
                          'Historical provider-snapshot availability differs from actual local observation.']}
