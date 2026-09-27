"""Ten rehashed evidence controls; never executes a producer or the candidate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from audit import audit


def write(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2)+'\n')


def read(path):
    return json.loads(path.read_bytes())


def controls(source, mode):
    baseline = audit(source, mode)
    if baseline['errors']:
        raise ValueError('INVALID_CONTROL_BASELINE')
    names = ['missing_case', 'wrong_payload', 'cursor_boolean', 'writer_exit_missing',
             'authority_invented', 'advanced_regression', 'reset_omission',
             'changed_prefix_success', 'wrong_byte_total', 'cli_exit_boolean']
    results = []
    for name in names:
        with tempfile.TemporaryDirectory(prefix='budget-audit-') as tmp:
            root = Path(tmp)/'data'
            shutil.copytree(source, root)
            case = root/'case-00'
            if name == 'missing_case':
                write(root/'ROWS.json', read(root/'ROWS.json')[:-1])
            elif name == 'cursor_boolean':
                obj = read(case/'cursor.json'); obj['offset'] = True
                write(case/'cursor.json', obj)
            elif name == 'advanced_regression':
                write(case/'advanced.json', read(case/'cursor.json'))
            elif name in ('writer_exit_missing', 'wrong_byte_total', 'cli_exit_boolean'):
                rows = read(root/'ROWS.json'); row = rows[0]
                if name == 'writer_exit_missing':
                    row['writer_exit'] = None
                elif name == 'wrong_byte_total':
                    row['total'] += 1
                else:
                    row['calls'][0]['exit'] = False
                    write(case/'prefix.exit.json', row['calls'][0])
                write(case/'ROW.json', row); write(root/'ROWS.json', rows)
            else:
                stem = {'wrong_payload':'expanded', 'authority_invented':'expanded',
                        'reset_omission':'reset', 'changed_prefix_success':'changed'}[name]
                obj = read(case/(stem+'.stdout'))
                if name == 'wrong_payload':
                    obj['records'][0]['message'] = 'different'
                elif name == 'authority_invented':
                    obj['input_dispatched'] = True
                elif name == 'reset_omission':
                    obj['records'] = obj['records'][2:]
                else:
                    obj = read(case/'expanded.stdout')
                (case/(stem+'.stdout')).write_text(json.dumps(obj)+'\n')
            manifest = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
            write(root/'MANIFEST.json', manifest)
            got = audit(root, mode)
            results.append({'control': name, 'rejected': bool(got['errors']),
                            'errors': got['errors']})
    return {'baseline': baseline['decision'], 'controls': results,
            'passed': all(r['rejected'] for r in results), 'count': len(results)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('root', type=Path)
    p.add_argument('--mode', choices=('construction','formal'), required=True)
    a = p.parse_args(); result = controls(a.root, a.mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result['passed'] else 1)
