from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Policy(str, Enum):
    CONTENT_ONLY = 'content_only_prefix'
    BOUND_PREFIX = 'bound_prefix'

@dataclass(frozen=True)
class Observation:
    text: str
    sequence: int
    binding_revision: int
    target_id: int
    observed_ns: int

@dataclass(frozen=True)
class Context:
    current_sequence: int
    current_revision: int
    expected_target: int
    current_focus: int
    now_ns: int
    max_age_ns: int

@dataclass(frozen=True)
class Decision:
    accepted: bool
    text: str
    reason: str

def decide(policy: Policy, desired: str, obs: Observation, ctx: Context) -> Decision:
    if not desired.startswith(obs.text):
        return Decision(False, '', 'observed_not_prefix')
    if policy is Policy.CONTENT_ONLY:
        return Decision(True, desired[len(obs.text):], 'content_prefix_only')
    if policy is not Policy.BOUND_PREFIX:
        raise ValueError('unknown policy')
    if obs.sequence != ctx.current_sequence:
        return Decision(False, '', 'stale_sequence')
    if obs.binding_revision != ctx.current_revision:
        return Decision(False, '', 'stale_binding')
    if obs.target_id != ctx.expected_target:
        return Decision(False, '', 'wrong_target')
    age = ctx.now_ns - obs.observed_ns
    if age < 0 or age > ctx.max_age_ns:
        return Decision(False, '', 'stale_age')
    if ctx.current_focus != ctx.expected_target:
        return Decision(False, '', 'focus_mismatch')
    return Decision(True, desired[len(obs.text):], 'bound_prefix_valid')
