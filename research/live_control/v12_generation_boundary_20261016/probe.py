"""Finite current V4→V12 owner characterization; all X I/O is Fake X."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
LIVE = ROOT / 'research/live_control'
sys.path.insert(0, str(LIVE))
import input_owner_v12 as native
from input_transition_owner_v4 import InputOwner
from lease_cause_v2 import Lease
from test_input_owner_v12_explicit_up_cancel import FakeDisplay


def run_case(name, generation, focus):
    expected = {'xid': 41, 'pid': 123, 'process_identity': '123:100'}
    fake = FakeDisplay()
    fake.get_input_focus = lambda: SimpleNamespace(focus=focus)
    events = []
    def emit(connection, kind, code):
        if connection is not fake:
            raise RuntimeError('unexpected X connection')
        events.append({'kind': kind, 'code': code})
        if kind == native.X.KeyPress:
            fake.down.add(code)
        elif kind == native.X.KeyRelease:
            fake.down.discard(code)
    owner = None
    with patch.object(native.display, 'Display', return_value=fake), patch.object(
            native.xtest, 'fake_input', side_effect=emit):
        try:
            owner = InputOwner(':fake-generation-boundary')
            lease = Lease(time.perf_counter_ns() + 2_000_000_000)
            lease.expected_focus = expected['xid']
            lease.target_generation = dict(expected)
            admission, error = None, None
            try:
                admission = owner.call('down', lease, 'W')
            except Exception as failure:
                error = type(failure).__name__
            held_after_call = sorted(fake.down)
            release = owner.call('release', lease)
            records = owner.records
        finally:
            if owner is not None:
                owner.close()
        thread_stopped = owner._inner.stopped.is_set() and not owner._inner.thread.is_alive()
    return {'case': name, 'source_generation': expected,
            'fixture_current_generation': generation, 'fixture_focus': focus,
            'reference_eligible': generation == expected and focus == expected['xid'],
            'admission': admission, 'error_type': error,
            'events': events, 'held_after_admission_call': held_after_call,
            'release': release, 'owner_records': records,
            'final_fake_keys': sorted(fake.down), 'owner_thread_stopped': thread_stopped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    freeze = json.loads((directory / 'FREEZE.json').read_text())
    for relative, digest in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError('frozen dependency changed: ' + relative)
    # Reserve first output before touching the fake input owner.
    with args.output.open('x', encoding='utf-8') as output:
        cells = [
            ('stable', {'xid': 41, 'pid': 123, 'process_identity': '123:100'}, 41),
            ('same_xid_new_pid', {'xid': 41, 'pid': 456, 'process_identity': '456:200'}, 41),
            ('same_xid_pid_new_start', {'xid': 41, 'pid': 123, 'process_identity': '123:200'}, 41),
            ('changed_focus', {'xid': 41, 'pid': 123, 'process_identity': '123:100'}, 71),
        ]
        rows = [run_case(*cell) for cell in cells]
        raw = {'schema': 'v12-generation-boundary-v1', 'freeze': freeze,
               'runner_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                        cwd=ROOT, text=True).strip(),
               'rows': rows,
               'scope': 'Fake X V4→V12 owner only; metadata is probe-supplied, not a standard caller observation proof',
               'task_success_verified': False}
        output.write(json.dumps(raw, indent=2) + '\n')
        output.flush()
    print(json.dumps({'output': str(args.output), 'cells': len(rows),
                      'stale_admissions': sum(not row['reference_eligible'] and
                                              row['admission'] is not None for row in rows)}))


if __name__ == '__main__':
    main()
