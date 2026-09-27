"""Eight effective copied-output checks; originals remain untouched."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from audit import audit
from io_data import inputs

HERE = Path(__file__).resolve().parent


def controls(records, cases, freeze, *, full=True):
    if audit(records, cases, freeze, full=full)['errors']:
        raise ValueError('control baseline must pass')
    results = []
    for kind in ('source_index', 'execution_status', 'release', 'partial_effect',
                 'report_hash', 'missing_row', 'duplicate_row', 'image_exit'):
        changed = deepcopy(records)
        if kind == 'missing_row':
            changed['rows'].pop()
        elif kind == 'duplicate_row':
            changed['rows'][-1] = deepcopy(changed['rows'][0])
        else:
            cid = 'image_missing' if kind == 'image_exit' else ('h04' if kind == 'partial_effect' else 'h02')
            row = next(r for r in changed['rows'] if r['case'] == cid)
            output = json.loads(row['stdout'])
            if kind == 'source_index':
                output['outcome_summary']['validation_source_operation']['source_operation_index'] = 99
            elif kind == 'execution_status':
                output['outcome_summary']['execution_status'] = 'completed'
            elif kind == 'release':
                output['outcome_summary']['input_release_verified'] = True
            elif kind == 'partial_effect':
                output['outcome_summary']['failed_operation_effect'] = 'no input occurred'
            elif kind == 'report_hash':
                output['receipt']['source']['sha256'] = 'f' * 64
            elif kind == 'image_exit':
                row['exit'] = 0
            row['stdout'] = json.dumps(output, sort_keys=True) + '\n'
        if changed == records:
            raise ValueError('ineffective control')
        result = audit(changed, cases, freeze, full=full)
        results.append({'mutation': kind, 'rejected': bool(result['errors']), 'errors': result['errors']})
    return {'controls': results, 'effective': len(results),
            'rejected': sum(r['rejected'] for r in results), 'baseline_passed': True}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('records', type=Path)
    args = p.parse_args()
    result = controls(json.loads(args.records.read_text()), inputs(HERE),
                      json.loads((HERE / 'FREEZE.json').read_text())['files'])
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result['rejected'] == 8 else 1)
