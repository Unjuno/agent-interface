from dataclasses import dataclass, field

VALID_STATES={"CLEAR","WATCH","HARD"}

@dataclass
class Prepared:
    scope:str
    decision_id:str
    generation:int
    state:str
    consumed:bool=False

@dataclass
class ScopeState:
    generation:int=0
    open:bool=False
    state:str="HARD"
    closed_events:set=field(default_factory=set)

class Candidate:
    def __init__(self):
        self.scopes={}
        self.prepared={}
        self.effects=[]
    def _s(self, scope): return self.scopes.setdefault(scope, ScopeState())
    def frontier_request(self, scope):
        if not isinstance(scope,str) or not scope: return {"ok":False,"reason":"BAD_SCOPE"}
        s=self._s(scope); s.generation += 1; s.open=True
        return {"ok":True,"generation":s.generation}
    def observe(self, scope, state):
        if state not in VALID_STATES: return {"ok":False,"reason":"BAD_STATE"}
        s=self._s(scope); s.state=state
        return {"ok":True}
    def prepare(self, scope, decision_id):
        if not isinstance(decision_id,str) or not decision_id or decision_id in self.prepared:
            return {"ok":False,"reason":"BAD_OR_DUPLICATE_DECISION"}
        s=self._s(scope)
        if not s.open: return {"ok":False,"reason":"CLOSED"}
        p=Prepared(scope,decision_id,s.generation,s.state)
        self.prepared[decision_id]=p
        return {"ok":True,"generation":p.generation,"state":p.state}
    def frontier_return(self, scope, event_id):
        if not isinstance(event_id,str) or not event_id: return {"ok":False,"reason":"BAD_EVENT"}
        s=self._s(scope)
        if event_id in s.closed_events: return {"ok":False,"reason":"DUPLICATE_RETURN"}
        s.closed_events.add(event_id); s.open=False
        return {"ok":True,"closed_generation":s.generation}
    def try_admit(self, scope, prepared_id, ordinary_authority, claimed_generation=None):
        p=self.prepared.get(prepared_id)
        if not p: return {"admit":False,"reason":"MISSING_PREPARED"}
        if p.consumed: return {"admit":False,"reason":"REPLAY"}
        if p.scope != scope: return {"admit":False,"reason":"CROSS_SCOPE"}
        s=self._s(scope)
        if claimed_generation is not None and claimed_generation != p.generation:
            return {"admit":False,"reason":"GENERATION_FORGERY"}
        if not ordinary_authority: return {"admit":False,"reason":"ORDINARY_AUTHORITY_FALSE"}
        if not s.open: return {"admit":False,"reason":"CLOSED"}
        if s.state != "CLEAR" or p.state != "CLEAR": return {"admit":False,"reason":"STATE"}
        if p.generation != s.generation: return {"admit":False,"reason":"STALE_GENERATION"}
        p.consumed=True
        self.effects.append((scope,prepared_id,s.generation))
        return {"admit":True,"reason":"OK"}

class StateOnlyComparator(Candidate):
    def try_admit(self, scope, prepared_id, ordinary_authority, claimed_generation=None):
        p=self.prepared.get(prepared_id)
        if not p: return {"admit":False,"reason":"MISSING_PREPARED"}
        if p.consumed: return {"admit":False,"reason":"REPLAY"}
        if p.scope != scope: return {"admit":False,"reason":"CROSS_SCOPE"}
        s=self._s(scope)
        if not ordinary_authority: return {"admit":False,"reason":"ORDINARY_AUTHORITY_FALSE"}
        if not s.open: return {"admit":False,"reason":"CLOSED"}
        if s.state != "CLEAR" or p.state != "CLEAR": return {"admit":False,"reason":"STATE"}
        p.consumed=True; self.effects.append((scope,prepared_id,s.generation))
        return {"admit":True,"reason":"OK"}
