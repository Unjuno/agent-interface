from dataclasses import dataclass
from typing import Any, Mapping, Sequence

@dataclass(frozen=True)
class Decision:
    kind: str
    value: str

@dataclass(frozen=True)
class Request:
    contract_id: str
    facts: Mapping[str, Any]
    allowed: frozenset[tuple[str,str]]
    evidence_roles: frozenset[str]
    authority: str = 'none'

# Predicate bytecode is immutable nested tuples:
# ('eq', key, value), ('all', p1, ...), ('any', p1, ...), ('not', p)
# Clause: (predicate, kind, value); predicate None means default.

def pred(expr, facts):
    op=expr[0]
    if op=='eq': return facts.get(expr[1], object()) == expr[2]
    if op=='all': return all(pred(x,facts) for x in expr[1:])
    if op=='any': return any(pred(x,facts) for x in expr[1:])
    if op=='not': return not pred(expr[1],facts)
    raise ValueError('predicate_opcode')

def eval_program(request: Request, program: Sequence[tuple]) -> Decision:
    if request.authority != 'none':
        return Decision('YIELD','INVALID_AUTHORITY')
    for predicate,kind,value in program:
        if predicate is None or pred(predicate, request.facts):
            out=Decision(kind,value)
            if (out.kind,out.value) not in request.allowed:
                return Decision('YIELD','OUTPUT_OUT_OF_VOCAB')
            return out
    return Decision('YIELD','UNKNOWN_EVIDENCE')

CHROMIUM_PROGRAM=(
    (('any',('eq','session_current',False),('eq','surface_current',False),('eq','geometry_current',False),('eq','handle_live',False)),'YIELD','STALE_CAPABILITY'),
    (('all',('eq','need_scale',False),('eq','need_center',False)),'UNSUPPORTED','UNSUPPORTED'),
    (('eq','ctrl_capability',True),'EXECUTE','CTRL_WHEEL'),
    (('all',('eq','native_capability',True),('eq','need_scale',True),('eq','need_center',False)),'EXECUTE','NATIVE_SCALE'),
    (None,'UNSUPPORTED','UNSUPPORTED'),
)

OPENTTD_PROGRAM=(
    (('eq','binding_current',False),'YIELD','BINDING_CHANGED'),
    (('eq','guard_reason','met'),'EXECUTE','CONTINUE_PROGRAM'),
    (('eq','guard_reason','target_not_reached'),'YIELD','TARGET_NOT_REACHED'),
    (None,'YIELD','UNKNOWN_EVIDENCE'),
)

CHROMIUM_ALLOWED=frozenset({('EXECUTE','CTRL_WHEEL'),('EXECUTE','NATIVE_SCALE'),('YIELD','STALE_CAPABILITY'),('UNSUPPORTED','UNSUPPORTED'),('YIELD','INVALID_AUTHORITY'),('YIELD','OUTPUT_OUT_OF_VOCAB')})
OPENTTD_ALLOWED=frozenset({('EXECUTE','CONTINUE_PROGRAM'),('YIELD','BINDING_CHANGED'),('YIELD','TARGET_NOT_REACHED'),('YIELD','UNKNOWN_EVIDENCE'),('YIELD','INVALID_AUTHORITY'),('YIELD','OUTPUT_OUT_OF_VOCAB')})
