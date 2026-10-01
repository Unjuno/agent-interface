"""Notification-only gap policy. No database writes, timers, threads or authority."""
from __future__ import annotations
import hashlib
import json
from typing import Any

BUDGET_NS = 80_000_000
POLICIES = ('OBS_COUNT_3', 'ELAPSED_80MS')

class GapPolicy:
    def __init__(self, policy: str) -> None:
        if policy not in POLICIES:
            raise ValueError('unknown policy')
        self.policy = policy
        self.state: dict[str, Any] | None = None

    def clear(self) -> None:
        self.state = None

    def observe(self, key: list[Any], now_ns: int) -> dict[str, Any]:
        if type(now_ns) is not int or now_ns < 0:
            raise ValueError('invalid monotonic timestamp')
        if self.state is None or self.state['key'] != key:
            self.state = dict(key=list(key), first_ns=now_ns, count=0, receipt=None)
        s = self.state
        if now_ns < s['first_ns']:
            raise ValueError('clock regression')
        if s['receipt'] is None:
            s['count'] += 1
            due = (s['count'] >= 3 if self.policy == 'OBS_COUNT_3'
                   else now_ns - s['first_ns'] >= BUDGET_NS)
            if due:
                material = json.dumps([key, s['first_ns']], separators=(',', ':'))
                s['receipt'] = {
                    'type': 'RESYNC_REQUIRED',
                    'id': hashlib.sha256(material.encode()).hexdigest(),
                    'key': list(key), 'first_ns': s['first_ns'],
                    'authority': False,
                }
        return dict(status='RESYNC_REQUIRED' if s['receipt'] else 'EVENT_PREDECESSOR_MISSING',
                    state=json.loads(json.dumps(s)))
