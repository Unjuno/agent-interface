"""Conditional arithmetic adjudication of immutable observations, not kernel replay."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())
OBSERVED_KEYS = frozenset(('execution_end_700', 'execution_end_999', 'execution_end_1000',
                         'execution_end_1001', 'execution_wrong_command', 'effect_at_499',
                         'effect_at_699', 'effect_at_700', 'effect_at_701'))


def strict_record(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    record = json.loads(raw, object_pairs_hook=pairs)
    if type(record) is not dict or set(record) != OBSERVED_KEYS:
        raise ValueError('observed-key inventory')
    if any(type(v) is not bool for v in record.values()):
        raise ValueError('observations must be exact booleans')
    return record


def analyze(record):
    variants = []
    for release_role, equality in itertools.product(
            ('snapshot_only', 'post_execution', 'terminal_includes_release'), ('inclusive', 'exclusive')):
        def release_ok(end):
            if release_role == 'snapshot_only': return True
            if release_role == 'post_execution': return 800 >= end
            return 500 <= 800 <= end
        rows = []
        for key in sorted(record):
            if key == 'execution_wrong_command':
                expected = False
            elif key.startswith('execution_end_'):
                end = int(key.rsplit('_', 1)[-1])
                expected = 500 <= end < 1000 and release_ok(end)
            elif not release_ok(700):
                expected = None
            else:
                time = int(key.rsplit('_', 1)[-1])
                expected = time >= 700 if equality == 'inclusive' else time > 700
            rows.append({'key': key, 'observed': record[key], 'conditional_expected': expected,
                         'status': 'UNKNOWN_CONTEXT' if expected is None else
                         'AGREES' if record[key] is expected else 'DISAGREES'})
        variants.append({'release_role': release_role, 'effect_equality': equality, 'rows': rows,
                         'disagreements': [r['key'] for r in rows if r['status'] == 'DISAGREES'],
                         'unknown': [r['key'] for r in rows if r['status'] == 'UNKNOWN_CONTEXT'],
                         'original_gate': 'HOLD_UNEVALUABLE',
                         'gate_reasons': ['missing_effect_at_900', 'original_effect_at_700_contract_conflict']})
    return {'observed_count': len(record), 'variants': variants,
            'raw_record_status': 'COMPLETE_NINE_OBSERVED_BOOLEANS',
            'planned_record_status': 'INCOMPLETE_EFFECT_AT_900',
            'scientific_status': 'HOLD_UNEVALUABLE',
            'scope': 'conditional arithmetic labels only; original dispositions and observed values unchanged'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git', default='git')
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    blobs = {}
    for path, pin in freeze['sources'].items():
        blob = subprocess.check_output([args.git, 'rev-parse', freeze['source_commit'] + ':' + path], cwd=ROOT).decode().strip()
        data = subprocess.check_output([args.git, 'cat-file', 'blob', blob], cwd=ROOT)
        if blob != pin['git_blob'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('source identity: ' + path)
        blobs[path] = data
    record = strict_record(blobs[freeze['raw_path']])
    output = analyze(record)
    output.update(source_commit=freeze['source_commit'], raw_git_blob=freeze['sources'][freeze['raw_path']]['git_blob'],
                  raw_sha256=hashlib.sha256(blobs[freeze['raw_path']]).hexdigest())
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
