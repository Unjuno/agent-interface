from dataclasses import dataclass

REGIMES={'VALID_CONTINUATION','HARD_INVALIDATION','AMBIGUOUS_BOUNDARY'}

@dataclass(frozen=True)
class CacheEntry:
    cache_id: str
    intent_id: str
    strategy_id: str
    generation: int
    provenance: str
    macro_id: str
    allowed_action: str
    max_age: int
    max_updates: int

@dataclass(frozen=True)
class Evidence:
    intent_id: str
    strategy_id: str
    generation: int
    provenance: str
    age: int
    update_index: int
    regime: str


def _good_text(x):
    return isinstance(x,str) and bool(x.strip())


def validate_entry(e):
    if not isinstance(e,CacheEntry): raise ValueError('entry')
    if not all(_good_text(getattr(e,k)) for k in ('cache_id','intent_id','strategy_id','provenance','macro_id','allowed_action')): raise ValueError('entry_identity')
    if type(e.generation) is not int or e.generation<0: raise ValueError('generation')
    if type(e.max_age) is not int or e.max_age<1: raise ValueError('max_age')
    if type(e.max_updates) is not int or e.max_updates<1: raise ValueError('max_updates')
    return e


def validate_evidence(v):
    if not isinstance(v,Evidence): raise ValueError('evidence')
    if not all(_good_text(getattr(v,k)) for k in ('intent_id','strategy_id','provenance')): raise ValueError('evidence_identity')
    if type(v.generation) is not int or v.generation<0: raise ValueError('generation')
    if type(v.age) is not int or v.age<0: raise ValueError('age')
    if type(v.update_index) is not int or v.update_index<0: raise ValueError('update')
    if v.regime not in REGIMES: raise ValueError('regime')
    return v


def monitor(entry,evidence):
    e=validate_entry(entry); v=validate_evidence(evidence)
    reason=None
    if v.intent_id!=e.intent_id: reason='intent_changed'
    elif v.strategy_id!=e.strategy_id: reason='strategy_changed'
    elif v.generation!=e.generation: reason='generation_changed'
    elif v.provenance!=e.provenance: reason='provenance_changed'
    elif v.age>e.max_age: reason='expired'
    elif v.update_index>=e.max_updates: reason='update_budget_exhausted'
    elif v.regime=='HARD_INVALIDATION': reason='hard_invalidated'
    elif v.regime=='AMBIGUOUS_BOUNDARY': reason='ambiguous_yield'
    if reason is None:
        return {'disposition':'KEEP','action':e.allowed_action,'reason':'valid_continuation','grants_input_authority':False}
    return {'disposition':'YIELD','action':None,'reason':reason,'grants_input_authority':False}
