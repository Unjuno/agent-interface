"""Version 2 raw-only oracle, independent of runtime, producer and v1 auditor."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

AFTER_SHA = 'ccaff4ce59cfbe7af76bfe80655c968eed7855acdb7514df64730790766cf7f7'
BASELINE_SHA = 'a20c7ef88ca3c103a8b2bcea4056e8e714bb4baa41474a4d4bac6c937d3110c7'
SCOPE = 'finite analytical/engineering check; no physical input, backend, model or timing measurement'
SEQUENCES = (0, 1, 2, 7, 2**63 - 1)
LABELS = ('equal_int', 'wrong_int', 'false', 'true', 'equal_float', 'string',
          'null', 'int_subclass', 'nan', 'infinity')
PROFILES = ('valid', 'ineligible', 'expired')


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def expected(sequence, label, profile):
    identity = {
        'equal_int': ('int', str(sequence)), 'wrong_int': ('int', str(sequence + 1)),
        'false': ('bool', 'False'), 'true': ('bool', 'True'),
        'equal_float': ('float', repr(float(sequence))), 'string': ('str', repr(str(sequence))),
        'null': ('NoneType', 'None'), 'int_subclass': ('IntAlias', str(sequence)),
        'nan': ('float', 'nan'), 'infinity': ('float', 'inf'),
    }
    kind, representation = identity[label]
    row = dict(case_id=f'{sequence}:{label}:{profile}', observation_sequence=sequence,
               admission_label=label, admission_type=kind, admission_repr=representation,
               profile=profile, dispatched=[], critical_events=[], result=None,
               exception={'type': 'ValueError', 'message': 'fresh revalidated admission required'},
               calls={'observe': 1, 'execute': 0, 'verify_effect': 0})
    if profile == 'ineligible':
        row['exception'] = None
        row['result'] = dict(outcome='SAFE_YIELD', reason='stale_symbol', completed_transitions=0)
        row['critical_events'] = [
            dict(action='mark', event='admission_refused', reason='stale_symbol', status='stale'),
            dict(event='runtime_finished', **row['result']),
        ]
    elif profile == 'valid' and label == 'equal_int':
        row['exception'] = None
        row['result'] = dict(outcome='TASK_SUCCEEDED', reason='method_complete', completed_transitions=1)
        row['calls'] = dict(observe=2, execute=1, verify_effect=1)
        row['dispatched'] = [dict(type='int', repr=str(sequence))]
        row['critical_events'] = [
            dict(action='mark', action_id='fixture-action', event='action_terminal',
                 release_verified=True, status='completed'),
            dict(action='mark', event='effect_checked', evidence_ref='fixture-effect', status='succeeded'),
            dict(event='runtime_finished', **row['result']),
        ]
    return row


def audit(raw, expected_source_sha256=AFTER_SHA):
    errors = []
    fields = {'format', 'module_sha256', 'python', 'platform', 'scope', 'rows'}
    if type(raw) is not dict or set(raw) != fields:
        return dict(status='FAIL_FINITE_CONTRACT_V2', rows=0, errors=['schema'])
    if (raw['format'] != 'compiled-admission-sequence-finite-v1' or raw['scope'] != SCOPE
            or type(raw['python']) is not str or not raw['python']
            or type(raw['platform']) is not str or not raw['platform']
            or raw['module_sha256'] != expected_source_sha256):
        errors.append('metadata')
    if type(raw['rows']) is not list:
        return dict(status='FAIL_FINITE_CONTRACT_V2', rows=0, errors=errors + ['rows_schema'])
    wanted = {f'{s}:{label}:{profile}': expected(s, label, profile)
              for s, label, profile in itertools.product(SEQUENCES, LABELS, PROFILES)}
    seen = set()
    for row in raw['rows']:
        if type(row) is not dict or type(row.get('case_id')) is not str:
            errors.append('row_schema')
            continue
        case = row['case_id']
        if case in seen or case not in wanted:
            errors.append('coverage')
            continue
        seen.add(case)
        if not same_json(row, wanted[case]):
            errors.append(f'{case}:boundary')
    if seen != wanted.keys() or len(raw['rows']) != len(wanted):
        errors.append('coverage')
    return dict(status='PASS_FINITE_CONTRACT_V2_SCOPED' if not errors else 'FAIL_FINITE_CONTRACT_V2',
                rows=len(raw['rows']), errors=errors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--module-sha256', choices=(AFTER_SHA, BASELINE_SHA), default=AFTER_SHA)
    args = parser.parse_args()
    result = audit(json.loads(args.raw.read_text(encoding='utf-8')), args.module_sha256)
    result['raw_sha256'] = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    result['auditor_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
