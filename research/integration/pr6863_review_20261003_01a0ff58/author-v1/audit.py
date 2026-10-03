"""Independent raw-only oracle: does not import the runtime or probe."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

SEQUENCES = (0, 1, 2, 7, 2**63 - 1)
LABELS = ('equal_int', 'wrong_int', 'false', 'true', 'equal_float', 'string',
          'null', 'int_subclass', 'nan', 'infinity')
PROFILES = ('valid', 'ineligible', 'expired')


def audit(raw):
    errors = []
    expected_ids = {f'{s}:{v}:{p}' for s, v, p in itertools.product(SEQUENCES, LABELS, PROFILES)}
    rows = raw.get('rows', [])
    ids = [row.get('case_id') for row in rows]
    if len(ids) != 150 or len(set(ids)) != 150 or set(ids) != expected_ids:
        errors.append('coverage')
    for row in rows:
        case = row['case_id']
        sequence, label, profile = case.split(':')
        if (row['observation_sequence'], row['admission_label'], row['profile']) != (int(sequence), label, profile):
            errors.append(f'{case}:identity')
        calls, result, exception = row['calls'], row['result'], row['exception']
        if profile == 'ineligible':
            valid = (result == dict(outcome='SAFE_YIELD', reason='stale_symbol', completed_transitions=0)
                     and exception is None and calls == dict(observe=1, execute=0, verify_effect=0))
        elif profile == 'valid' and label == 'equal_int':
            valid = (result == dict(outcome='TASK_SUCCEEDED', reason='method_complete', completed_transitions=1)
                     and exception is None and calls == dict(observe=2, execute=1, verify_effect=1)
                     and row['dispatched'] == [dict(type='int', repr=sequence)])
        else:
            valid = (result is None and isinstance(exception, dict) and exception.get('type') == 'ValueError'
                     and calls == dict(observe=1, execute=0, verify_effect=0))
        if not valid:
            errors.append(f'{case}:boundary')
        if calls['execute'] == 0 and row['dispatched']:
            errors.append(f'{case}:dispatch')
    return dict(status='PASS_FINITE_CONTRACT_SCOPED' if not errors else 'FAIL_FINITE_CONTRACT',
                rows=len(rows), errors=errors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(json.loads(args.raw.read_text(encoding='utf-8')))
    result['raw_sha256'] = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
