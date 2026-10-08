from dataclasses import dataclass
from typing import Tuple

UNIVERSE=(-2,-1,1,2)
K=1
GAP_NS=40_000_000
REALIZE_NS=10_000_000
LOCAL_COST_NS=1_000_000
MISS_EFFECT_NS=GAP_NS + LOCAL_COST_NS
HIT_EFFECT_NS=REALIZE_NS + LOCAL_COST_NS

@dataclass(frozen=True)
class Case:
    case_id:int
    history:Tuple[int,int,int]
    realized:int
    category:str


def current_only_select(case:Case):
    return (1,)


def temporal_select(case:Case):
    h=case.history
    if h[0] < h[1] < h[2]: return (1,)
    if h[0] > h[1] > h[2]: return (-1,)
    return (1,)


def admit(prepared, realized, *, authority=True, expired=False):
    if not authority or expired: return False
    return realized in prepared


def virtual_effect_latency_ns(prepared, realized, *, authority=True, expired=False):
    # Every effect is gated by fresh realized state. A prepared miss never executes;
    # it waits until the gap deadline, then exact-plans the current state.
    if admit(prepared, realized, authority=authority, expired=expired):
        return LOCAL_COST_NS
    return (GAP_NS-REALIZE_NS)+LOCAL_COST_NS
