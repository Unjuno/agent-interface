from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Policy(str, Enum):
    BLIND_FULL = 'blind_full_retry'
    SENDER_SUFFIX = 'sender_count_suffix'
    OBSERVED_PREFIX = 'observed_prefix_suffix'

@dataclass(frozen=True)
class RecoveryDecision:
    accepted: bool
    text: str
    reason: str

def decide(policy: Policy, desired: str, sent_count: int, observed: str) -> RecoveryDecision:
    if not isinstance(desired, str) or not isinstance(observed, str):
        raise TypeError('text must be str')
    if type(sent_count) is not int or not 0 <= sent_count <= len(desired):
        raise ValueError('invalid sent_count')
    if policy is Policy.BLIND_FULL:
        return RecoveryDecision(True, desired, 'blind_full')
    if policy is Policy.SENDER_SUFFIX:
        return RecoveryDecision(True, desired[sent_count:], 'sender_count')
    if policy is Policy.OBSERVED_PREFIX:
        if desired.startswith(observed):
            return RecoveryDecision(True, desired[len(observed):], 'observed_exact_prefix')
        return RecoveryDecision(False, '', 'observed_not_prefix')
    raise ValueError('unknown policy')
