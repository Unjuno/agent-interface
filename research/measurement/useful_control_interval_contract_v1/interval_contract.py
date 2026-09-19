from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

@dataclass(frozen=True, order=True)
class Interval:
    start_ns: int
    end_ns: int
    def __post_init__(self):
        if self.start_ns < 0 or self.end_ns < self.start_ns:
            raise ValueError('invalid interval')
    @property
    def width_ns(self) -> int:
        return self.end_ns - self.start_ns


def intersect(a: Interval, b: Interval) -> Interval | None:
    s, e = max(a.start_ns, b.start_ns), min(a.end_ns, b.end_ns)
    return Interval(s, e) if e > s else None


def merge(intervals: Iterable[Interval]) -> list[Interval]:
    xs = sorted(intervals)
    if not xs:
        return []
    out = [xs[0]]
    for cur in xs[1:]:
        prev = out[-1]
        if cur.start_ns <= prev.end_ns:
            out[-1] = Interval(prev.start_ns, max(prev.end_ns, cur.end_ns))
        else:
            out.append(cur)
    return out


def measure(intervals: Iterable[Interval]) -> int:
    return sum(i.width_ns for i in merge(intervals))

@dataclass(frozen=True)
class ReleaseReceipt:
    lo_ns: int
    hi_ns: int
    post_key_down: bool
    def __post_init__(self):
        if self.lo_ns < 0 or self.hi_ns < self.lo_ns:
            raise ValueError('invalid release interval')

@dataclass(frozen=True)
class Actuation:
    down_ns: int
    release: ReleaseReceipt
    authority: Sequence[Interval]
    actuation_id: str
    def __post_init__(self):
        if self.down_ns < 0 or self.release.lo_ns < self.down_ns:
            raise ValueError('release precedes down')
        if self.release.post_key_down:
            raise ValueError('receipt does not establish released state')

@dataclass(frozen=True)
class Bounds:
    lower_ns: int
    upper_ns: int
    authority_lower_ns: int
    authority_upper_ns: int


def occupancy_bounds(a: Actuation, wait: Interval) -> Bounds:
    lower = Interval(a.down_ns, a.release.lo_ns)
    upper = Interval(a.down_ns, a.release.hi_ns)
    lower_wait = intersect(lower, wait)
    upper_wait = intersect(upper, wait)
    lower_ns = 0 if lower_wait is None else lower_wait.width_ns
    upper_ns = 0 if upper_wait is None else upper_wait.width_ns

    auth = merge(a.authority)
    auth_lower_parts: list[Interval] = []
    auth_upper_parts: list[Interval] = []
    if lower_wait:
        for x in auth:
            y = intersect(lower_wait, x)
            if y:
                auth_lower_parts.append(y)
    if upper_wait:
        for x in auth:
            y = intersect(upper_wait, x)
            if y:
                auth_upper_parts.append(y)
    return Bounds(lower_ns, upper_ns, measure(auth_lower_parts), measure(auth_upper_parts))

@dataclass(frozen=True)
class EffectEvent:
    t_ns: int
    actuation_id: str | None
    independently_scored: bool
    useful: bool


def classify_effects(events: Iterable[EffectEvent], known_actuation_ids: set[str]) -> dict[str, int]:
    out = {'useful_bound': 0, 'useful_unbound': 0, 'nonuseful_bound': 0, 'unscored': 0}
    for e in events:
        if not e.independently_scored:
            out['unscored'] += 1
        elif e.actuation_id in known_actuation_ids:
            out['useful_bound' if e.useful else 'nonuseful_bound'] += 1
        else:
            out['useful_unbound'] += int(e.useful)
    return out


def analyze(wait: Interval, actuations: Sequence[Actuation], events: Sequence[EffectEvent]) -> dict:
    ids = [a.actuation_id for a in actuations]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate actuation_id')
    per = {a.actuation_id: occupancy_bounds(a, wait).__dict__ for a in actuations}
    lower_intervals: list[Interval] = []
    upper_intervals: list[Interval] = []
    auth_lower_intervals: list[Interval] = []
    auth_upper_intervals: list[Interval] = []
    for a in actuations:
        l = intersect(Interval(a.down_ns, a.release.lo_ns), wait)
        u = intersect(Interval(a.down_ns, a.release.hi_ns), wait)
        if l:
            lower_intervals.append(l)
        if u:
            upper_intervals.append(u)
        for x in a.authority:
            if l:
                y = intersect(l, x)
                if y:
                    auth_lower_intervals.append(y)
            if u:
                y = intersect(u, x)
                if y:
                    auth_upper_intervals.append(y)
    return {
        'wait_ns': wait.width_ns,
        'physical_occupancy_lower_ns': measure(lower_intervals),
        'physical_occupancy_upper_ns': measure(upper_intervals),
        'authorized_occupancy_lower_ns': measure(auth_lower_intervals),
        'authorized_occupancy_upper_ns': measure(auth_upper_intervals),
        'per_actuation': per,
        'effects': classify_effects(events, {a.actuation_id for a in actuations}),
    }
