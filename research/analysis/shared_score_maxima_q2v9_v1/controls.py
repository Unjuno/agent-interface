"""Ten frozen effective copied-record mutations; no candidate invocation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit import audit, load


def check(data, process, corpus_hash, freeze_hash):
    base = audit(data, process, corpus_hash, freeze_hash)
    if base['errors']:
        raise ValueError('failed unchanged baseline')
    ids = {row['input']['id']: i for i, row in enumerate(data['rows'])}
    specifications = [
        ('missing_row', ['rows',len(data['rows'])-1], None),
        ('duplicate_row', ['rows',1], data['rows'][0]),
        ('omit_possible_winner', ['rows',ids['common_offset'],'output','joint'], []),
        ('include_impossible', ['rows',ids['incompatible_pairs'],'output','joint'], [0,1,2]),
        ('singleton_widened', ['rows',ids['interior_singleton'],'output','intervals',0], ['-1','1']),
        ('authority_changed', ['rows',0,'output','action_authority'], True),
        ('task_success_changed', ['rows',0,'output','task_success'], True),
        ('input_changed', ['rows',0,'input','a',0], 99),
        ('box_changed', ['rows',0,'output','box'], []),
        ('exit_changed', ['returncode'], 1),
    ]
    outcomes = []
    for name, path, replacement in specifications:
        changed, receipt = copy.deepcopy(data), copy.deepcopy(process)
        subject = receipt if name == 'exit_changed' else changed
        for key in path[:-1]:
            subject = subject[key]
        before = copy.deepcopy(subject[path[-1]])
        if name == 'missing_row':
            subject.pop(path[-1])
        else:
            subject[path[-1]] = copy.deepcopy(replacement)
        effective = before != replacement
        # Rehash changed bytes: semantic audit must work beyond file hash checks.
        wire = (json.dumps(changed, sort_keys=True, separators=(',', ':'))+'\n').encode()
        receipt['stdout_sha256'] = hashlib.sha256(wire).hexdigest()
        result = audit(changed, receipt, corpus_hash, freeze_hash)
        outcomes.append({'name': name, 'path': path, 'before': before, 'after': replacement,
                         'effective': effective, 'rejected': bool(result['errors']),
                         'errors': result['errors']})
    return {'controls': outcomes, 'passed': all(x['effective'] and x['rejected'] for x in outcomes),
            'count': len(outcomes)}


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    freeze_bytes = (root/'FREEZE.json').read_bytes()
    data, process = load(root/sys.argv[1])
    result = check(data, process, json.loads(freeze_bytes)['corpus_sha256'], hashlib.sha256(freeze_bytes).hexdigest())
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
