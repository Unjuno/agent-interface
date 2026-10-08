"""Raw-only independent checker; never imports session or core runtime code."""
from copy import deepcopy
import json
import sys
from pathlib import Path

ROUTES = ('win32_v1', 'x11_v1', 'quartz_v1')
EXPECTED = {
    'valid': ('completed', None, ['clock', 'preflight', 'execute'], 1),
    'expired': ('refused', 'LEASE_EXPIRED', ['clock'], 0),
    'nan_clock': ('refused', 'INVALID_PROGRAM', ['clock'], 0),
    'negative_clock': ('refused', 'INVALID_PROGRAM', ['clock'], 0),
    'bool_clock': ('refused', 'INVALID_PROGRAM', ['clock'], 0),
    'bool_sequence': ('refused', 'INVALID_PROGRAM', ['clock'], 0),
    'float_revision': ('refused', 'INVALID_PROGRAM', ['clock'], 0),
}


def audit(raw):
    errors, seen = [], set()
    rows = raw.get('rows', [])
    if len(rows) != 21:
        errors.append('row_count')
    for row in rows:
        key = row['route'], row['case']
        if key in seen:
            errors.append('duplicate')
        seen.add(key)
        if type(row.get('spy_execution_count')) is not int:
            errors.append('counter_type:' + '/'.join(key))
        want = EXPECTED.get(row['case'])
        if row['route'] not in ROUTES or want is None:
            errors.append('unexpected_case')
            continue
        got = row['status'], row['error'], row['calls'], row['spy_execution_count']
        if got != want:
            errors.append('verdict_or_execution:' + '/'.join(key))
    if seen != {(route, case) for route in ROUTES for case in EXPECTED}:
        errors.append('coverage')
    return errors


def main(path):
    raw = json.loads(Path(path).read_bytes())
    errors = audit(raw)
    mutations = {}
    for name in ('omission', 'duplicate', 'fabricated_nan_admission', 'hidden_execute', 'boolean_counter'):
        changed = deepcopy(raw)
        if name == 'omission':
            changed['rows'].pop()
        elif name == 'duplicate':
            changed['rows'][-1] = deepcopy(changed['rows'][0])
        elif name == 'fabricated_nan_admission':
            changed['rows'][2]['status'] = 'completed'
            changed['rows'][2]['error'] = None
        elif name == 'hidden_execute':
            changed['rows'][2]['calls'].append('execute')
        elif name == 'boolean_counter':
            changed['rows'][2]['spy_execution_count'] = False
        rejected = audit(changed)
        mutations[name] = rejected
        if not rejected:
            errors.append('mutation_not_rejected:' + name)
    result = {'scope': 'raw-only engineering check, no physical backend evidence',
              'rows': len(raw['rows']), 'errors': errors, 'mutation_rejections': mutations,
              'status': 'PASS_SESSION_ADMISSION_CHECK' if not errors else 'FAIL_SESSION_ADMISSION_CHECK'}
    print(json.dumps(result, indent=2, allow_nan=False))
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
