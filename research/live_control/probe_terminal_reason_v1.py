"""Synthetic regression for empty exception reasons and per-intent isolation."""
import json
import time
from pathlib import Path
from executor_v6 import Executor
from executor_v3 import DecisionRequired
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent
out = HERE / 'results/terminal-reason-01'
out.mkdir(exist_ok=False)
rows = []
cases = [('focus_changed', '', True, 'focus_changed'),
         ('surface_changed', '', True, 'surface_changed'),
         ('focus_changed', 'explicit-detail', True, 'explicit-detail'),
         (None, '', True, None), ('expired', '', True, None),
         ('cancelled', '', True, None), ('stop_requested', '', True, None),
         ('focus_changed', '', False, None)]
for cause, explicit, release_ok, expected in cases:
    events = []
    class Backend:
        sequence = 1
        def validate(self, steps):
            assert steps == [{'op': 'fault'}] or steps == [{'op': 'observe'}]
        def execute(self, step, lease, identifier, index):
            if step['op'] == 'observe':
                return
            if cause:
                lease.record_interruption(dict(event='owner_release', reason=cause,
                    verified=True, keys_down=[], buttons_down=[]))
            raise DecisionRequired(explicit)
        def release_all(self):
            return dict(verified=release_ok if len(events) < 4 else True)
    backend = Backend()
    engine = Executor(backend, events.append)
    deadline = time.perf_counter_ns() + 5_000_000_000
    try:
        engine.submit('fault', [{'op': 'fault'}], 1, deadline)
        with engine.lock:
            job = engine.active
        if job:
            job[2].join(2)
            assert not job[2].is_alive()
        first = events[-1]
        assert first['status'] == ('needs_decision' if release_ok else 'failed')
        assert first['decision_reason'] == expected
        engine.submit('fresh', [{'op': 'observe'}], 1, deadline)
        with engine.lock:
            job = engine.active
        if job:
            job[2].join(2)
            assert not job[2].is_alive()
        fresh = events[-1]
        assert fresh['status'] == 'completed' and fresh['decision_reason'] is None
        assert fresh['interruption'] is None
        rows.append(dict(cause=cause, explicit=explicit, release_ok=release_ok, events=events))
    finally:
        engine.close()
result = dict(success=True, scope='synthetic; no X11 or model performance claim', cases=rows,
    sources={n: digest((HERE/n).read_bytes()) for n in ['probe_terminal_reason_v1.py',
    'executor_v6.py', 'lease_cause_v1.py', 'lease_cause_v2.py']})
(out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(dict(success=True, cases=len(rows))))
