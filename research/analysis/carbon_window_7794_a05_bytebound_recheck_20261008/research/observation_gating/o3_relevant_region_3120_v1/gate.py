"""Pure O3 relevant-region admission evaluator.

This module deliberately has no GUI, input, model, provider, or authority side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RegionDecision:
    admitted: bool
    reason: str


def evaluate_region(
    evidence: Mapping[str, Any],
    *,
    observation_id: str,
    intent_epoch: int,
    region_id: str,
) -> RegionDecision:
    """Admit only a complete, current, authority-free region evidence record."""
    if not isinstance(evidence, Mapping):
        return RegionDecision(False, "malformed")
    if evidence.get("observation_id") != observation_id:
        return RegionDecision(False, "stale_observation")
    if evidence.get("intent_epoch") != intent_epoch:
        return RegionDecision(False, "stale_intent")
    if evidence.get("region_id") != region_id:
        return RegionDecision(False, "region_mismatch")
    if evidence.get("coverage") != "COMPLETE":
        return RegionDecision(False, "incomplete_coverage")
    if evidence.get("freshness") != "CURRENT":
        return RegionDecision(False, "stale_freshness")
    if evidence.get("effect_binding") != "BOUND":
        return RegionDecision(False, "unbound_effect")
    if evidence.get("authority_grants", 0) != 0:
        return RegionDecision(False, "authority_present")
    if evidence.get("ambiguous", False):
        return RegionDecision(False, "ambiguous")
    return RegionDecision(True, "admitted")
