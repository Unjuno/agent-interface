"""Offline bounds and behavior controls for bounded effect waits."""
import hashlib
import json
import tempfile
import threading
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v6 import initialize, run
from effect_checkpoint_v3 import Checkpoints


H = Path(__file__).resolve().parent
R = H / 'results/effect-wait-controls-01'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['probe_effect_wait_v1.py', 'effect_checkpoint_v3.py',
         'effect_checkpoint_v2.py', 'effect_checkpoint.py',
         'durable_submit_v6.py', 'checkpoint_contract_v1.py',
         'append_checkpoint_v1.py']
dump('plan.json', {
    'scope': 'offline wait behavior and pre-transport bounds; no GUI or model calls',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})

contract = {'kind': 'saved_form_value', 'expected': 'bounded'}
with tempfile.TemporaryDirectory(prefix='effect-wait-controls-') as raw:
    root = Path(raw)
    records = []
    signal = threading.Event()

    def emit(record):
        records.append(record)
        signal.set()

    service = Checkpoints(emit, root / 'archive')
    missing = root / 'missing.txt'
    service.request(missing, contract, {'transport_request_id': 'timeout'},
                    wait_ms=100, poll_ms=20)
    assert signal.wait(2)
    timeout_record = records.pop()
    signal.clear()
    timeout_evidence = timeout_record['evidence']
    assert timeout_evidence['status'] == 'UNKNOWN'
    assert timeout_evidence['sample_attempts'] >= 2
    assert timeout_evidence['wait_requested_ms'] == 100
    assert timeout_evidence['poll_requested_ms'] == 20

    target = root / 'appears.txt'
    timer = threading.Timer(0.1, lambda: target.write_text('value=bounded', encoding='utf-8'))
    timer.start()
    service.request(target, contract, {'transport_request_id': 'verified'},
                    wait_ms=500, poll_ms=20)
    assert signal.wait(2)
    verified_record = records.pop()
    verified_evidence = verified_record['evidence']
    assert verified_evidence['status'] == 'VERIFIED'
    assert verified_evidence['sample_attempts'] >= 2
    timer.join()

    refused = []
    invalid_service = [
        {'wait_ms': -1, 'poll_ms': 20}, {'wait_ms': 10001, 'poll_ms': 20},
        {'wait_ms': 100, 'poll_ms': 9}, {'wait_ms': 100, 'poll_ms': 501},
        {'wait_ms': 10, 'poll_ms': 20}, {'wait_ms': 1.0, 'poll_ms': 20},
    ]
    for options in invalid_service:
        try:
            service.request(missing, contract, {'transport_request_id': 'invalid'}, **options)
        except ValueError as exc:
            refused.append({'layer': 'service', 'options': options, 'error': str(exc)})
        else:
            raise AssertionError('invalid service bounds accepted')
    service.close()

    archived = read_initial = json.loads(
        (H / 'results/effect-wait-ab-01/poll/initial.json').read_text(encoding='utf-8'))
    invalid_journal = [
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 100},
        {'op': 'effect_checkpoint', 'contract': contract, 'poll_ms': 20},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': -1, 'poll_ms': 20},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 10001, 'poll_ms': 20},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 100, 'poll_ms': 9},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 100, 'poll_ms': 501},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 10, 'poll_ms': 20},
        {'op': 'effect_checkpoint', 'contract': contract, 'wait_ms': 100,
         'poll_ms': 20, 'extra': True},
    ]
    for index, command in enumerate(invalid_journal):
        journal = root / f'journal-{index}.jsonl'
        initialize(journal, archived['continuation'])
        before = load(journal)
        try:
            run(journal, {'command': command, 'timeout': 0})
        except ValueError as exc:
            refused.append({'layer': 'journal', 'command': command, 'error': str(exc)})
        else:
            raise AssertionError('invalid journal command accepted')
        assert load(journal) == before

result = {
    'timeout_status': timeout_evidence['status'],
    'timeout_sample_attempts': timeout_evidence['sample_attempts'],
    'verified_status': verified_evidence['status'],
    'verified_sample_attempts': verified_evidence['sample_attempts'],
    'invalid_controls': len(refused), 'model_calls': 0, 'gui_actions': 0,
}
dump('refusals.json', refused)
dump('result.json', result)
print(json.dumps(result, indent=2))
