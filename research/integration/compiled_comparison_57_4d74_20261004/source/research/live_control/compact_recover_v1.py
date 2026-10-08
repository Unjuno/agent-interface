"""Explicit reviewed recovery for compact-live-01; no automatic retry loop."""
import json
import sys
from pathlib import Path
from pointer_exchange_v1 import run
from decision_receipt_v2 import build
from unix_json_deadline import exchange


def main():
    socket, root = sys.argv[1], Path(sys.argv[2])
    out = root / 'reviewed-recovery'
    out.mkdir(exist_ok=False)
    def save(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    original = json.loads((root / 'move/original-report.json').read_text())
    assert original['terminal']['status'] == 'needs_decision'
    batch = original['last_reply']
    steps = [{'op': 'pointer_click', 'x': 618, 'y': 391, 'duration_ms': 80},
             {'op': 'hold', 'keys': ['Right'], 'duration_ms': 80},
             {'op': 'chord', 'modifier': 'Control_L', 'key': 's'},
             {'op': 'settle', 'quiet_ms': 80, 'timeout_ms': 500}]
    save('source-batch', batch)
    save('steps', steps)
    report = run(lambda q: exchange(socket, q, timeout=16), batch, root / 'runtime',
                 'reviewed-recovery', steps, 30000, save)
    save('report', report)
    receipt = build((out / 'report.json').read_bytes())
    save('receipt', receipt)
    print(json.dumps({'receipt': receipt, 'image': report.get('image')}))


if __name__ == '__main__':
    main()
