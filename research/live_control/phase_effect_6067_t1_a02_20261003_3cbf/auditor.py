"""Single saved-only A02 invocation: historical audit plus stable-source gate.

Historical oracle and candidate execution guard share frozen A01 code, explicitly
not independent implementations. This process does not import execution_guard,
producer, observer, policy or fixture execution code and never acquires images.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import audit
from qualification import qualify
from admission import require_formal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', type=Path, required=True)
    ap.add_argument('--fixture', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    require_formal()
    # Audit.main checks the frozen original oracle, full source receipt,
    # all 114 cells, typed journal joins, native pixels, controls and 8 mutations.
    audit.main()
    fixture = audit.read(args.fixture)
    qualified = []
    for spec in fixture['cases']:
        cell = args.raw / 'cells' / spec['id']
        q = qualify(audit.read(cell / 'source.json'), audit.read(cell / 'capture.json'))
        qualified.append({**spec, **q})
    counts = {a: sum(q['kind'] == 'pulse' and not q['stable_ids'] for q in qualified if q['schedule'] == a)
              for a in ('fixed', 'irregular', 'rotated')}
    fixed_blind_width = all(any(q['kind'] == 'pulse' and q['schedule'] == 'fixed' and q['width_ms'] == w
                               and not q['stable_ids'] for q in qualified) for w in (10,20,30))
    clean = all(q['boundary_hits'] == 0 and q['unknown_frames'] == 0 for q in qualified)
    base = audit.read(args.out / 'audit.json')
    benefit = clean and fixed_blind_width and counts['irregular'] < counts['fixed'] and counts['rotated'] < counts['fixed']
    status = ('HOLD_SOURCE_BOUNDARY_AMBIGUITY' if not clean else
              'PASS_NATIVE_PHASE_EFFECT_SCOPED' if benefit and base['status'] == 'PASS_TRANSFER_SCOPED' else
              'HOLD_BENEFIT_NOT_ESTABLISHED')
    result = {'status': status, 'historical_gate_status': base['status'], 'qualified_all_miss_episodes': counts,
              'boundary_hits': sum(q['boundary_hits'] for q in qualified),
              'unknown_frames': sum(q['unknown_frames'] for q in qualified),
              'cells_checked': len(qualified), 'captures_checked': 8 * len(qualified), 'results': qualified,
              'scope': 'finite private native X11 color/ID only; no input/model/task/safety transfer'}
    (args.out / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'results'}, sort_keys=True))

if __name__ == '__main__': main()
