"""Prior-match form only; never reads the target result."""
from collections import defaultdict,deque

class Form:
    def __init__(self): self.teams=defaultdict(lambda:deque(maxlen=10))
    def observe(self,home,away,hg,ag):
        for team,gf,ga in ((home,hg,ag),(away,ag,hg)):
            self.teams[team].append((3 if gf>ga else 1 if gf==ga else 0,gf,ga))
    def summary(self,team,window=5):
        rows=list(self.teams.get(team,()))[-window:];n=len(rows)
        return {'matches':n,'points_per_match':sum(r[0] for r in rows)/n if n else 0,
                'goals_for_per_match':sum(r[1] for r in rows)/n if n else 0,
                'goals_against_per_match':sum(r[2] for r in rows)/n if n else 0}
    def features(self,home,away):
        values=[]
        for window in (5,10):
            for team in (home,away):
                s=self.summary(team,window);values.extend(s.values())
        return values
