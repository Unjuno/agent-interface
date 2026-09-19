from dataclasses import dataclass
from enum import Enum
class Classification(str,Enum):
    DEFINITELY_BEFORE="DEFINITELY_BEFORE"; TEMPORALLY_AMBIGUOUS="TEMPORALLY_AMBIGUOUS"; GUARANTEED_AFTER="GUARANTEED_AFTER"; UNBOUND_OR_WRONG_LINEAGE="UNBOUND_OR_WRONG_LINEAGE"; CLOCK_UNKNOWN="LIVE_CLOCK_OR_ORDER_UNKNOWN"; SEMANTICALLY_UNRELATED="EFFECT_SEMANTICALLY_UNRELATED"
class Action(str,Enum):
    DONE="DONE"; QUERY_EFFECT="QUERY_EFFECT"; RECONCILE_CLOCKS="RECONCILE_CLOCKS"; ABORT="ABORT"; WAIT="WAIT"; RETRY="RETRY"
@dataclass(frozen=True)
class Decision:
    action: Action
    authoritative: bool
    retry_allowed: bool

def decide(classification: Classification, *, idempotent: bool=False, generation_match: bool=False) -> Decision:
    if classification is Classification.DEFINITELY_BEFORE:
        return Decision(Action.DONE, True, False)
    if classification in (Classification.TEMPORALLY_AMBIGUOUS, Classification.GUARANTEED_AFTER):
        return Decision(Action.QUERY_EFFECT, False, idempotent and generation_match)
    if classification is Classification.CLOCK_UNKNOWN:
        return Decision(Action.RECONCILE_CLOCKS, False, False)
    return Decision(Action.ABORT, False, False)
