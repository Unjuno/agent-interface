"""Raw-only oracle. No runtime imports or candidate helper reuse."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

def expected(context):
    fields = ('now_ns', 'current_observation_seq', 'current_binding_revision')
    if any(type(context[f]) is not int or not 0 <= context[f] < 2**63 for f in fields):
        return {'accepted': False, 'error': 'INVALID_PROGRAM', 'required': []}
    error = ('LEASE_EXPIRED' if context['now_ns'] > 100 else
             'STALE_OBSERVATION' if context['current_observation_seq'] != 1 else
             'STALE_BINDING' if context['current_binding_revision'] != 1 else None)
    return {'accepted': error is None, 'error': error, 'required': ['input.release_all']}

def legacy_expected(context):
    if type(context['now_ns']) not in (int, float, bool):
        return {'exception': 'TypeError'}
    error = ('LEASE_EXPIRED' if context['now_ns'] > 100 else
             'STALE_OBSERVATION' if context['current_observation_seq'] != 1 else
             'STALE_BINDING' if context['current_binding_revision'] != 1 else None)
    return {'accepted': error is None, 'error': error, 'required': ['input.release_all']}

def verify(raw, fixtures, source_sha, stage='fixed'):
    errors = []
    if raw.get('schema') != 'admission-context-regression-v1' or raw.get('stage') != stage:
        errors.append('schema_or_stage')
    if raw.get('source_sha256') != source_sha:
        errors.append('source_identity')
    if raw.get('fixtures_sha256') != hashlib.sha256((HERE / 'fixtures.json').read_bytes()).hexdigest():
        errors.append('fixture_identity')
    if raw.get('backend_opened') is not False or raw.get('input_dispatched') is not False:
        errors.append('side_effects')
    rows = raw.get('rows')
    if type(rows) is not list or len(rows) != len(fixtures['cases']):
        return errors + ['denominator']
    for row, case in zip(rows, fixtures['cases']):
        name = case['id']
        if row.get('id') != name or canonical(row.get('context')) != canonical(case['context']):
            errors.append('case_identity:' + name)
        if row.get('unchanged') is not True:
            errors.append('input_mutation:' + name)
        wanted = expected(case['context']) if stage == 'fixed' else legacy_expected(case['context'])
        if canonical(row.get('result')) != canonical(wanted):
            errors.append('result:' + name)
    return errors

if __name__ == '__main__':
    fixtures = json.loads((HERE / 'fixtures.json').read_bytes())
    fixed = json.loads((HERE / 'fixed.json').read_bytes())
    before = json.loads((HERE / 'before.json').read_bytes())
    identity = json.loads((HERE / 'SOURCE_MANIFEST.json').read_bytes())
    source_sha = hashlib.sha256((HERE.parents[2] / 'runtime/core_v1/contract.py').read_bytes()).hexdigest()
    errors = verify(fixed, fixtures, source_sha)
    before_errors = verify(before, fixtures, identity['before_source_sha256'], stage='before')
    for stage in ('before', 'fixed'):
        if hashlib.sha256((HERE / (stage + '.json')).read_bytes()).hexdigest() != identity[stage + '_raw_sha256']:
            errors.append('raw_identity:' + stage)
    if source_sha != identity['fixed_source_sha256']:
        errors.append('fixed_source_identity')
    controls = []
    for label in ('omitted_row', 'duplicate_id', 'context_int_to_bool', 'result_bool_to_int',
                  'invalid_accepted', 'source_identity', 'fixture_identity', 'input_mutated', 'input_dispatched'):
        mutant = copy.deepcopy(fixed)
        if label == 'omitted_row':
            mutant['rows'].pop()
        elif label == 'duplicate_id':
            mutant['rows'][1]['id'] = mutant['rows'][0]['id']
        elif label == 'context_int_to_bool':
            mutant['rows'][11]['context']['now_ns'] = True
        elif label == 'result_bool_to_int':
            mutant['rows'][0]['result']['accepted'] = 0
        elif label == 'invalid_accepted':
            mutant['rows'][0]['result'] = {'accepted': True, 'error': None, 'required': []}
        elif label == 'source_identity':
            mutant['source_sha256'] = '0' * 64
        elif label == 'fixture_identity':
            mutant['fixtures_sha256'] = '0' * 64
        elif label == 'input_mutated':
            mutant['rows'][0]['unchanged'] = False
        else:
            mutant['input_dispatched'] = True
        failures = verify(mutant, fixtures, source_sha)
        controls.append({'control': label, 'rejected': bool(failures), 'errors': failures})
    before_rows = before['rows']
    baseline_gaps = sum(canonical(row['result']) != canonical(expected(case['context']))
                        for row, case in zip(before_rows, fixtures['cases']))
    result = {'status': 'PASS_CONTEXT_REFUSAL_SCOPED' if not errors and not before_errors and all(c['rejected'] for c in controls) else 'FAIL_AUDIT',
              'rows': len(fixed['rows']), 'fixed_errors': errors, 'baseline_decision_gaps': baseline_gaps,
              'before_errors': before_errors,
              'baseline_unexpected_exceptions': sum('exception' in row['result'] for row in before_rows),
              'corruption_controls': controls, 'same_author_independent_implementation': True,
              'external_non_author_review': False}
    with Path(sys.argv[1]).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
