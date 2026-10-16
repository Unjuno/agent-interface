"""Controlled executor boundaries and wake behavior; synthetic owner records."""
import json
import threading
import time
from pathlib import Path
from executor_v5 import Executor
from lease_cause_v2 import Lease
from report_pages_v2 import digest

HERE = Path(__file__).resolve().parent


def record(reason):
    return {'event': 'owner_release', 'reason': reason, 'verified': True,
            'keys_down': [], 'buttons_down': [], 'verified_ns': time.perf_counter_ns()}


def main():
    out = HERE / 'results/interrupt-wake-01'
    out.mkdir(exist_ok=False)
    result = {'sources': {n: digest((HERE / n).read_bytes()) for n in
              ['probe_interrupt_wake_v1.py', 'executor_v5.py', 'lease_cause_v2.py', 'lease_cause_v1.py', 'lease.py']},
              'cases': [], 'scope': 'synthetic interruption injection, not X11 or app performance'}
    cases = [('focus_changed', 'wait', 'needs_decision'), ('surface_changed', 'wait', 'needs_decision'),
             ('expired', 'wait', 'expired'), ('cancelled', 'wait', 'cancelled'),
             ('stop_requested', 'wait', 'cancelled'), ('focus_changed', 'return', 'needs_decision'),
             ('focus_changed', 'cleanup', 'needs_decision'), (None, 'wait', 'completed'),
             (None, 'cancel', 'cancelled')]
    try:
        for reason, phase, expected in cases:
            events = []
            entered, proceed, done = threading.Event(), threading.Event(), threading.Event()
            class Backend:
                sequence = 1
                def validate(self, steps):
                    assert steps == [{'op': 'one'}]
                def execute(self, step, lease, identifier, index):
                    entered.set()
                    if phase == 'return':
                        assert proceed.wait(2)
                    elif phase in ('wait', 'cancel'):
                        if lease.wait(.5):
                            from executor_v3 import Cancelled
                            raise Cancelled()
                def release_all(self):
                    if phase == 'cleanup':
                        self.lease.record_interruption(record(reason))
                    return record('release')
            backend = Backend()
            def emit(e):
                events.append(e)
                if e['event'] == 'terminal':
                    done.set()
            executor = Executor(backend, emit)
            try:
                executor.submit('one', [{'op': 'one'}], 1, time.perf_counter_ns() + 5_000_000_000)
                assert entered.wait(2)
                injected = time.perf_counter_ns()
                if reason is not None and phase != 'cleanup':
                    backend.lease.record_interruption(record(reason))
                if phase == 'cancel':
                    executor.cancel('one')
                proceed.set()
                assert done.wait(2)
                terminal = events[-1]
                result['cases'].append({'reason': reason, 'phase': phase, 'expected': expected,
                                        'events': events, 'inject_to_terminal_ms': (terminal['terminal_ns'] - injected) / 1e6})
                assert terminal['status'] == expected
                if phase in ('wait', 'return', 'cancel') and expected != 'completed':
                    assert terminal['steps_completed'] == 0
                if reason is not None:
                    assert terminal['interruption']['record']['reason'] == reason
                else:
                    assert terminal['interruption'] is None
                if reason is not None and phase == 'wait':
                    assert terminal['terminal_ns'] - injected < 400_000_000, 'wait did not wake before original 500ms interval'
            finally:
                proceed.set()
                executor.close()
        deadline = time.perf_counter_ns() + 5_000_000_000
        old, fresh = Lease(deadline), Lease(deadline)
        old.record_interruption(record('focus_changed'))
        fresh.record_interruption(record('release'))
        fresh.check()
        assert fresh.interruption_snapshot() is None and old.intent_token != fresh.intent_token
        result['same_deadline_isolation'] = True
        result['success'] = True
    except Exception as exc:
        result.update(success=False, error=repr(exc))
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'success': result['success'], 'cases': len(result['cases']), 'error': result.get('error')}))
    if not result['success']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
