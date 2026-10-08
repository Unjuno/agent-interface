"""Versioned raw-only identity gate; no runtime, runner or candidate import."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('retained_v1_oracle', ROOT / 'auditor.py')
V1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V1)
ROW_KEYS = {'arm', 'case', 'input_before', 'input_after', 'input_before_sha256',
    'input_after_sha256', 'core_admission', 'trace', 'journal', 'terminal', 'exception'}

def same_json(actual, expected):
    """JSON identity includes scalar types, keys, list order and values."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return actual.keys() == expected.keys() and all(same_json(actual[k], v) for k, v in expected.items())
    if type(expected) is list:
        return len(actual) == len(expected) and all(same_json(a, b) for a, b in zip(actual, expected))
    return actual == expected

def terminal(success):
    return {'outcome': 'TASK_SUCCEEDED' if success else 'SAFE_YIELD',
        'reason': 'method_complete' if success else 'authority_unavailable',
        'completed_transitions': 1 if success else 0,
        'pending_effect': None, 'frontier_model_resumptions': 0}

def identity_errors(row):
    errors = []
    if type(row) is not dict or row.keys() != ROW_KEYS:
        return ['row schema']
    try:
        reference = V1.expected_input(row['case'])
    except (KeyError, TypeError):
        return ['case schema']
    if not same_json(row['input_before'], reference) or not same_json(row['input_after'], reference):
        errors.append('typed frozen input')
    core, trace, journal, exception = (row[k] for k in ('core_admission', 'trace', 'journal', 'exception'))
    if type(trace) is not list or any(type(e) is not dict for e in trace):
        return errors + ['trace schema']
    if type(journal) is not list:
        return errors + ['journal schema']
    initial_journal = [
        {'event': 'observation_recorded', 'evidence_ref': 'e1', 'sequence': 1, 'state': 'ready'},
        {'action': 'once', 'event': 'branch_selected', 'evidence_ref': 'e1',
            'matched_conditions': {'phase': 0}, 'outcome': 'action', 'state': 'ready'}]
    expected_trace = [{'call': 'observe', 'sequence': 1}, {'call': 'admit'}]
    expected_journal = list(initial_journal)
    expected_terminal = None
    expected_exception_type = None
    if core is None:
        expected_exception_type = 'TypeError'
        expected_trace.append({'call': 'core_exception', 'type': expected_exception_type})
    else:
        if type(core) is not dict or core.keys() != {'accepted', 'error', 'required_capabilities'} \
                or type(core['accepted']) is not bool or not (core['error'] is None or type(core['error']) is str) \
                or type(core['required_capabilities']) is not list \
                or any(type(cap) is not str for cap in core['required_capabilities']):
            return errors + ['core schema/types']
        expected_trace.append({'call': 'core_result', **core})
        executions = sum(e.get('call') == 'execute' for e in trace)
        if not core['accepted']:
            expected_terminal = terminal(False)
            expected_journal.append({'action': 'once', 'event': 'admission_refused',
                'reason': 'authority_unavailable', 'status': core['error']})
        elif executions == 1:
            expected_terminal = terminal(True)
            expected_trace.extend([
                {'call': 'execute', 'expected_sequence': reference['compiled_sequence']},
                {'call': 'observe', 'sequence': 2}, {'call': 'verify_effect', 'sequence': 2}])
            expected_journal.extend([
                {'action': 'once', 'action_id': 'inert-action', 'event': 'action_terminal',
                    'release_verified': True, 'status': 'completed'},
                {'event': 'observation_recorded', 'evidence_ref': 'e2', 'sequence': 2, 'state': 'done'},
                {'action': 'once', 'event': 'effect_checked', 'evidence_ref': 'e2', 'status': 'succeeded'},
                {'action': None, 'event': 'branch_selected', 'evidence_ref': 'e2',
                    'matched_conditions': {'phase': 1}, 'outcome': 'complete', 'state': 'done'}])
        else:
            expected_exception_type = 'ValueError'
    if expected_terminal is not None:
        expected_journal.append({'event': 'runtime_finished',
            **{key: expected_terminal[key] for key in ('completed_transitions', 'outcome', 'reason')}})
    if not same_json(trace, expected_trace):
        errors.append('typed ordered trace / actual execute sequence / core-observation linkage')
    if not same_json(journal, expected_journal):
        errors.append('typed ordered journal / effect-observation linkage')
    if not same_json(row['terminal'], expected_terminal):
        errors.append('typed terminal')
    if expected_exception_type is None:
        if exception is not None:
            errors.append('unexpected exception')
    elif type(exception) is not dict or exception.keys() != {'type', 'message'} \
            or not same_json(exception.get('type'), expected_exception_type) \
            or type(exception.get('message')) is not str or not exception['message']:
        errors.append('exception schema/type')
    return errors

def check(rows, arm):
    identities = []
    if type(rows) is not list:
        return {'arm': arm, 'rows': 0, 'errors': ['rows schema'], 'identity_error_count': 1,
            'mismatch_count': 0}
    for ordinal, row in enumerate(rows):
        issues = identity_errors(row)
        if issues:
            identities.append({'ordinal': ordinal, 'case_id': row.get('case', {}).get('case_id')
                if type(row) is dict and type(row.get('case')) is dict else None, 'violations': issues})
    try:
        result = V1.check(rows, arm)
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as error:
        result = {'arm': arm, 'rows': len(rows), 'errors': ['v1 input/schema refusal: ' + type(error).__name__],
            'mismatch_count': 0}
    result['identity_errors'] = identities
    result['identity_error_count'] = len(identities)
    result['errors'] += [f"identity row {r['ordinal']}: {', '.join(r['violations'])}" for r in identities]
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--arm', choices=('baseline', 'combined'), required=True)
    args = parser.parse_args()
    data = args.raw.read_bytes()
    rows = [json.loads(line) for line in data.decode('utf-8').splitlines()]
    result = check(rows, args.arm)
    result.update(raw_sha256=hashlib.sha256(data).hexdigest(),
        disposition='FAIL_SCOPED' if result['errors'] or (args.arm == 'combined' and result['mismatch_count'])
        else 'PASS_SCOPED' if args.arm == 'combined' else 'RETAINED_BASELINE_GAPS')
    print(json.dumps(result, sort_keys=True, indent=2))
    return int(result['disposition'] == 'FAIL_SCOPED')

if __name__ == '__main__':
    raise SystemExit(main())
