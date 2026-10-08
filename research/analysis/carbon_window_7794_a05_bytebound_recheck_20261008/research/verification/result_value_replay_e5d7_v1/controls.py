"""Effective, well-formed copied-evidence mutation tests. No receiver processes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import audit


def main(root):
    rows = []
    paths = ('formal-00/STABLE-CURRENT_PROJECTION-0', 'formal-02/ABA-CURRENT_PROJECTION-0')
    mutations = ('result_value', 'result_version', 'authority', 'task_success', 'new_effect',
                 'boolean_delta', 'wrong_exit', 'missing_pid', 'drop_call', 'database_value',
                 'aba_version_laundering', 'source_drift')
    for name in mutations:
        with tempfile.TemporaryDirectory(prefix='e5d7-control-') as tmp:
            d = Path(tmp) / 'study'
            shutil.copytree(root, d, ignore=shutil.ignore_patterns('__pycache__', 'CONTROLS.json'))
            p = d / paths[0] / '01.stdout'
            if name == 'result_value':
                mutate = lambda x: x['result'].__setitem__('counter_after', 91)
            elif name == 'result_version':
                mutate = lambda x: x['result'].__setitem__('commit_version', 91)
            elif name == 'authority':
                mutate = lambda x: x.__setitem__('authority', True)
            elif name == 'task_success':
                mutate = lambda x: x.__setitem__('task_success', True)
            elif name == 'new_effect':
                mutate = lambda x: x.__setitem__('new_effect', True)
            elif name == 'boolean_delta':
                p = d / paths[0] / '01.request.json'
                mutate = lambda x: x.__setitem__('delta', True)
            elif name == 'wrong_exit':
                p = d / paths[0] / '01.process.json'
                mutate = lambda x: x.__setitem__('returncode', 1)
            elif name == 'missing_pid':
                p = d / paths[0] / '01.process.json'
                mutate = lambda x: x.__setitem__('pid', None)
            elif name == 'drop_call':
                p = d / paths[0] / 'case.json'
                mutate = lambda x: x['calls'].pop()
            elif name == 'aba_version_laundering':
                p = d / paths[1] / '03.stdout'
                mutate = lambda x: x['result'].__setitem__('commit_version', 1)
            elif name == 'database_value':
                p = d / paths[0] / '01.sqlite'
            else:
                p = d / 'receiver.py'
            before = hashlib.sha256(p.read_bytes()).hexdigest()
            if name == 'database_value':
                db = sqlite3.connect(p)
                db.execute('UPDATE state SET counter=91')
                db.commit()
                db.close()
                # Rehash the altered copy: semantic reconstruction must still reject.
                q = p.with_suffix('.process.json')
                obj = json.loads(q.read_text())
                obj['snapshot_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
                q.write_text(json.dumps(obj))
            elif name == 'source_drift':
                p.write_text(p.read_text() + '\n# copied source mutation\n')
            else:
                obj = json.loads(p.read_text())
                mutate(obj)
                p.write_text(json.dumps(obj, sort_keys=True) + '\n')
            after = hashlib.sha256(p.read_bytes()).hexdigest()
            result = audit.inspect(d)
            normal_rejection = bool(result['errors']) and not any(':unreadable:' in e or e.startswith('freeze:') for e in result['errors'])
            rows.append({'name': name, 'effective': before != after, 'before_sha256': before,
                         'after_sha256': after, 'rejected_normally': normal_rejection, 'errors': result['errors']})
    return {'passed': all(r['effective'] and r['rejected_normally'] for r in rows), 'controls': rows}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    a = ap.parse_args()
    out = main(a.root.resolve())
    print(json.dumps(out, indent=2, sort_keys=True))
    raise SystemExit(not out['passed'])
