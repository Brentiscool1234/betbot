"""Online opponent-adjusted Poisson with low-score correction, not full Bayesian MLE."""
import math
from datetime import date
from ..poisson import distribution

SIDES=('home','draw','away')


def temperature(probabilities,value):
    if not math.isfinite(value) or value<=0: raise ValueError('invalid temperature')
    logits={k:math.log(max(probabilities[k],1e-15))/value for k in SIDES}
    largest=max(logits.values()); raw={k:math.exp(v-largest) for k,v in logits.items()}; total=sum(raw.values())
    return {k:v/total for k,v in raw.items()}


def corrected_probabilities(home,away,rho):
    h=distribution(home); a=distribution(away); output=dict.fromkeys(SIDES,0.0)
    for i,ph in enumerate(h):
        for j,pa in enumerate(a):
            tau=1-home*away*rho if (i,j)==(0,0) else 1+home*rho if (i,j)==(0,1) else 1+away*rho if (i,j)==(1,0) else 1-rho if (i,j)==(1,1) else 1
            if tau<=0: raise ValueError('invalid low-score correction')
            output['home' if i>j else 'away' if i<j else 'draw']+=ph*pa*tau
    total=sum(output.values()); return {k:v/total for k,v in output.items()}


class Dynamic:
    def __init__(self,learning_rate=.03,half_life=180):
        self.learning_rate=learning_rate; self.half_life=half_life
        self.intercept_home=math.log(1.5); self.intercept_away=math.log(1.2); self.rho=0; self.teams={}; self.matches=0
    def team(self,name,day):
        if name not in self.teams: self.teams[name]={'attack':0.,'weakness':0.,'day':day,'matches':0}
        t=self.teams[name]; gap=(date.fromisoformat(day)-date.fromisoformat(t['day'])).days
        if gap<0: raise ValueError('cannot run model clock backwards')
        factor=2**(-gap/self.half_life)
        t['attack']*=factor; t['weakness']*=factor; t['day']=day
        return t
    def forecast(self,home,away,day):
        h=self.team(home,day); a=self.team(away,day)
        lh=min(5.,max(.15,math.exp(self.intercept_home+h['attack']+a['weakness'])))
        la=min(5.,max(.15,math.exp(self.intercept_away+a['attack']+h['weakness'])))
        return {'lambda_home':lh,'lambda_away':la,'rho':self.rho,'probabilities':corrected_probabilities(lh,la,self.rho),
                'home_history':h['matches'],'away_history':a['matches'],'training_matches':self.matches}
    def observe(self,home,away,day,hg,ag):
        if any(type(g) is not int or g<0 for g in (hg,ag)): raise ValueError('invalid goal counts')
        predicted=self.forecast(home,away,day); h=self.teams[home]; a=self.teams[away]
        # Robust score residuals; heuristic online learning, not exact joint likelihood.
        rh=max(-3.,min(3.,hg-predicted['lambda_home'])); ra=max(-3.,min(3.,ag-predicted['lambda_away']))
        eh=self.learning_rate/math.sqrt(1+h['matches']/20); ea=self.learning_rate/math.sqrt(1+a['matches']/20)
        h['attack']+=eh*rh; a['weakness']+=ea*rh
        a['attack']+=ea*ra; h['weakness']+=eh*ra
        self.intercept_home+=.02*self.learning_rate*rh; self.intercept_away+=.02*self.learning_rate*ra
        lh=predicted['lambda_home']; la=predicted['lambda_away']; rho=self.rho
        derivative=-lh*la/(1-lh*la*rho) if (hg,ag)==(0,0) else lh/(1+lh*rho) if (hg,ag)==(0,1) else la/(1+la*rho) if (hg,ag)==(1,0) else -1/(1-rho) if (hg,ag)==(1,1) else 0.
        self.rho=min(0.,max(-.1,.999*rho+.002*derivative))
        h['matches']+=1; a['matches']+=1; self.matches+=1


def residual_proposal(market,members,weights,team_depth,odds):
    """Conservative proposal only; requires prospective market validation."""
    if len(members)!=len(weights) or not members or abs(sum(weights)-1)>1e-6: raise ValueError('invalid ensemble')
    if abs(sum(market.values())-1)>1e-6 or min(market.values())<=0: raise ValueError('invalid market')
    football={k:sum(w*p[k] for w,p in zip(weights,members)) for k in SIDES}
    dispersion=max(max(p[k] for p in members)-min(p[k] for p in members) for k in SIDES)
    gate=.25*max(0,team_depth)/(max(0,team_depth)+20)*math.exp(-4*dispersion)
    def blend(p):
        residual={k:max(-.5,min(.5,math.log(max(p[k],1e-15)/market[k]))) for k in SIDES}
        raw={k:market[k]*math.exp(gate*residual[k]) for k in SIDES}; total=sum(raw.values())
        return {k:v/total for k,v in raw.items()}
    q=blend(football); scenarios=[blend(p) for p in members]
    return {'status':'research_only_unvalidated','market_residual_weight':gate,'model_disagreement':dispersion,
            'probabilities':q,'scenario_minimum_estimated_ev':{k:min(p[k]*odds[k]-1 for p in scenarios) for k in SIDES},
            'warning':'scenario minima are not statistical confidence bounds; no novelty or edge claim'}
