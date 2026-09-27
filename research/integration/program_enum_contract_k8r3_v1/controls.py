"""Eight effective mutations of copied evidence, never of original records."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from audit import check, load


def run(path):
    cases, arms, execution = load(path)
    baseline = check(cases, arms, execution)
    if baseline['errors']:
        raise ValueError('controls require an interpretable baseline audit')
    result = []
    for name in ('missing_row', 'duplicate_row', 'boolean_location', 'authority',
                 'admitted_invalid', 'input_digest', 'missing_worker', 'cli_exit'):
        a, e = deepcopy(arms), deepcopy(execution)
        if name == 'missing_row': a['candidate'].pop()
        elif name == 'duplicate_row': a['candidate'][1] = deepcopy(a['candidate'][0])
        elif name == 'boolean_location': a['candidate'][0]['static']['source_operation_index'] = False
        elif name == 'authority': a['candidate'][0]['static']['side_effect_authority'] = True
        elif name == 'admitted_invalid': a['candidate'][0]['admission']['accepted'] = True
        elif name == 'input_digest': a['candidate'][0]['input_sha256'] = '0'*64
        elif name == 'missing_worker': e.pop()
        elif name == 'cli_exit': a['candidate'][0]['cli']['exit'] = False
        changed = json.dumps([a, e], sort_keys=True) != json.dumps([arms, execution], sort_keys=True)
        verdict = check(cases, a, e)
        result.append({'name':name, 'changed':changed, 'rejected':bool(verdict['errors']),
                       'errors':verdict['errors']})
    ok = all(r['changed'] and r['rejected'] for r in result)
    return {'status':'PASS' if ok else 'FAIL', 'controls':result}


if __name__ == '__main__':
    r = run(Path(sys.argv[1]))
    print(json.dumps(r, indent=2, sort_keys=True))
    sys.exit(r['status'] != 'PASS')
