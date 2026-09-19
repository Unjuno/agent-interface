"""Explicit model-reviewed patch-servo task through socket and compact receipt."""
import json
import sys
import uuid
from pathlib import Path
from pointer_exchange_v1 import run
from decision_receipt_v3 import build
from receipt_image import select_image
from report_pages_v2 import digest
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent


def main():
    stage, socket, directory = sys.argv[1:]
    assert stage in ('initial', 'servo', 'save', 'finish')
    root = Path(directory)
    runtime = root / 'runtime'
    out = root / stage
    out.mkdir(exist_ok=False)
    def save(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    def read(path):
        return json.loads((root / path).read_text())
    def query(q):
        n = len(list(out.glob('query-*-request.json')))
        save(f'query-{n}-request', q)
        reply = exchange(socket, q, timeout=16)
        save(f'query-{n}-reply', reply)
        return reply
    if stage == 'initial':
        names = ['cause_servo_live_v1.py', 'cause_servo_session_v1.py', 'cause_servo_interactive_v1.py',
                 'cause_servo_socket_v1.py', 'session_v21.py', 'patch_servo_v5.py',
                 'executor_v5.py', 'input_owner_v10.py', 'lease_cause_v2.py',
                 'pointer_exchange_v1.py', 'decision_receipt_v3.py', 'score_drag_v1.py']
        save('plan', {'sources': {n: digest((HERE / n).read_bytes()) for n in names},
                     'allocation': 'one fresh Inkscape seed 215; no implicit retries',
                     'target': '20 screen pixels right at 118%; saved x=66.95 +/-1, y/width/height=50/40/30 +/-0.1',
                     'scope': 'existing patch policy plus cause/wake integration and model self-use; no paired speed claim',
                     'verified_model_id': None, 'model_tokens': None})
        batch = query({'after': 0, 'events': ['observation'], 'timeout': 5})
        save('batch', batch)
        result = {'batch': batch, 'image': select_image(batch, runtime)}
    elif stage in ('servo', 'save'):
        batch = read('initial/batch.json') if stage == 'servo' else read('servo/report.json')['last_reply']
        source = select_image(batch, runtime)
        steps = ([{'op': 'pointer_servo', 'source_sequence': source['sequence'],
                   'box': [592, 369, 56, 44], 'target_delta': [20, 0],
                   'points': [{'x': 618, 'y': 391}, {'x': 628, 'y': 391}],
                   'duration_ms': 100, 'max_corrections': 3}]
                 if stage == 'servo' else
                 [{'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                  {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}])
        save('steps', steps)
        report = run(query, batch, runtime, stage, steps, 30000, save)
        save('report', report)
        receipt = build((out / 'report.json').read_bytes())
        save('receipt', receipt)
        result = {'receipt': receipt, 'image': report.get('image')}
    else:
        batch = read('save/report.json')['last_reply']
        result = query({'after': batch['cursor'], 'events': ['independent_evaluation'], 'timeout': 5,
                        'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
    save('result', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
