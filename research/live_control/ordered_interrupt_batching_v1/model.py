from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

VALID_KINDS = {
    'PROGRESS': 1,
    'NEEDS_DECISION': 2,
    'TARGET_LOST': 3,
    'LEASE_EXPIRED': 4,
    'GOAL_REACHED': 3,
    'TERMINAL': 4,
}

@dataclass(frozen=True)
class Event:
    record_id: str
    session: str
    delivery_index: int
    arrival: int
    kind: str
    priority: int
    evidence_id: str

    def to_dict(self):
        return asdict(self)


def validate(events: Iterable[Event]) -> list[Event]:
    xs = list(events)
    seen = set()
    last_idx = -1
    for e in xs:
        if not isinstance(e, Event):
            raise ValueError('invalid_event_type')
        if e.record_id in seen:
            raise ValueError('duplicate_record_id')
        seen.add(e.record_id)
        if e.delivery_index <= last_idx:
            raise ValueError('nonmonotonic_delivery_index')
        last_idx = e.delivery_index
        if e.kind not in VALID_KINDS:
            raise ValueError('invalid_kind')
        if e.priority != VALID_KINDS[e.kind]:
            raise ValueError('invalid_priority')
        if e.session not in {'A','B'}:
            raise ValueError('invalid_session')
        if not isinstance(e.arrival, int) or e.arrival < 0:
            raise ValueError('invalid_arrival')
    return xs


def individual(events: Iterable[Event]) -> list[dict]:
    xs = validate(events)
    return [{'delivery_id': f'd{i}', 'events': [e.to_dict()]} for i,e in enumerate(xs)]


def ordered_batch(events: Iterable[Event], batch_size: int = 4) -> list[dict]:
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError('invalid_batch_size')
    xs = validate(events)
    out=[]
    for start in range(0,len(xs),batch_size):
        chunk=xs[start:start+batch_size]
        if not chunk:
            continue
        out.append({
            'batch_id': f'b{start//batch_size}',
            'events': [e.to_dict() for e in chunk],
            'highest_priority': max(e.priority for e in chunk),
            'first_arrival': min(e.arrival for e in chunk),
            'last_arrival': max(e.arrival for e in chunk),
            'sessions': list(dict.fromkeys(e.session for e in chunk)),
            'input_authority': False,
            'semantic_authority': False,
            'resolution_claim': None,
        })
    return out


def priority_sorted_batch(events: Iterable[Event], batch_size: int = 4) -> list[dict]:
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError('invalid_batch_size')
    xs = validate(events)
    out=[]
    for start in range(0,len(xs),batch_size):
        chunk=xs[start:start+batch_size]
        ordered=sorted(chunk,key=lambda e:(-e.priority,e.delivery_index))
        out.append({'batch_id':f'n{start//batch_size}','events':[e.to_dict() for e in ordered]})
    return out


def flatten(deliveries: list[dict]) -> list[dict]:
    return [event for delivery in deliveries for event in delivery['events']]
