"""Effective copied-evidence controls; does not rerun any X11 actor."""
import copy
import hashlib
import json
import sys
from pathlib import Path
from audit import audit, load_cases


def check_controls(cases, ids, hashes):
    baseline = audit(cases, ids, hashes)
    if baseline['errors']:
        raise ValueError('control baseline has audit errors')
    live = next(i for i, c in enumerate(cases) if c['raw']['scenario'] == 'LIVE_RELEASE')
    destroyed = next(i for i, c in enumerate(cases) if c['raw']['scenario'] == 'DESTROY_RELEASE')
    held = next(i for i, c in enumerate(cases) if c['raw']['scenario'] == 'DESTROY_HELD')
    lost = next(i for i, c in enumerate(cases) if c['raw']['scenario'] == 'DESTROY_WITNESS_LOST')
    variants = []

    def add(name, mutator):
        changed = copy.deepcopy(cases)
        mutator(changed)
        if changed == cases:
            raise AssertionError('no-op corruption: ' + name)
        outcome = audit(changed, ids, hashes)
        variants.append(dict(name=name, effective=changed != cases,
                             rejected=bool(outcome['errors']), errors=outcome['errors']))

    add('wrong_epoch', lambda c: c[destroyed]['raw']['policy_request']['identity'].update(epoch='foreign'))
    add('wrong_actuation', lambda c: c[live]['raw']['down'].update(actuation='foreign'))
    add('contradictory_key_bit', lambda c: c[held]['raw']['post'].update(key_down=False))
    add('missing_recipient_event', lambda c: c[live]['recipient'].pop(next(i for i,r in enumerate(c[live]['recipient']) if r['kind']=='key_event')))
    add('unknown_promoted', lambda c: c[lost]['raw']['policy_result'].update(server='SERVER_RELEASE_OBSERVED'))
    add('held_promoted', lambda c: c[held]['raw']['policy_result'].update(server='SERVER_RELEASE_OBSERVED'))
    add('authority_granted', lambda c: c[live]['raw']['policy_result'].update(authority='task_input'))
    add('nonneutral_final', lambda c: c[held]['raw']['final_state'].update(key_down=True))
    add('process_exit_missing', lambda c: c[live]['raw']['processes'][0].update(returncode=None))
    add('source_changed', lambda c: c[live]['raw']['source_hashes'].update({'source/policy.py': '0'*64}))
    add('reversed_query_time', lambda c: c[destroyed]['raw']['post'].update(query_start_ns=c[destroyed]['raw']['post']['query_end_ns']+1))
    add('denominator_missing', lambda c: c.pop())
    return dict(baseline=baseline['decision'], rejected=sum(v['rejected'] for v in variants),
                total=len(variants), controls=variants)


if __name__ == '__main__':
    root = Path(sys.argv[1])
    paths = sorted((root / 'evidence').glob('case-*/RAW.json'))
    cases = load_cases([p.parent for p in paths])
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'source').rglob('*.py'))}
    result = check_controls(cases, list(range(16)), hashes)
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(result['rejected'] != result['total'])
