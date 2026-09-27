from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import coarse_model_dependency as coarse
import preflight_dependency as direct

CLIPBOARD_EFFECTS=frozenset({coarse.SideEffect.CLIPBOARD_CONTENT,coarse.SideEffect.CLIPBOARD_OWNER,coarse.SideEffect.CLIPBOARD_TARGETS})

@dataclass(frozen=True)
class PayloadDecision:
    selected: str | None
    direct_preflight_ok: bool
    direct_preflight_error: str | None
    coarse_selected: str | None
    decision: coarse.Decision

def coverage_for(text: str) -> coarse.TextCoverage:
    return coarse.TextCoverage.ASCII if all(ord(ch) < 128 for ch in text) else coarse.TextCoverage.UNICODE

def choose_payload_aware(text: str, mapping: list[list[int]], first_code: int, allowed_side_effects=frozenset()) -> PayloadDecision:
    try:
        direct.prepare(text,mapping,first_code); ok=True; err=None
    except direct.Rejected as exc:
        ok=False; err=str(exc)
    req=coarse.Request(coverage_for(text),frozenset(allowed_side_effects))
    coarse_decision=coarse.choose_route(coarse.x11_evidence_profile(),req)
    routes=list(coarse.x11_evidence_profile())
    if not ok:
        r=routes[0]
        routes[0]=coarse.Route(r.name,coarse.CapabilityState.UNSUPPORTED,r.coverage,r.side_effects,r.exact_semantics_observed,r.permission)
    decision=coarse.choose_route(routes,req)
    return PayloadDecision(decision.selected,ok,err,coarse_decision.selected,decision)
