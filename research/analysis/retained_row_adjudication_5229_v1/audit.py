"""Independent source-AST and raw-row audit. Never import candidate/old study."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())


def source_facts(source):
    functions = {f.name:f for f in ast.parse(source).body if isinstance(f, ast.FunctionDef)}
    def call_in(function, name):
        calls = [c for c in ast.walk(functions[function]) if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Name) and c.func.id == name]
        if len(calls) != 1: raise ValueError('source shape:' + name)
        return calls[0]
    receipt = call_in('try_execution', 'ExecutionReceipt')
    effect = call_in('try_effect', 'ExecutionReceipt')
    lease = call_in('fixture', 'AuthorityLease')
    start, normal_end = ast.literal_eval(receipt.args[6]), ast.literal_eval(effect.args[7])
    release = ast.literal_eval(receipt.args[10].args[0])
    deadline = ast.literal_eval(lease.args[3])
    assert ast.literal_eval(effect.args[6]) == start
    assert ast.literal_eval(effect.args[10].args[0]) == release
    dictionaries = [d for d in ast.walk(functions['main']) if isinstance(d, ast.Dict)]
    assert len(dictionaries) == 1
    cases = {}
    for key, call in zip(dictionaries[0].keys, dictionaries[0].values):
        name = ast.literal_eval(key)
        if call.func.id == 'try_execution':
            cases[name] = ('execution', ast.literal_eval(call.args[0]),
                           len(call.args) == 1 or ast.literal_eval(call.args[1]) == 'command')
        elif call.func.id == 'try_effect':
            cases[name] = ('effect', ast.literal_eval(call.args[0]), True)
        else:
            raise ValueError('unknown source case')
    return start, normal_end, release, deadline, cases


def validate(report, raw, facts, freeze):
    if type(report) is not dict: return ['report_type']
    start, normal_end, release, deadline, cases = facts
    errors = []
    variants = report.get('variants')
    roles = ('snapshot_only', 'post_execution', 'terminal_includes_release')
    modes = ('inclusive', 'exclusive')
    if type(variants) is not list or len(variants) != 6:
        return ['variant_inventory']
    if {(v.get('release_role'),v.get('effect_equality')) for v in variants} != {(r,m) for r in roles for m in modes}:
        return ['variant_identity']
    for variant in variants:
        role, mode = variant['release_role'], variant['effect_equality']
        release_predicate = {
            'snapshot_only': lambda end: True,
            'post_execution': lambda end: not release < end,
            'terminal_includes_release': lambda end: not (release < start or end < release),
        }[role]
        expected_rows = []
        for key in sorted(cases):
            kind, time, same_command = cases[key]
            if not same_command:
                expected = False
            elif kind == 'execution':
                expected = not (time < start or deadline <= time) and release_predicate(time)
            elif not release_predicate(normal_end):
                expected = None
            else:
                expected = not time < normal_end if mode == 'inclusive' else normal_end < time
            expected_rows.append({'key':key,'observed':raw[key], 'conditional_expected':expected,
                                  'status':'UNKNOWN_CONTEXT' if expected is None else
                                  'AGREES' if raw[key] == expected else 'DISAGREES'})
        # Serialized equality preserves bool/null types; Python scalar equality does not.
        if json.dumps(variant.get('rows'),sort_keys=True) != json.dumps(expected_rows,sort_keys=True):
            errors.append('row_arithmetic:' + role + ':' + mode)
        for status, field in [('DISAGREES','disagreements'), ('UNKNOWN_CONTEXT','unknown')]:
            if variant.get(field) != [r['key'] for r in expected_rows if r['status'] == status]:
                errors.append('row_denominator:' + field)
        if (variant.get('original_gate') != 'HOLD_UNEVALUABLE'
                or variant.get('gate_reasons') != ['missing_effect_at_900','original_effect_at_700_contract_conflict']):
            errors.append('gate_promotion')
    if (report.get('source_commit') != freeze['source_commit'] or report.get('observed_count') != 9
            or report.get('scientific_status') != 'HOLD_UNEVALUABLE'
            or report.get('raw_record_status') != 'COMPLETE_NINE_OBSERVED_BOOLEANS'
            or report.get('planned_record_status') != 'INCOMPLETE_EFFECT_AT_900'
            or report.get('raw_git_blob') != freeze['sources'][freeze['raw_path']]['git_blob']
            or report.get('raw_sha256') != freeze['sources'][freeze['raw_path']]['sha256']):
        errors.append('scope_or_identity')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git', default='git')
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    originals = {}
    for path, pin in freeze['sources'].items():
        data = subprocess.check_output([args.git, 'show', freeze['source_commit'] + ':' + path], cwd=ROOT)
        actual_blob = subprocess.check_output([args.git,'hash-object','--stdin'],input=data,cwd=ROOT).decode().strip()
        if hashlib.sha256(data).hexdigest()!=pin['sha256'] or actual_blob!=pin['git_blob']:
            raise ValueError('source identity: ' + path)
        originals[path]=data
    facts = source_facts(originals[freeze['probe_path']])
    raw = json.loads(originals[freeze['raw_path']])
    assert type(raw) is dict and set(raw)==set(facts[-1]) and all(type(v) is bool for v in raw.values())
    plan = originals[freeze['plan_path']].decode()
    assert 'effect time 900' in plan and 'effect_at_900' not in raw
    assert 'reject at execution end (causally eligible)' in plan
    report = json.loads(args.result.read_bytes())
    errors = validate(report, raw, facts, freeze)
    controls = {}
    for label in ('drop_variant','flip_observed','integer_for_bool','invent_unknown','promote_gate','omit_gate_reason'):
        changed = copy.deepcopy(report)
        if label=='drop_variant': changed['variants'].pop()
        if label=='flip_observed': changed['variants'][0]['rows'][0]['observed']=False
        if label=='integer_for_bool': changed['variants'][0]['rows'][0]['observed']=1
        if label=='invent_unknown': changed['variants'][0]['rows'][0]['conditional_expected']=None
        if label=='promote_gate': changed['variants'][0]['original_gate']='PASS'
        if label=='omit_gate_reason': changed['variants'][0]['gate_reasons'].pop()
        controls[label]=bool(validate(changed,raw,facts,freeze))
    passed=not errors and all(controls.values())
    print(json.dumps({'passed':passed,'errors':errors,'corruption_controls':controls,
                      'facts_from_frozen_AST':{'start_ns':facts[0],'normal_end_ns':facts[1],
                                              'release_ns':facts[2],'lease_end_ns':facts[3], 'cases':len(facts[4])},
                      'disposition':'PASS_ADJUDICATION_SCOPED' if passed else 'HOLD_AUDIT',
                      'scientific_status':'HOLD_UNEVALUABLE','imports_historical_code':False},indent=2,sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
