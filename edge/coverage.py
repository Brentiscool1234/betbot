"""Diagnose observed source/team gaps; never manufacture missing history."""
from datetime import datetime
from .store import timestamp


def diagnose(states,matches,as_of):
    latest={}; results=0
    for rows in states.values():
        fixture=next((r for r in rows if r['kind']=='fixture'),None); result=next((r for r in rows if r['kind']=='result'),None)
        if not fixture or not result: continue
        results+=1; f=fixture['payload']
        for team in (f['home_team'],f['away_team']): latest[team]=max(latest.get(team,''),timestamp(f['kickoff']))
    entries=[]
    for match in matches:
        c=match['model'].get('history_counts',{}); f=match['fixture']
        home=c.get('home_team_at_home',0); away=c.get('away_team_away',0); league=c.get('league',0)
        def age(team):
            date=latest.get(team)
            return round((datetime.fromisoformat(timestamp(as_of))-datetime.fromisoformat(date)).total_seconds()/86400,1) if date else None
        entries.append({'match_id':match['match_id'],'home_team':f['home_team'],'away_team':f['away_team'],
                        'model_ready':match['model']['status']=='experimental_prediction','home_history':home,'away_history':away,
                        'home_shortfall':max(0,5-home),'away_shortfall':max(0,5-away),'league_shortfall':max(0,50-league),
                        'home_latest_result_age_days':age(f['home_team']),'away_latest_result_age_days':age(f['away_team']),
                        'reason':match['model'].get('reason'),'warning':'minimum counts are not evidence of calibration or complete coverage'})
    return {'as_of':as_of,'observed_result_events':results,'model_ready':sum(e['model_ready'] for e in entries),
            'upcoming_matches':len(entries),'matches':entries,
            'limitations':['Community files may be incomplete or delayed.','Missing prior EPL history may be genuine for promoted teams.','No substitute lower-league scores or invented records used.']}
