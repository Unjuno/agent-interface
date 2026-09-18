from __future__ import annotations
from dataclasses import dataclass, field

CLEAR = 'CLEAR'
HARD = 'HARD'

@dataclass(frozen=True)
class Prepared:
    decision_id: str
    scope: str
    generation: int
    state: str
    prepared_ns: int

@dataclass
class Authority:
    scope: str
    generation: int = 1
    closed: bool = False
    raw_recv_return_ns: int | None = None
    authority_publish_ns: int | None = None
    published_event_id: str | None = None
    consumed_decisions: set[str] = field(default_factory=set)
    effects: int = 0

    def prepare(self, decision_id: str, state: str, prepared_ns: int) -> Prepared:
        if not isinstance(decision_id, str) or not decision_id:
            raise ValueError('bad_decision_id')
        if state not in (CLEAR, HARD):
            raise ValueError('bad_state')
        if not isinstance(prepared_ns, int) or prepared_ns < 0:
            raise ValueError('bad_prepared_ns')
        return Prepared(decision_id, self.scope, self.generation, state, prepared_ns)

    def raw_receive(self, raw_ns: int) -> None:
        if not isinstance(raw_ns, int) or raw_ns < 0:
            raise ValueError('bad_raw_ns')
        if self.raw_recv_return_ns is not None:
            raise ValueError('duplicate_raw_receive')
        self.raw_recv_return_ns = raw_ns

    def publish_return(self, event_id: str, publish_ns: int) -> str:
        if not isinstance(event_id, str) or not event_id:
            raise ValueError('bad_event_id')
        if not isinstance(publish_ns, int) or publish_ns < 0:
            raise ValueError('bad_publish_ns')
        if self.raw_recv_return_ns is None:
            raise ValueError('publish_without_raw_receive')
        if publish_ns < self.raw_recv_return_ns:
            raise ValueError('publish_before_raw_receive')
        if self.published_event_id is not None:
            if event_id == self.published_event_id:
                return 'DUPLICATE_NOOP'
            raise ValueError('second_publication_event')
        self.authority_publish_ns = publish_ns
        self.closed = True
        self.generation += 1
        self.published_event_id = event_id
        return 'PUBLISHED'

    def try_admit(self, prepared: Prepared, commit_ns: int, ordinary_authority: bool,
                  presented_scope: str | None = None, presented_generation: int | None = None) -> dict:
        if not isinstance(commit_ns, int) or commit_ns < 0:
            raise ValueError('bad_commit_ns')
        if not isinstance(ordinary_authority, bool):
            raise ValueError('bad_ordinary_authority')
        if not isinstance(prepared, Prepared):
            raise ValueError('bad_prepared')
        scope = prepared.scope if presented_scope is None else presented_scope
        gen = prepared.generation if presented_generation is None else presented_generation
        reason = 'ADMIT'
        admitted = True
        if scope != self.scope or prepared.scope != self.scope:
            admitted, reason = False, 'WRONG_SCOPE'
        elif not isinstance(gen, int) or gen < 1:
            admitted, reason = False, 'BAD_GENERATION'
        elif prepared.decision_id in self.consumed_decisions:
            admitted, reason = False, 'REPLAY'
        elif self.authority_publish_ns is not None and commit_ns >= self.authority_publish_ns:
            admitted, reason = False, 'CLOSED_AFTER_PUBLICATION'
        elif self.closed:
            admitted, reason = False, 'CLOSED'
        elif gen != self.generation or prepared.generation != self.generation:
            admitted, reason = False, 'STALE_OR_FORGED_GENERATION'
        elif prepared.state != CLEAR:
            admitted, reason = False, 'NONCLEAR_STATE'
        elif not ordinary_authority:
            admitted, reason = False, 'ORDINARY_AUTHORITY_FALSE'
        if admitted:
            self.consumed_decisions.add(prepared.decision_id)
            self.effects += 1
        return {
            'admitted': admitted,
            'reason': reason,
            'commit_ns': commit_ns,
            'generation_at_commit': self.generation,
            'closed_at_commit': self.closed,
        }

    def snapshot(self) -> dict:
        return {
            'scope': self.scope,
            'generation': self.generation,
            'closed': self.closed,
            'raw_recv_return_ns': self.raw_recv_return_ns,
            'authority_publish_ns': self.authority_publish_ns,
            'published_event_id': self.published_event_id,
            'consumed_decisions': sorted(self.consumed_decisions),
            'effects': self.effects,
        }
