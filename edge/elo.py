"""Elo with a Davidson draw model; ratings do not establish betting value."""
import math

class Elo:
    def __init__(self,k=20,home_advantage=50,draw_parameter=.75):
        if k<=0 or draw_parameter<=0: raise ValueError('invalid Elo parameters')
        self.k=k; self.home_advantage=home_advantage; self.draw_parameter=draw_parameter
        self.ratings={}; self.counts={}
    def forecast(self,home,away):
        h=self.ratings.get(home,1500.); a=self.ratings.get(away,1500.)
        x=10**(max(-1200,min(1200,h+self.home_advantage-a))/800)
        total=x+1/x+self.draw_parameter
        p={'home':x/total,'draw':self.draw_parameter/total,'away':1/x/total}
        # Shared ranks make ties explicit; no lower-division ratings compared.
        rank=lambda r:1+sum(value>r for value in self.ratings.values())
        return {'probabilities':p,'home_rating':h,'away_rating':a,
                'home_rank':rank(h),'away_rank':rank(a),
                'home_matches':self.counts.get(home,0),'away_matches':self.counts.get(away,0)}
    def observe(self,home,away,hg,ag):
        if home==away or any(type(g) is not int or g<0 for g in (hg,ag)): raise ValueError('invalid result')
        p=self.forecast(home,away)['probabilities']
        expected=p['home']+.5*p['draw']; actual=1 if hg>ag else .5 if hg==ag else 0
        change=self.k*(actual-expected)
        self.ratings[home]=self.ratings.get(home,1500.)+change
        self.ratings[away]=self.ratings.get(away,1500.)-change
        for team in (home,away): self.counts[team]=self.counts.get(team,0)+1


def blend(football,elo,weight):
    if not 0<=weight<=1: raise ValueError('invalid blend weight')
    return {k:(1-weight)*football[k]+weight*elo[k] for k in ('home','draw','away')}
