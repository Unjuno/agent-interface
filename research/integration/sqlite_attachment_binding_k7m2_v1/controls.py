"""Effective well-formed semantic mutations: exercise audit logic, not only hashes."""
import copy
import json
from pathlib import Path
import sys
from audit import check_case


def controls(root):
    files = sorted(root.glob('batch-*/*/CASE.json'))
    original = json.loads(files[0].read_text())
    root0 = files[0].parent
    e, _ = check_case(original, root0, files=True)
    if e:
        raise ValueError('INTACT_CONTROL_FAILED:' + repr(e))
    def response(r, tag):
        return next(x['response'] for x in r['calls'] if x['tag'] == tag)
    mutations = {
        'value': lambda r: response(r, 'prepared')['token'].__setitem__('value', 'wrong'),
        'missing_dependency': lambda r: response(r, 'prepared')['token'].__setitem__('dependencies', {}),
        'binding': lambda r: response(r, 'prepared')['token'].__setitem__('binding', 9),
        'schema': lambda r: response(r, 'initial')['B'].__setitem__('schema', 4),
        'effect': lambda r: response(r, 'final')['main'].__setitem__('effects', []),
        'exit': lambda r: r['processes']['reader'].__setitem__('returncode', None),
        'bool_repetition': lambda r: r.__setitem__('repetition', False),
        'decision': lambda r: response(r, 'decision').__setitem__('accepted', False),
    }
    outcomes = []
    for name, mutation in mutations.items():
        r = copy.deepcopy(original)
        before = json.dumps(r, sort_keys=True)
        mutation(r)
        changed = json.dumps(r, sort_keys=True) != before
        e, _ = check_case(r, root0, files=False)
        outcomes.append({'name': name, 'effective': changed, 'rejected': bool(e), 'errors': e})
    return {'controls': outcomes, 'pass': all(x['effective'] and x['rejected'] for x in outcomes)}


if __name__ == '__main__':
    result = controls(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result['pass'] else 1)
