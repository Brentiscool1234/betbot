"""The Odds API v4: archives precede conversion; errors never expose URLs/keys."""
import json
import os
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from .store import canonical, digest, timestamp, now, validate


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(canonical(value)+'\n')
    temporary.replace(path)


def fetch(endpoint, params):
    key = os.environ.get('ODDS_API_KEY')
    if not key:
        raise ValueError('ODDS_API_KEY is not configured')
    query = urllib.parse.urlencode(dict(params, apiKey=key))
    url = 'https://api.the-odds-api.com/v4/'+endpoint+'?'+query
    try:
        with urllib.request.urlopen(url, timeout=40) as response:
            data = json.load(response)
            quota = {k: response.headers.get('x-requests-'+k) for k in ('remaining','used','last')}
    except urllib.error.HTTPError as exc:
        raise ValueError('provider HTTP '+str(exc.code)+'; URL withheld') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError('provider connection failed; URL withheld') from None
    except (ValueError, UnicodeError):
        raise ValueError('invalid provider JSON') from None
    return {'source': 'the-odds-api', 'received_at': now(), 'request': {'endpoint':endpoint, 'parameters':params}, 'quota':quota, 'response':data}


def archive(directory, envelope):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    sha = digest(envelope)
    path = directory/(sha+'.json')
    if path.exists():
        if digest(json.loads(path.read_text())) != sha:
            raise ValueError('archive checksum mismatch')
    else:
        atomic_json(path, envelope)
    return sha


def load_archive(path):
    envelope = json.loads(Path(path).read_text())
    if digest(envelope) != Path(path).stem:
        raise ValueError('archive checksum mismatch')
    return envelope


def convert(envelope, historical=False):
    received = timestamp(envelope['received_at'])
    response = envelope['response']
    if historical:
        available = timestamp(response['timestamp'])
        requested = timestamp(envelope['request']['parameters']['date'])
        if available > requested or available > received:
            raise ValueError('historical snapshot after requested/received time')
        events = response['data']
    else:
        available, events = received, response
    reference = digest(envelope)
    records = []
    for event in events:
        if event.get('sport_key') != 'soccer_epl':
            raise ValueError('non-EPL event')
        kickoff = timestamp(event['commence_time'])
        mid = 'the-odds-api:'+event['id']
        base = {'match_id':mid,'source':'the-odds-api','source_ref':reference,'available_at':available,
                'effective_at':available,'observed_at':received,'ingested_at':received,
                'availability_basis':'provider_snapshot' if historical else 'observed_only'}
        records.append(dict(base,kind='fixture',key='fixture',payload={'competition_id':'soccer_epl','kickoff':kickoff,'home_team':event['home_team'],'away_team':event['away_team']}))
        if kickoff <= available:
            continue  # do not ingest in-play prices as pre-match
        for book in event.get('bookmakers',[]):
            if book['key'] in ('betfair_ex_uk','betfair_ex_au','matchbook','betfair_ex_eu'):
                continue
            for market in book.get('markets',[]):
                if market['key'] != 'h2h':
                    continue
                updated = timestamp(market.get('last_update') or book['last_update'])
                if updated > available:
                    raise ValueError('odds updated after evidence time')
                outcomes = {o['name']:o['price'] for o in market['outcomes']}
                expected = {event['home_team'], event['away_team'], 'Draw'}
                if set(outcomes) != expected:
                    continue
                for selection,name in [('home',event['home_team']),('draw','Draw'),('away',event['away_team'])]:
                    records.append(dict(base,effective_at=updated,kind='odds',key=book['key']+':'+selection,
                        payload={'bookmaker':book['key'],'market':'1X2','selection':selection,'decimal_odds':outcomes[name]}))
    return [validate(r) for r in records]
