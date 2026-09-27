"""Retained-evidence corruption controls; never reruns the GUI experiment."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from audit import audit


def main(root, construction):
    baseline = audit(root, construction)
    if baseline['result'] != 'PASS_WIDGET_PHASE_BOUNDARY_SCOPED':
        raise RuntimeError('baseline must pass before corruption controls')
    first = json.loads((root / 'run.json').read_text())['rows'][0]
    cases = ['missing_case', 'duplicate_case', 'receipt_epoch_boolean',
             'nonneutral_release', 'effect_value', 'missing_process_exit']
    results = []
    for case in cases:
        with tempfile.TemporaryDirectory(prefix='widget-audit-control-') as tmp:
            dst = Path(tmp) / 'evidence'
            shutil.copytree(root, dst)
            if case in ['missing_case', 'duplicate_case']:
                path = dst / 'run.json'
                obj = json.loads(path.read_text())
                if case == 'missing_case':
                    obj['rows'].pop()
                else:
                    obj['rows'][-1] = obj['rows'][0]
            elif case == 'effect_value':
                path = dst / first / 'effects.jsonl'
                obj = json.loads(path.read_text().splitlines()[0])
                obj['value'] = 99
            else:
                path = dst / first / 'row.json'
                obj = json.loads(path.read_text())
                if case == 'receipt_epoch_boolean':
                    obj['candidate_receipt']['epoch'] = True
                elif case == 'nonneutral_release':
                    obj['final_server']['button_mask'] = 256
                else:
                    obj['app_returncode'] = None
            path.write_text(json.dumps(obj, sort_keys=True) + '\n')
            # Rehash the mutation: controls must test semantics, not just stale digests.
            manifest = {str(p.relative_to(dst)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(dst.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
            (dst / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True) + '\n')
            result = audit(dst, construction)
            results.append({'case': case, 'rejected': not result['result'].startswith('PASS'),
                            'result': result['result'], 'errors': result['errors'],
                            'gate_failures': result['gate_failures']})
    return {'baseline': baseline['result'], 'controls': results,
            'pass': len(results) == 6 and all(r['rejected'] for r in results)}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    p.add_argument('--construction', action='store_true')
    args = p.parse_args()
    result = main(args.root, args.construction)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result['pass'] else 1)
