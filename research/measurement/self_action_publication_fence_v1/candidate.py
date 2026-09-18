from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    scope: str
    visual_guard: bool
    covered_action_seq: int

class PublicationFence:
    def __init__(self, scope: str):
        if not isinstance(scope, str) or not scope:
            raise ValueError('bad_scope')
        self.scope = scope
        self.action_seq = 0
        self.actions: dict[str, tuple[int, bool]] = {}
        self.evidences: dict[str, Evidence] = {}
        self.effects = 0

    def self_action(self, action_id: str, relevant: bool) -> dict:
        if not isinstance(action_id, str) or not action_id:
            raise ValueError('bad_action_id')
        if not isinstance(relevant, bool):
            raise ValueError('bad_relevant')
        prior = self.actions.get(action_id)
        if prior is not None:
            if prior[1] != relevant:
                raise ValueError('conflicting_duplicate_action')
            return {'result': 'DUPLICATE_NOOP', 'action_seq': prior[0]}
        self.action_seq += 1
        self.actions[action_id] = (self.action_seq, relevant)
        return {'result': 'RECORDED', 'action_seq': self.action_seq}

    def observe(self, evidence_id: str, visual_guard: bool, covered_action_seq: int) -> dict:
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError('bad_evidence_id')
        if not isinstance(visual_guard, bool):
            raise ValueError('bad_visual_guard')
        if not isinstance(covered_action_seq, int) or covered_action_seq < 0:
            raise ValueError('bad_covered_action_seq')
        if covered_action_seq > self.action_seq:
            raise ValueError('future_covered_action_seq')
        ev = Evidence(evidence_id, self.scope, visual_guard, covered_action_seq)
        prior = self.evidences.get(evidence_id)
        if prior is not None:
            if prior != ev:
                raise ValueError('conflicting_duplicate_evidence')
            return {'result': 'DUPLICATE_NOOP', 'evidence_id': evidence_id}
        self.evidences[evidence_id] = ev
        return {'result': 'PUBLISHED', 'evidence_id': evidence_id}

    def latest_relevant_action_seq(self) -> int:
        seqs = [seq for seq, relevant in self.actions.values() if relevant]
        return max(seqs, default=0)

    def try_effect(self, evidence_id: str, ordinary_authority: bool, presented_scope: str | None = None) -> dict:
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError('bad_effect_evidence_id')
        if not isinstance(ordinary_authority, bool):
            raise ValueError('bad_ordinary_authority')
        scope = self.scope if presented_scope is None else presented_scope
        ev = self.evidences.get(evidence_id)
        admitted = True
        reason = 'ADMIT'
        if scope != self.scope:
            admitted, reason = False, 'WRONG_SCOPE'
        elif ev is None:
            admitted, reason = False, 'EVIDENCE_MISSING'
        elif ev.scope != self.scope:
            admitted, reason = False, 'EVIDENCE_SCOPE_MISMATCH'
        elif not ordinary_authority:
            admitted, reason = False, 'ORDINARY_AUTHORITY_FALSE'
        elif not ev.visual_guard:
            admitted, reason = False, 'VISUAL_GUARD_FALSE'
        elif self.latest_relevant_action_seq() > ev.covered_action_seq:
            admitted, reason = False, 'WAIT_FRESH_PUBLICATION'
        if admitted:
            self.effects += 1
        return {'admitted': admitted, 'reason': reason, 'evidence_id': evidence_id}

    def snapshot(self) -> dict:
        return {
            'scope': self.scope,
            'action_seq': self.action_seq,
            'actions': {k: {'seq': v[0], 'relevant': v[1]} for k, v in sorted(self.actions.items())},
            'evidences': {k: asdict(v) for k, v in sorted(self.evidences.items())},
            'effects': self.effects,
            'latest_relevant_action_seq': self.latest_relevant_action_seq(),
        }
