"""One explicit live move with compact index/image review and optional details."""
import argparse
import json
import time
import uuid
from pathlib import Path
from pointer_exchange_v1 import run
from decision_receipt_v2 import build
from pointer_report_view_v1 import pack
from receipt_image import select_image
from report_pages_v2 import page, digest, reconstruct
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['initial', 'move', 'page', 'finish'])
    ap.add_argument('socket')
    ap.add_argument('root', type=Path)
    ap.add_argument('--after', type=int, default=0)
    args = ap.parse_args()
    root, runtime = args.root, args.root / 'runtime'
    label = 'page-' + str(args.after) if args.stage == 'page' else args.stage
    out = root / label
    out.mkdir(exist_ok=False)
    def save(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    def read(path):
        return json.loads((root / path).read_text())
    def query(q):
        index = len(list(out.glob('query-*-request.json')))
        save(f'query-{index}-request', q)
        reply = exchange(args.socket, q, timeout=16)
        save(f'query-{index}-reply', reply)
        return reply
    started = time.perf_counter_ns()
    if args.stage == 'initial':
        sources = ['compact_live_v1.py', 'decision_receipt_v1.py', 'decision_receipt_v2.py', 'report_pages_v2.py', 'pointer_exchange_v1.py', 'pointer_report_view_v1.py', 'receipt_image.py']
        save('plan', {'sources': {name: digest((HERE / name).read_bytes()) for name in sources},
                     'allocation': 'one fresh Inkscape seed 206; no clean rerun; compact index and original image review; attention requires source inspection before finish',
                     'page_wire_limit': 4096, 'verified_model_id': None, 'model_tokens': None,
                     'scope': 'integration/self-use, not paired speed study'})
        batch = query({'after': 0, 'events': ['observation'], 'timeout': 5})
        save('batch', batch)
        result = {'batch': batch, 'image': select_image(batch, runtime)}
    elif args.stage == 'move':
        steps = [{'op': 'pointer_click', 'x': 618, 'y': 391},
                 {'op': 'hold', 'keys': ['Right'], 'duration_ms': 80},
                 {'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                 {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}]
        save('steps', steps)
        report = run(query, read('initial/batch.json'), runtime, 'move-save', steps, 30000, save)
        save('original-report', report)
        save('view', pack(report))
        receipt = build((out / 'original-report.json').read_bytes())
        save('receipt', receipt)
        result = {'receipt': receipt, 'image': report.get('image')}
    elif args.stage == 'page':
        data = (root / 'move/view.json').read_bytes()
        expected = digest(data)
        result = page(data, args.after, expected, 4096)
    else:
        save('coverage', {'mode': 'compact index plus selected image; full source not claimed reviewed', 'model_receipt': 'unverified; explicit finish requested by caller'})
        report = read('move/original-report.json')
        batch = report.get('last_reply') or read('initial/batch.json')
        result = query({'after': batch['cursor'], 'events': ['independent_evaluation'], 'timeout': 5,
                        'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
    save('result', result)
    save('timing', {'started_ns': started, 'returned_ns': time.perf_counter_ns(), 'scope': 'local CLI, not model receipt'})
    print(json.dumps(result))


if __name__ == '__main__':
    main()
