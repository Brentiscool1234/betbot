"""Persistent credit reservations. Unknown failed requests retain their reservation."""
import json
from pathlib import Path
from .provider import atomic_json


class Budget:
    def __init__(self,path,daily=20,monthly=400,reserve_quota=100):
        self.path=Path(path); self.daily=daily; self.monthly=monthly; self.reserve_quota=reserve_quota
    def reserve(self,current,cost=1):
        state=json.loads(self.path.read_text()) if self.path.exists() else {}
        day=current.strftime('%Y-%m-%d'); month=current.strftime('%Y-%m')
        if state.get('month')!=month:
            state={'month':month,'monthly_used':0}
        if state.get('day')!=day:
            state.update(day=day,daily_used=0)
        if state['daily_used']+cost>self.daily: return 'daily credit limit reached'
        if state['monthly_used']+cost>self.monthly: return 'monthly credit limit reached'
        if state.get('quota_remaining') is not None and state['quota_remaining']<self.reserve_quota+cost:
            return 'provider quota reserve reached'
        state['daily_used']+=cost; state['monthly_used']+=cost
        atomic_json(self.path,state)
        return None
    def reconcile(self,quota,reserved=1):
        state=json.loads(self.path.read_text())
        try: actual=int(quota['last'])
        except (KeyError,TypeError,ValueError): actual=reserved
        # Never reduce reservations, even for zero-charge/failed requests.
        extra=max(0,actual-reserved)
        state['daily_used']+=extra; state['monthly_used']+=extra
        try: state['quota_remaining']=int(quota['remaining'])
        except (KeyError,TypeError,ValueError): pass
        atomic_json(self.path,state)
