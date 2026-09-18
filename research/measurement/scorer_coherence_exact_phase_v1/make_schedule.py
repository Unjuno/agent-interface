from __future__ import annotations
import json
from pathlib import Path
from oracle import guaranteed_boundary

ROOT = Path(__file__).resolve().parent
T = round(1_000_000_000 / 35)
cases = []
for attempts in [2,3,4]:
    b = guaranteed_boundary(T, attempts)
    spans = [b-1, b, b+1, b+1000, T]
    if attempts == 3:
        spans += [20_000_000, 25_000_000]
    for span in sorted(set(spans)):
        cases.append({'attempts': attempts, 'span_ns': span, 'boundary_ns': b})
obj = {
    'task': 'SCORER-COHERENCE-EXACT-PHASE-SUCCESSOR-20260918-001',
    'period_ns': T,
    'cases': cases,
    'formal_invocation_limit': 1,
    'reruns_allowed': 0,
    'predecessor_issue': 944,
    'predecessor_disposition': 'HOLD_GRID_TOO_COARSE',
}
(ROOT/'schedule.json').write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')
print(json.dumps(obj, sort_keys=True))
