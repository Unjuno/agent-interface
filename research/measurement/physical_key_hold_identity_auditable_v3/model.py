from dataclasses import dataclass

OPS={'down','up','cleanup'}
class LifecycleError(ValueError): pass
@dataclass(frozen=True)
class Event:
    op:str; owner:str; intent:str; key:str; confirmed:bool

def _valid_text(x): return type(x) is str and bool(x.strip())
def validate_event(e):
    if not isinstance(e,Event) or e.op not in OPS or not all(_valid_text(x) for x in (e.owner,e.intent,e.key)) or type(e.confirmed) is not bool:
        raise LifecycleError('malformed_event')

class Candidate:
    def __init__(self):
        self.counters={}; self.active={}; self.retired=set()
    def step(self,e):
        validate_event(e); cur=self.active.get(e.key)
        if e.op=='down':
            if cur is not None:
                owner,intent,aid=cur
                if (owner,intent)!=(e.owner,e.intent): return ('LINEAGE_MISMATCH',None)
                return ('ACTIVE_REUSED',aid)
            if not e.confirmed: return ('UNCONFIRMED_DOWN_NO_ID',None)
            gen=self.counters.get(e.owner,0)+1; aid=f'{e.owner}:g{gen}:{e.key}'
            if aid in self.retired: raise LifecycleError('retired_id_reuse')
            self.counters[e.owner]=gen; self.active[e.key]=(e.owner,e.intent,aid)
            return ('MINTED',aid)
        if not e.confirmed: return ('UNCONFIRMED_UP_NO_CHANGE',None)
        if cur is None: return ('NO_ACTIVE',None)
        owner,intent,aid=cur
        if (owner,intent)!=(e.owner,e.intent): return ('LINEAGE_MISMATCH',None)
        del self.active[e.key]; self.retired.add(aid)
        return ('RETIRED',aid)
    def snapshot(self):
        return {'counters':sorted(self.counters.items()),'active':sorted((k,*v) for k,v in self.active.items()),'retired':sorted(self.retired)}
