from dataclasses import dataclass

@dataclass(frozen=True)
class Scope:
    session: str
    target: str

@dataclass(frozen=True)
class Decision:
    decision_id: str
    scope: Scope
    generation: int
    grants_authority: bool = False

@dataclass(frozen=True)
class Invalidation:
    event_id: str
    scope: Scope

def _s(x): return isinstance(x,str) and bool(x.strip())
def valid_scope(sc): return isinstance(sc,Scope) and _s(sc.session) and _s(sc.target)

def valid_decision(d):
    if not isinstance(d,Decision) or not _s(d.decision_id) or not valid_scope(d.scope): raise ValueError('decision_identity')
    if type(d.generation) is not int or d.generation < 0: raise ValueError('generation')
    if d.grants_authority: raise ValueError('authority')

def valid_inv(e):
    if not isinstance(e,Invalidation) or not _s(e.event_id) or not valid_scope(e.scope): raise ValueError('invalidation_identity')

class Barrier:
    def __init__(self):
        self.required={}
        self.installed={}
        self.seen_invalidations=set()
    def install(self,d):
        valid_decision(d); req=self.required.get(d.scope,0)
        if d.generation < req: return {'status':'STALE_DECISION_REFUSED','required':req}
        self.installed[d.scope]=d
        return {'status':'DECISION_INSTALLED','required':req,'generation':d.generation}
    def invalidate(self,e):
        valid_inv(e)
        if e.event_id in self.seen_invalidations: return {'status':'DUPLICATE_NOOP','required':self.required.get(e.scope,0)}
        self.seen_invalidations.add(e.event_id)
        self.required[e.scope]=self.required.get(e.scope,0)+1
        return {'status':'CURRENTNESS_INVALIDATED','required':self.required[e.scope]}
    def use(self,scope):
        if not valid_scope(scope): raise ValueError('scope')
        req=self.required.get(scope,0); d=self.installed.get(scope)
        if d is None: return {'status':'NO_DECISION','required':req,'generation':None}
        if d.generation < req: return {'status':'STALE_POLICY_REFUSED','required':req,'generation':d.generation}
        return {'status':'ADMITTED','required':req,'generation':d.generation}
