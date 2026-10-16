"""Executor control with synthetic owner release; not an X11 integration test."""
import json
import threading
import time
from pathlib import Path
from executor_v4 import Executor
from executor_v3 import DecisionRequired
from lease_cause_v1 import Lease
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def main():
    deadline = time.perf_counter_ns() + 10_000_000_000
    first, second = Lease(deadline), Lease(deadline)
    record = {'event': 'owner_release', 'reason': 'focus_changed', 'verified': True,
              'verified_ns': time.perf_counter_ns(), 'valid_until_ns': deadline}
    first.record_interruption(record)
    record['reason'] = 'surface_changed'
    first.record_interruption(record)
    assert first.interruption_snapshot()['record']['reason'] == 'focus_changed'
    assert second.interruption_snapshot() is None
    snapshot = first.interruption_snapshot()
    snapshot['record']['reason'] = 'corrupted'
    assert first.interruption_snapshot()['record']['reason'] == 'focus_changed'
    class Backend:
        sequence = 1
        def validate(self, steps):
            pass
        def execute(self, step, lease, identifier, index):
            if step['op'] == 'interrupt':
                lease.record_interruption({'event': 'owner_release', 'reason': 'focus_changed',
                                           'verified': True, 'verified_ns': time.perf_counter_ns()})
                raise DecisionRequired('observed focus mismatch')
        def release_all(self):
            record = {'event': 'owner_release', 'reason': 'release', 'verified': True}
            self.lease.record_interruption(record)
            return record
    events, done = [], threading.Event()
    def emit(event):
        events.append(event)
        if event['event'] == 'terminal':
            done.set()
    executor = Executor(Backend(), emit)
    executor.submit('first', [{'op': 'interrupt'}], 1, deadline)
    assert done.wait(2)
    with executor.lock:
        assert executor.active is None
    done.clear()
    executor.submit('second', [{'op': 'ok'}], 1, deadline)
    assert done.wait(2)
    executor.close()
    terminals = [e for e in events if e['event'] == 'terminal']
    assert terminals[0]['status'] == 'needs_decision'
    assert terminals[0]['decision_reason'] == 'observed focus mismatch'
    assert terminals[0]['interruption']['record']['reason'] == 'focus_changed'
    assert terminals[0]['release']['reason'] == 'release'
    assert terminals[1]['status'] == 'completed' and terminals[1]['interruption'] is None
    result = {'sources': {p.name: digest(p.read_bytes()) for p in (Path(__file__), HERE / 'lease_cause_v1.py', HERE / 'executor_v4.py', HERE / 'input_owner_v10.py')},
              'first_cause_preserved': True, 'snapshot_isolated': True,
              'same_deadline_distinct_intents_isolated': True, 'terminals': terminals,
              'scope': 'Synthetic owner release through real executor threads; input_owner_v10 compiled but not executed against X11. No live readiness or speed claim.'}
    out = HERE / 'results/lease-cause-01'
    out.mkdir(exist_ok=True)
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
