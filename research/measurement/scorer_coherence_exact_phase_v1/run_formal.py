from __future__ import annotations
import hashlib, json
from pathlib import Path
from model import failure_phase_intervals, interval_cardinality
from oracle import closed_form_failure_count

ROOT = Path(__file__).resolve().parent
RESULT = ROOT/'RESULT.json'
INV = ROOT/'FORMAL_INVOCATION.json'


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    if RESULT.exists() or INV.exists():
        raise SystemExit('formal result/invocation already exists; rerun forbidden')
    schedule = json.loads((ROOT/'schedule.json').read_text())
    rows = []
    disagreement = 0
    for case in schedule['cases']:
        n = case['attempts']; d = case['span_ns']; T = schedule['period_ns']
        intervals = failure_phase_intervals(T, d, n)
        exact = interval_cardinality(intervals)
        closed = closed_form_failure_count(T, d, n)
        if exact != closed:
            disagreement += 1
        rows.append({**case,
            'failure_intervals': [list(x) for x in intervals],
            'exact_failure_phase_count': exact,
            'closed_form_failure_phase_count': closed,
            'failure_fraction': exact/T,
            'guaranteed': exact == 0,
        })

    gate_errors = []
    for r in rows:
        b=r['boundary_ns']; d=r['span_ns']; n=r['attempts']
        if d <= b and r['exact_failure_phase_count'] != 0:
            gate_errors.append(f'n{n}: at/below boundary has failures at {d}')
        if d == b+1 and r['exact_failure_phase_count'] <= 0:
            gate_errors.append(f'n{n}: boundary+1ns not detected')
        if d >= schedule['period_ns'] and r['exact_failure_phase_count'] <= 0:
            gate_errors.append(f'n{n}: d>=T marked guaranteed')
    n2 = [r for r in rows if r['attempts']==2 and r['span_ns']==r['boundary_ns']+1]
    if len(n2)!=1 or n2[0]['exact_failure_phase_count'] != 1:
        gate_errors.append('n2 predecessor 1ns control not exactly one failing integer phase')

    decision = 'PASS_EXACT_COHERENCE_PHASE_GEOMETRY_SCOPED' if disagreement==0 and not gate_errors else 'FAIL_EXACT_GEOMETRY_IMPLEMENTATION'
    inv = {'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
    INV.write_text(json.dumps(inv, indent=2, sort_keys=True)+'\n')
    result = {
        'decision': decision,
        'period_ns': schedule['period_ns'],
        'rows': rows,
        'method_disagreements': disagreement,
        'gate_errors': gate_errors,
        'invocation': inv,
        'schedule_sha256': sha256(ROOT/'schedule.json'),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'rows':len(rows),'gate_errors':gate_errors},sort_keys=True))
    if decision.startswith('FAIL_'):
        raise SystemExit(2)

if __name__ == '__main__': run()
