"""Bounded copied-raw controls; never imports or executes the producer/runtime."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import time
import auditor

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
RAW = PACKAGE / 'evidence/combined.jsonl'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(row):
    return (json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode()

def replace(row, path, value):
    target = row
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

def main():
    started = time.monotonic()
    raw = RAW.read_bytes()
    lines = raw.splitlines(keepends=True)
    rows = [json.loads(line) for line in lines]
    controls = [
        ('reported-success-count-bool', 0, ('terminal', 'completed_transitions'), True),
        ('reported-refusal-count-bool', 4, ('terminal', 'completed_transitions'), False),
        ('reported-effect-sequence-float', 0, ('trace', 5, 'sequence'), 2.0),
        ('reported-execute-sequence-float', 0, ('trace', 3, 'expected_sequence'), {'type': 'float', 'repr': '1.0'}),
        ('model-resumptions-bool', 0, ('terminal', 'frontier_model_resumptions'), False),
        ('observation-sequence-bool', 0, ('trace', 0, 'sequence'), True),
        ('journal-observation-bool', 0, ('journal', 0, 'sequence'), True),
        ('journal-effect-observation-float', 0, ('journal', 3, 'sequence'), 2.0),
        ('effect-wrong-observation-ref', 0, ('journal', 4, 'evidence_ref'), 'e1'),
        ('core-trace-accepted-int', 0, ('trace', 2, 'accepted'), 1),
        ('core-trace-verdict-disagreement', 0, ('trace', 2, 'error'), 'STALE_OBSERVATION'),
        ('execute-wrong-sequence-int', 0, ('trace', 3, 'expected_sequence'), {'type': 'int', 'value': 2}),
        ('terminal-journal-count-bool', 0, ('journal', 6, 'completed_transitions'), True),
        ('release-journal-int', 0, ('journal', 2, 'release_verified'), 1),
        ('exception-message-bool', 1, ('exception', 'message'), True),
        ('unexpected-trace-field', 0, ('trace', 0, 'unbound_field'), 'extra'),
    ]
    results = []
    for index, (name, ordinal, path, value) in enumerate(controls):
        if time.monotonic() - started > 120:
            raise RuntimeError('bounded control time exceeded')
        changed = copy.deepcopy(rows[ordinal])
        replace(changed, path, value)
        copied = rows.copy()
        copied[ordinal] = changed
        original_v1 = auditor.V1.check(copied, 'combined') if index < 4 else None
        updated = auditor.check(copied, 'combined')
        other_rows = b''.join(lines[:ordinal] + lines[ordinal + 1:])
        changed_raw = b''.join(lines[:ordinal] + [encoded(changed)] + lines[ordinal + 1:])
        results.append({'control': name, 'ordinal': ordinal, 'path': list(path),
            'original_row': rows[ordinal], 'changed_row': changed,
            'original_row_sha256': digest(lines[ordinal]), 'changed_row_sha256': digest(encoded(changed)),
            'unchanged_other_rows_sha256': digest(other_rows), 'changed_full_copy_sha256': digest(changed_raw),
            'v1_passed': None if original_v1 is None else not original_v1['errors'] and original_v1['mismatch_count'] == 0,
            'v2_rejected': bool(updated['errors']), 'identity_error_count': updated['identity_error_count'],
            'errors': updated['errors'], 'mismatch_count': updated['mismatch_count']})
    if RAW.read_bytes() != raw or encoded(rows[0]) != lines[0]:
        raise ValueError('original raw or original parsed row mutated')
    report = {'policy': 'FINAL-v5', 'kind': 'copied-raw engineering controls, no producer/matrix replay',
        'original_raw_sha256': digest(raw), 'original_rows': len(rows),
        'controls': results, 'control_count': len(results),
        'first_four_v1_accept': all(r['v1_passed'] for r in results[:4]),
        'all_v2_reject': all(r['v2_rejected'] and r['identity_error_count'] == 1 for r in results),
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    output = ROOT / 'controls-result.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    if output.stat().st_size > 256 * 1024:
        raise ValueError('output byte bound')
    print(json.dumps({key: report[key] for key in ('original_raw_sha256', 'control_count', 'first_four_v1_accept', 'all_v2_reject')}))
    return int(not report['first_four_v1_accept'] or not report['all_v2_reject'])

if __name__ == '__main__':
    raise SystemExit(main())
