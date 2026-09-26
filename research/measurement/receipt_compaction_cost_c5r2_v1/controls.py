"""Effective mutations of copied saved evidence, not new measurements."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from audit import inspect


def run(base):
    case = json.loads((base / 'case-4/case.json').read_bytes())
    exe = json.loads((base / 'execution-4.json').read_bytes())
    expected = case['input_sha256']
    if inspect(case, exe, expected):
        raise ValueError('control baseline failed')
    results = []
    for kind in ('dropped_sample', 'wrong_input', 'boolean_exit', 'changed_pid',
                 'changed_hash', 'reordered_sample', 'false_release', 'false_authority',
                 'changed_raw_report', 'negative_duration'):
        c, e = copy.deepcopy(case), copy.deepcopy(exe)
        if kind == 'dropped_sample':
            c['samples'].pop()
        elif kind == 'wrong_input':
            c['input'] += ' '
        elif kind == 'boolean_exit':
            e['exit'] = False
        elif kind == 'changed_pid':
            e['pid'] += 1
        elif kind == 'changed_hash':
            c['samples'][0][-1] = '0' * 64
        elif kind == 'reordered_sample':
            c['samples'][0], c['samples'][1] = c['samples'][1], c['samples'][0]
        elif kind == 'negative_duration':
            c['samples'][0][6] = c['samples'][0][3] - 1
        else:
            out = json.loads(c['outputs']['compact'])
            if kind == 'false_release':
                out['outcome_summary']['input_release_verified'] = True
            elif kind == 'false_authority':
                out['authority'] = 'input'
            else:
                out['receipt']['source']['raw_report']['status'] = 'fabricated'
            wire = json.dumps(out, sort_keys=True, separators=(',', ':'), allow_nan=False)
            c['outputs']['compact'] = wire
            new_hash = hashlib.sha256(wire.encode()).hexdigest()
            for row in c['samples']:
                if row[2] == 'compact':
                    row[-1] = new_hash
        old = json.dumps([case, exe], sort_keys=True).encode()
        new = json.dumps([c, e], sort_keys=True).encode()
        errors = inspect(c, e, expected)
        results.append({'kind': kind, 'changed': old != new,
                        'mutation_sha256': hashlib.sha256(new).hexdigest(), 'errors': errors})
    result = {'passed': all(r['changed'] and r['errors'] for r in results), 'count': len(results), 'results': results}
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(run(Path(sys.argv[1])))
