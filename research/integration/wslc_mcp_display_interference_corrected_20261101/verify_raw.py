"""Cross-check recorded summary against independent fixture and target files.

This does not establish independent keymap capture: keymaps are retained in
the trial's result JSON. It does not re-run a live experiment.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(value, reason):
    if not value:
        raise ValueError(reason)


for name, trial, target_key, target_path, expected in (
    ('mcp-same-key-fixed-r168', 'r168-same', 'target_result',
     'target-events.json', 2),
    ('mcp-isolated-fixed-r169', 'r169-isolated', 'second_target_result',
     'target2/target-events.json', 6),
):
    output = ROOT / name / trial / 'output'
    summary = load(output / 'result.json')
    raw_target = load(output / target_path)
    require(summary[target_key] == raw_target, name + ': target receipt mismatch')
    events = raw_target['events']
    require([(e['type'], e['key']) for e in events] ==
            [('press', 'a'), ('release', 'a')] * expected,
            name + ': unexpected target events')
    require(raw_target['value'] == 'a' * expected, name + ': target value mismatch')
    for owner in ('first', 'second'):
        log = output / owner / 'xvfb-delayed-injections.jsonl'
        entries = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines() if line]
        require(entries == summary['injections'][owner] and len(entries) == 1,
                name + ': injection receipt mismatch for ' + owner)
        require(type(entries[0]['owner_pid']) is int and entries[0]['owner_pid'] > 0,
                name + ': invalid recorded pid')
    require(summary['first_close_final']['cleanup_status'] == 'UNKNOWN' and
            summary['second_close_final']['cleanup_status'] == 'UNKNOWN',
            name + ': close status')
print('PASS: target and injection summary fields match retained separate raw files')
