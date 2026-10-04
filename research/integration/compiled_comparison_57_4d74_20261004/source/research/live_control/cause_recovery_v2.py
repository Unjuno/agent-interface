"""Explicit observation after image-less interruption, then reviewed recovery."""
import json
import sys
import uuid
from pathlib import Path
from pointer_exchange_v1 import run, prefix, own_command
from decision_receipt_v2 import build
from receipt_image import select_image
from report_pages_v2 import digest
from unix_json_deadline import exchange


def main():
    stage, socket, directory = sys.argv[1:]
    assert stage in ('observe', 'recover', 'finish')
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
    save('source', {'sha256': digest(Path(__file__).read_bytes()), 'scope': 'explicit recovery; no automatic retries'})
    if stage == 'observe':
        batch = read('interrupt/report.json')['last_reply']
        identifier = uuid.uuid4().hex
        clock = query({'after': batch['cursor'], 'events': ['clock'], 'timeout': 5,
                       'request_id': identifier, 'command': {'op': 'clock'}})
        records = prefix(clock, batch['cursor'])
        assert own_command(records, identifier, 'clock') == len(records) - 2
        now = records[-1]
        assert now['event'] == 'clock'
        batch = query({'after': clock['cursor'], 'events': ['terminal'], 'timeout': 5,
                       'request_id': uuid.uuid4().hex, 'action_id': 'review-observation',
                       'command': {'op': 'submit', 'id': 'review-observation', 'steps': [{'op': 'observe'}],
                                   'expected_sequence': now['sequence'], 'valid_until_ns': now['runtime_ns'] + 5_000_000_000}})
        save('batch', batch)
        result = {'batch': batch, 'image': select_image(batch, runtime)}
    elif stage == 'recover':
        batch = read('observe/batch.json')
        assert batch['records'][-1]['status'] == 'completed'
        steps = [{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 80},
                 {'op': 'hold', 'keys': ['Right'], 'duration_ms': 80},
                 {'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
                 {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}]
        save('steps', steps)
        report = run(query, batch, runtime, 'recover', steps, 30000, save)
        save('report', report)
        receipt = build((out / 'report.json').read_bytes())
        save('receipt', receipt)
        result = {'receipt': receipt, 'image': report.get('image')}
    else:
        batch = read('recover/report.json')['last_reply']
        result = query({'after': batch['cursor'], 'events': ['independent_evaluation'], 'timeout': 5,
                        'request_id': uuid.uuid4().hex, 'command': {'op': 'finish'}})
    save('result', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
