from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Scope:
    session: str
    target: str

@dataclass(frozen=True)
class DecisionRequest:
    decision_id: str
    scope: Scope
    planner_generation: int
    grants_authority: bool = False

@dataclass(frozen=True)
class Invalidation:
    event_id: str
    scope: Scope


def _id(x):
    return isinstance(x, str) and bool(x.strip())

def validate_scope(s):
    if not isinstance(s, Scope) or not _id(s.session) or not _id(s.target):
        raise ValueError('scope')

def validate_decision(d):
    if not isinstance(d, DecisionRequest) or not _id(d.decision_id):
        raise ValueError('decision_id')
    validate_scope(d.scope)
    if type(d.planner_generation) is not int or d.planner_generation < 0:
        raise ValueError('planner_generation')
    if d.grants_authority is not False:
        raise ValueError('authority')

def validate_invalidation(e):
    if not isinstance(e, Invalidation) or not _id(e.event_id):
        raise ValueError('event_id')
    validate_scope(e.scope)

class EpochBarrier:
    def __init__(self):
        self.epoch = {}
        self.decisions = {}  # decision_id -> (scope, stamped_epoch, planner_generation)
        self.seen_invalidations = set()

    def install(self, d):
        validate_decision(d)
        if d.decision_id in self.decisions:
            raise ValueError('duplicate_decision_id')
        ep = self.epoch.get(d.scope, 0)
        self.decisions[d.decision_id] = (d.scope, ep, d.planner_generation)
        return {'status':'DECISION_INSTALLED','decision_id':d.decision_id,'scope':d.scope,'epoch':ep,'planner_generation':d.planner_generation,'grants_input_authority':False}

    def invalidate(self, e):
        validate_invalidation(e)
        if e.event_id in self.seen_invalidations:
            return {'status':'DUPLICATE_INVALIDATION_NOOP','event_id':e.event_id,'scope':e.scope,'epoch':self.epoch.get(e.scope,0),'grants_input_authority':False}
        self.seen_invalidations.add(e.event_id)
        ep = self.epoch.get(e.scope,0) + 1
        self.epoch[e.scope] = ep
        return {'status':'CURRENTNESS_INVALIDATED','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}

    def try_use(self, scope, decision_id):
        validate_scope(scope)
        if not _id(decision_id): raise ValueError('decision_id')
        cur = self.epoch.get(scope,0)
        rec = self.decisions.get(decision_id)
        if rec is None:
            return {'status':'UNKNOWN_DECISION','decision_id':decision_id,'scope':scope,'epoch':cur,'grants_input_authority':False}
        dscope, dep, pgen = rec
        if dscope != scope:
            return {'status':'SCOPE_MISMATCH','decision_id':decision_id,'scope':scope,'decision_scope':dscope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
        if dep != cur:
            return {'status':'STALE_EPOCH_REFUSED','decision_id':decision_id,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
        return {'status':'ADMITTED','decision_id':decision_id,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}

    def snapshot(self):
        return {
            'epochs': tuple(sorted((s.session,s.target,e) for s,e in self.epoch.items())),
            'decisions': tuple(sorted((did,sc.session,sc.target,ep,pg) for did,(sc,ep,pg) in self.decisions.items())),
            'seen_invalidations': tuple(sorted(self.seen_invalidations)),
        }
