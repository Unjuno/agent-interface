"""Synthetic receipt shapes; no dispatch, image, or real task is performed."""
import copy
import json

NAMES = ('minimal', 'detail_256', 'detail_8192', 'repeat_8', 'repeat_64', 'unique_64')


def make(index):
    name = NAMES[index]
    ok = index == 0
    report = {
        'schema': 'agent-interface/runtime-dispatch-result-v1',
        'status': 'completed' if ok else 'runtime_failed',
        'result': {
            'status': 'completed' if ok else 'execution_failed',
            'recovery_required': not ok,
            'execution': {'observations': [], 'releases': [
                {'verified': True, 'keys_down': [], 'buttons_down': []}]}}}
    if not ok:
        report['result']['execution'].update(
            failed_op=2, failed_op_effect='unknown', error='synthetic_error',
            releases=[{'verified': False, 'keys_down': ['F8'], 'buttons_down': []},
                      {'verified': True, 'keys_down': [], 'buttons_down': []}])
    if index in (1, 2):
        report['detail'] = 'x' * (256 if index == 1 else 8192)
    if index >= 3:
        event = {'event': 'needs_review', 'detail': 'x' * 512,
                 'literal': {'event_ref': 0, 'values': [True, 1, False, 0],
                             'a~/b': 'literal, not a reference'}}
        count = 8 if index == 3 else 64
        if index == 5:
            report['records'] = [dict(event, ordinal=k) for k in range(count)]
            report['diagnostics'] = [dict(event, ordinal=k, extra=True) for k in range(count)]
        else:
            report['records'] = [copy.deepcopy(event)]
            report['diagnostics'] = [copy.deepcopy(event) for _ in range(count)]
    return name, json.dumps(report, sort_keys=True, separators=(',', ':'),
                            allow_nan=False).encode('utf-8')
