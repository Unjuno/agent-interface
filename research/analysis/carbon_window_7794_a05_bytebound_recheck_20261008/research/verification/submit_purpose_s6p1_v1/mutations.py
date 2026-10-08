"""Effective well-formed copied-record mutations; no source or formal DB edits."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit import audit


def controls(root):
    root = Path(root)
    base = audit(root)
    if base['errors']:
        raise ValueError('baseline must pass before every control family')
    c = root / 'r0-01-SUBMIT_EVENT' / 'ACTOR.json'
    original = json.loads(c.read_text())
    outputs = []
    def trial(name, change):
        altered = copy.deepcopy(original); change(altered)
        altered['stdout_sha256'] = hashlib.sha256(altered['stdout'].encode()).hexdigest()
        raw = (json.dumps(altered, sort_keys=True, indent=2) + '\n').encode()
        if raw == c.read_bytes():
            raise ValueError('ineffective mutation: ' + name)
        res = audit(root, {str(c.relative_to(root)): raw})
        if not res['errors'] or any(e.startswith('AUDIT_EXCEPTION:') for e in res['errors']):
            raise ValueError('accepted or crashed control: ' + name)
        outputs.append({'name': name, 'changed': True, 'rejected': True, 'errors': res['errors'],
                        'mutated_sha256': hashlib.sha256(raw).hexdigest()})
    def inner(fn):
        def apply(record):
            obj = json.loads(record['stdout']); fn(obj); record['stdout'] = json.dumps(obj, sort_keys=True) + '\n'
        return apply
    trial('false_terminal_exit', lambda r: r.__setitem__('exit', 23))
    trial('missing_step', inner(lambda r: r['steps'].pop()))
    trial('wrong_disposition', inner(lambda r: r['steps'][1]['result'].__setitem__('status', 'DUPLICATE_REVISION')))
    trial('authority_promotion', inner(lambda r: r['steps'][1]['result'].__setitem__('authority', True)))
    trial('missing_submission', inner(lambda r: r['final'].__setitem__('submissions', [])))
    trial('extra_submission', inner(lambda r: r['final']['submissions'].append(['extra', 2, 'ab'])))
    trial('wrong_value', inner(lambda r: r['final']['document'][0].__setitem__(2, 'wrong')))
    trial('boolean_revision', inner(lambda r: r['steps'][1]['request'].__setitem__('revision', True)))
    trial('wrong_process_identity', inner(lambda r: r.__setitem__('pid', r['pid'] + 100000)))
    trial('wrong_input_identity', lambda r: r.__setitem__('stdin', r['stdin'].replace('epoch-1', 'epoch-2')))
    trial('clock_order', inner(lambda r: r.__setitem__('ended_ns', r['started_ns'] - 1)))
    trial('false_document_rewrite', inner(lambda r: r['final']['commits'].append([2, 'submit-2', 2, 'ab', 'SUBMIT'])))
    return {'baseline_passed': True, 'controls': len(outputs), 'rejected': len(outputs), 'rows': outputs}


if __name__ == '__main__':
    print(json.dumps(controls(Path(sys.argv[1])), sort_keys=True, indent=2))
