import argparse
import copy
import itertools
import json
from pathlib import Path

SEQUENCES = (0, 1, 2, 9007199254740992, 9223372036854775807)
KINDS = ('exact', 'wrong', 'false', 'true', 'float', 'string', 'null',
         'subclass', 'decimal', 'fraction', 'equality_object', 'list')
PROFILES = ('valid', 'expired', 'ineligible')

def audit(raw):
    errors = []
    if raw.get('schema') != 'pr6863-independent-boundary-v1' or raw.get('arm') not in ('base', 'head'):
        errors.append('schema/arm')
    identities = {f'{s}:{k}:{p}' for s, k, p in itertools.product(SEQUENCES, KINDS, PROFILES)}
    rows = raw.get('rows', [])
    ids = [r.get('case_id') for r in rows]
    if len(rows) != 180 or len(set(ids)) != 180 or set(ids) != identities:
        errors.append('coverage')
    baseline_aliases = 0
    for row in rows:
        case = row['case_id']
        s, kind, profile = case.split(':')
        sequence = int(s)
        if (type(row['sequence']) is not int or row['sequence'] != sequence
                or row['kind'] != kind or row['profile'] != profile):
            errors.append(case + ':identity')
        # Explicit finite truth independent of Python equality implementation.
        aliases = (kind in ('exact', 'subclass', 'decimal', 'fraction', 'equality_object')
                   or kind == 'false' and sequence == 0
                   or kind == 'true' and sequence == 1
                   or kind == 'float' and sequence != 9223372036854775807)
        allowed = kind == 'exact' if raw['arm'] == 'head' else aliases
        dispatch = profile == 'valid' and allowed
        equality_calls = int(raw['arm'] == 'base' and profile != 'ineligible' and kind == 'equality_object')
        expected = {'observe': 2 if dispatch else 1, 'admit': 1,
                    'execute': int(dispatch), 'verify': int(dispatch), 'equality': equality_calls}
        if (set(row['counts']) != set(expected) or
                any(type(row['counts'][k]) is not int or row['counts'][k] != v for k, v in expected.items())):
            errors.append(case + ':counts')
        if profile == 'ineligible':
            result = {'outcome': 'SAFE_YIELD', 'reason': 'stale_symbol', 'completed_transitions': 0}
        elif dispatch:
            result = {'outcome': 'TASK_SUCCEEDED', 'reason': 'method_complete', 'completed_transitions': 1}
        else:
            result = None
        if result is not None:
            actual = row['result']
            if (actual is None or set(actual) != set(result) or
                    any(type(actual[k]) is not type(v) or actual[k] != v for k, v in result.items()) or
                    row['exception'] is not None):
                errors.append(case + ':result')
        elif (row['result'] is not None or not isinstance(row['exception'], dict)
              or row['exception'].get('type') != 'ValueError'):
            errors.append(case + ':exception')
        if len(row['dispatched']) != int(dispatch):
            errors.append(case + ':dispatch')
        if raw['arm'] == 'head' and dispatch and row['dispatched'] != [{'type': 'int', 'repr': s}]:
            errors.append(case + ':dispatch_type')
        if dispatch and kind != 'exact':
            baseline_aliases += 1
    return {'status': 'PASS_FINITE_REVIEW' if not errors else 'FAIL_FINITE_REVIEW',
            'rows': len(rows), 'malformed_execute_entries': baseline_aliases, 'errors': errors}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text())
    result = audit(raw)
    controls = {}
    for name in ('missing_row', 'duplicate_row', 'boolean_count', 'float_identity', 'wrong_dispatch_type'):
        changed = copy.deepcopy(raw)
        if name == 'missing_row': changed['rows'].pop()
        elif name == 'duplicate_row': changed['rows'][-1] = changed['rows'][0]
        elif name == 'boolean_count': changed['rows'][0]['counts']['execute'] = True
        elif name == 'float_identity': changed['rows'][0]['sequence'] = 0.0
        else:
            target = next(row for row in changed['rows'] if row['kind'] == 'exact' and row['profile'] == 'valid')
            target['dispatched'][0]['type'] = 'bool'
        controls[name] = bool(audit(changed)['errors'])
    result['corruption_controls_rejected'] = controls
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(bool(result['errors']) or not all(controls.values()))

if __name__ == '__main__':
    main()
