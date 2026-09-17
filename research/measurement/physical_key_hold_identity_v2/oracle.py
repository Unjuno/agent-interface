from dataclasses import dataclass
from model import Event,LifecycleError,validate_event
@dataclass
class Hold:
    owner:str; intent:str; key:str; aid:str; active:bool=True
class HistoryOracle:
    def __init__(self): self.holds=[]
    def _active_for_key(self,key):
        for h in reversed(self.holds):
            if h.key==key and h.active: return h
        return None
    def step(self,e:Event):
        validate_event(e); h=self._active_for_key(e.key)
        if e.op=='down':
            if h is not None:
                if (h.owner,h.intent)!=(e.owner,e.intent): return ('LINEAGE_MISMATCH',None)
                return ('ACTIVE_REUSED',h.aid)
            if e.confirmed is False: return ('UNCONFIRMED_DOWN_NO_ID',None)
            gen=1+sum(1 for x in self.holds if x.owner==e.owner); aid=f'{e.owner}:g{gen}:{e.key}'
            if any(x.aid==aid for x in self.holds): raise LifecycleError('oracle_reuse')
            self.holds.append(Hold(e.owner,e.intent,e.key,aid,True)); return ('MINTED',aid)
        if e.confirmed is False: return ('UNCONFIRMED_UP_NO_CHANGE',None)
        if h is None: return ('NO_ACTIVE',None)
        if (h.owner,h.intent)!=(e.owner,e.intent): return ('LINEAGE_MISMATCH',None)
        h.active=False; return ('RETIRED',h.aid)
    def snapshot(self):
        owners=sorted({x.owner for x in self.holds})
        counters=sorted((o,sum(1 for x in self.holds if x.owner==o)) for o in owners)
        active=sorted((x.key,x.owner,x.intent,x.aid) for x in self.holds if x.active)
        retired=sorted(x.aid for x in self.holds if not x.active)
        return {'counters':counters,'active':active,'retired':retired}
