"""Research-only buffering policies; no X11, action, acknowledgement, or replay."""
from copy import deepcopy

KINDS = {'STATE', 'FOCUS_LOST', 'FOCUS_RESTORED'}

class Buffers:
    def __init__(self, sessions, cap=4):
        if type(cap) is not int or cap < 1 or len(sessions) != len(set(sessions)):
            raise ValueError('configuration')
        self.cap = cap
        self.sessions = tuple(sessions)
        self.last = {s: 0 for s in sessions}
        self.latest = {}; self.states = {}; self.events = {s: [] for s in sessions}
        self.bounded = {s: [] for s in sessions}; self.overflow = {}
        self.peak_bounded = 0

    def ingest(self, record):
        if not isinstance(record, dict) or set(record) != {'session', 'seq', 'kind', 'evidence'}:
            raise ValueError('record shape')
        s, q, k = record['session'], record['seq'], record['kind']
        if type(s) is not str or s not in self.last:
            raise ValueError('session')
        if type(q) is not int or q != self.last[s] + 1:
            raise ValueError('sequence')
        if type(k) is not str or k not in KINDS or not isinstance(record['evidence'], dict):
            raise ValueError('kind/evidence')
        r = deepcopy(record)
        self.last[s] = q; self.latest[s] = r
        if k == 'STATE':
            self.states[s] = r
        else:
            self.events[s].append(r)
            if len(self.bounded[s]) < self.cap:
                self.bounded[s].append(r)
            else:
                o = self.overflow.setdefault(s, {'first_unretained_seq':q,
                    'first_unretained_kind':k, 'unretained_count':0, 'status':'RESYNC_REQUIRED'})
                o['unretained_count'] += 1
        self.peak_bounded = max(self.peak_bounded, *(len(v) for v in self.bounded.values()))

    def package(self):
        out = {}
        for mode in ('LATEST_ONLY', 'SPLIT_UNBOUNDED', 'SPLIT_CAP4'):
            streams = {}
            for s in self.sessions:
                if mode == 'LATEST_ONLY':
                    r = self.latest.get(s)
                    state = r if r and r['kind'] == 'STATE' else None
                    events = [r] if r and r['kind'] != 'STATE' else []
                    overflow = None
                else:
                    state = self.states.get(s)
                    events = self.events[s] if mode == 'SPLIT_UNBOUNDED' else self.bounded[s]
                    overflow = self.overflow.get(s) if mode == 'SPLIT_CAP4' else None
                streams[s] = {'latest_state':state, 'events':events, 'overflow':overflow,
                              'coverage_complete':overflow is None}
            out[mode] = {'streams':streams, 'grants_input_authority':False,
                         'acknowledges_consumption':False}
        return deepcopy(out)
