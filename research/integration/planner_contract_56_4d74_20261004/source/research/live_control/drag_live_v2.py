"""Explicit selected-object drag and save; image review between stages."""
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
    assert stage in ('initial', 'select', 'drag', 'finish')
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
        names = ['drag_live_v2.py', 'cause_interactive_v2.py', 'cause_session_v1.py',
                 'cause_socket_entry_v2.py', 'input_owner_v10.py', 'executor_v5.py',
                 'lease_cause_v1.py', 'lease_cause_v2.py', 'pointer_exchange_v1.py',
                 'decision_receipt_v1.py', 'decision_receipt_v2.py', 'decision_receipt_v3.py', 'score_drag_v1.py']
        save('plan', {'sources': {n: digest((HERE / n).read_bytes()) for n in names},
                     'allocation': 'one fresh Inkscape seed 214; selected rectangle then 20 screen-pixel horizontal drag; duplicate endpoint adds 200ms dwell within same 600ms total',
                     'expected': 'at 118% zoom, approximately 16.95 document units right; x=66.95 +/-1, y=50 +/-0.1, width=40 and height=30 +/-0.1',
                     'scope': 'self-use feasibility with independent saved-SVG score, no speed comparison',
                     'verified_model_id': None, 'model_tokens': None})
        batch = query({'after': 0, 'events': ['observation'], 'timeout': 5})
        save('batch', batch)
        result = {'batch': batch, 'image': select_image(batch, runtime)}
    elif stage in ('select', 'drag'):
        batch = read('initial/batch.json') if stage == 'select' else read('select/report.json')['last_reply']
        steps = ([{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 80},
                  {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}]
                 if stage == 'select' else
                 [{'op': 'pointer_drag', 'points': [{'x': 618, 'y': 391}, {'x': 628, 'y': 391}, {'x': 638, 'y': 391}, {'x': 638, 'y': 391}], 'duration_ms': 600},
                  {'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                  {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}])
        save('steps', steps)
        report = run(query, batch, runtime, stage, steps, 30000, save)
        save('report', report)
        receipt = build((out / 'report.json').read_bytes())
        save('receipt', receipt)
        result = {'receipt': receipt, 'image': report.get('image')}
    else:
        batch = read('drag/report.json')['last_reply']
        result = query({'after': batch['cursor'], 'events': ['independent_evaluation'], 'timeout': 5,
                        'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
    save('result', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
