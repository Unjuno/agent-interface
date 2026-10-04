"""Frozen cohort linkage plus deliberate missing/misattributed references."""
import copy
import json
from pathlib import Path
from causal_trace import build, export

HERE = Path(__file__).resolve().parent
root = HERE/'results/servo-recovery-02'
out = HERE/'results/causal-trace-01'
out.mkdir(exist_ok=False)
events = [json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
original = copy.deepcopy(events)
graph = export(root, out/'graph.json')
assert events == original
assert len(graph['gaps']) == 3
cases = {}
for case in ['missing_source', 'stale_source', 'wrong_authority', 'expired_input', 'wrong_feedback_program']:
    changed = copy.deepcopy(events)
    submit = next(r for r in changed if r['event']=='command' and r['command'].get('id')=='recover')
    admission = next(r for r in changed if r['event']=='pointer_admission')
    feedback = next(r for r in changed if r['event']=='servo_feedback')
    if case=='missing_source': submit['command']['expected_sequence']=9999
    elif case=='stale_source': submit['command']['expected_sequence']=1
    elif case=='wrong_authority': admission['valid_until_ns']+=1
    elif case=='expired_input': admission['admitted_ns']=admission['valid_until_ns']
    elif case=='wrong_feedback_program': feedback['id']='save'
    try:
        build(changed)
    except ValueError as exc:
        cases[case]=str(exc)
    else:
        raise AssertionError(case)
report = dict(nodes=len(graph['nodes']), edges=len(graph['edges']), gaps=graph['gaps'], negative_controls=cases)
(out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
