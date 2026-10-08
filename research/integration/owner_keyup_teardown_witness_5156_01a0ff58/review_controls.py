"""Five directed integrity controls for the review's separate raw-only checker."""
import json
import shutil
import tempfile
from pathlib import Path
from witness_audit import audit

HERE = Path(__file__).resolve().parent


def main():
    source = HERE / 'review-01'
    control = audit(source)
    if control['errors']:
        raise ValueError('positive raw reconstruction failed')
    results = []
    for name in ('missing_row', 'wrong_head', 'wrong_case', 'wrong_mutation_value', 'raw_hash_corruption'):
        with tempfile.TemporaryDirectory(prefix='owner-witness-review-') as temp:
            out = Path(temp) / 'copied'
            shutil.copytree(source, out)
            report = json.loads((out / 'probe.json').read_bytes())
            if name == 'missing_row':
                report['rows'].pop()
            elif name == 'wrong_head':
                report['target_head'] = '0' * 40
            elif name == 'wrong_case':
                report['rows'][1]['name'] = 'wrong-case'
            elif name == 'wrong_mutation_value':
                report['rows'][1]['mutation_value'] = '0' * 32
            else:
                path = out / report['rows'][1]['file']
                path.write_bytes(path.read_bytes() + b' ')
            (out / 'probe.json').write_bytes((json.dumps(report, sort_keys=True, indent=2) + '\n').encode())
            result = audit(out)
            if not result['errors']:
                raise ValueError('corruption accepted:' + name)
            results.append({'case': name, 'errors': result['errors']})
    (HERE / 'controls.json').write_bytes((json.dumps({'positive_passed': True, 'controls': results},
                sort_keys=True, indent=2) + '\n').encode())
    print(json.dumps({'unchanged_positive': 'PASS', 'corruptions_rejected': len(results), 'total': 5}))


if __name__ == '__main__':
    main()
