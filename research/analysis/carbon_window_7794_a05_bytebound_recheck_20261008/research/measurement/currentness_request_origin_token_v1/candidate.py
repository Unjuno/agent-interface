from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Scope:
    session: str
    target: str

@dataclass(frozen=True)
class Invalidation:
    event_id: str
    scope: Scope

def _id(x):
    return isinstance(x, str) and bool(x.strip())

def validate_scope(s):
    if not isinstance(s, Scope) or not _id(s.session) or not _id(s.target):
        raise ValueError('scope')

def validate_pgen(x):
    if type(x) is not int or x < 0:
        raise ValueError('planner_generation')

def validate_invalidation(e):
    if not isinstance(e, Invalidation) or not _id(e.event_id):
        raise ValueError('event_id')
    validate_scope(e.scope)

class RequestOriginBarrier:
    def __init__(self):
        self.epoch = {}
        self.requests = {}
        self.decisions = {}
        self.seen_invalidations = set()

    def begin_request(self, scope, request_id, grants_authority=False):
        validate_scope(scope)
        if not _id(request_id): raise ValueError('request_id')
        if grants_authority is not False: raise ValueError('authority')
        if request_id in self.requests: raise ValueError('duplicate_request_id')
        ep = self.epoch.get(scope, 0)
        self.requests[request_id] = [scope, ep, False]
        return {'status':'REQUEST_BEGUN','request_id':request_id,'scope':scope,'request_epoch':ep,'grants_input_authority':False}

    def invalidate(self, e):
        validate_invalidation(e)
        if e.event_id in self.seen_invalidations:
            return {'status':'DUPLICATE_INVALIDATION_NOOP','event_id':e.event_id,'scope':e.scope,'epoch':self.epoch.get(e.scope,0),'grants_input_authority':False}
        self.seen_invalidations.add(e.event_id)
        ep = self.epoch.get(e.scope,0) + 1
        self.epoch[e.scope] = ep
        return {'status':'CURRENTNESS_INVALIDATED','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}

    def install_response(self, request_id, decision_id, planner_generation, grants_authority=False):
        if not _id(request_id): raise ValueError('request_id')
        if not _id(decision_id): raise ValueError('decision_id')
        validate_pgen(planner_generation)
        if grants_authority is not False: raise ValueError('authority')
        req = self.requests.get(request_id)
        if req is None:
            return {'status':'UNKNOWN_REQUEST_REFUSED','request_id':request_id,'decision_id':decision_id,'planner_generation':planner_generation,'grants_input_authority':False}
        scope, origin, consumed = req
        cur = self.epoch.get(scope,0)
        if consumed:
            return {'status':'RESPONSE_REPLAY_REFUSED','request_id':request_id,'decision_id':decision_id,'scope':scope,'request_epoch':origin,'epoch':cur,'planner_generation':planner_generation,'grants_input_authority':False}
        if decision_id in self.decisions:
            raise ValueError('duplicate_decision_id')
        req[2] = True
        if origin != cur:
            return {'status':'STALE_RESPONSE_REFUSED','request_id':request_id,'decision_id':decision_id,'scope':scope,'request_epoch':origin,'epoch':cur,'planner_generation':planner_generation,'grants_input_authority':False}
        self.decisions[decision_id] = (scope, origin, planner_generation, request_id)
        return {'status':'DECISION_INSTALLED','request_id':request_id,'decision_id':decision_id,'scope':scope,'epoch':origin,'planner_generation':planner_generation,'grants_input_authority':False}

    def try_use(self, scope, decision_id):
        validate_scope(scope)
        if not _id(decision_id): raise ValueError('decision_id')
        cur = self.epoch.get(scope,0)
        rec = self.decisions.get(decision_id)
        if rec is None:
            return {'status':'UNKNOWN_DECISION','decision_id':decision_id,'scope':scope,'epoch':cur,'grants_input_authority':False}
        dscope, dep, pgen, rid = rec
        if dscope != scope:
            return {'status':'SCOPE_MISMATCH','decision_id':decision_id,'scope':scope,'decision_scope':dscope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}
        if dep != cur:
            return {'status':'STALE_EPOCH_REFUSED','decision_id':decision_id,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}
        return {'status':'ADMITTED','decision_id':decision_id,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}

    def snapshot(self):
        return {
            'epochs': tuple(sorted((s.session,s.target,e) for s,e in self.epoch.items())),
            'requests': tuple(sorted((rid,sc.session,sc.target,ep,cons) for rid,(sc,ep,cons) in self.requests.items())),
            'decisions': tuple(sorted((did,sc.session,sc.target,ep,pg,rid) for did,(sc,ep,pg,rid) in self.decisions.items())),
            'seen_invalidations': tuple(sorted(self.seen_invalidations)),
        }
