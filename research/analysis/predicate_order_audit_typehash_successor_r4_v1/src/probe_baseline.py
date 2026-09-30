import copy
import json
from pathlib import Path

import audit_hardened


raw = json.loads(Path("/input/RAW.json").read_text(encoding="utf-8"))
print("baseline", audit_hardened.audit_document(raw))
cases = []

def mutate(label, path, value):
    candidate = copy.deepcopy(raw)
    target = candidate
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    cases.append((label, candidate))


mutate("cost.A", ["cost", "A"], True)
mutate("drift_grid[0]", ["drift_grid", 0], False)
mutate("final alpha", ["distributions", -1, "alpha"], True)
mutate("row state_id=1", ["distributions", 0, "rows", 1, "state_id"], True)
mutate("truth bool->int", ["distributions", 0, "rows", 0, "truth", "A"], 0)
mutate("replay cost", ["distributions", 0, "rows", 0, "NAIVE", "cost"], True)
mutate("replay evaluations", ["distributions", 0, "rows", 0, "NAIVE", "evaluations"], True)
mutate("semantic_mismatches", ["distributions", 0, "summaries", "NAIVE", "semantic_mismatches"], False)

for label, candidate in cases:
    try:
        audit_hardened.audit_document(candidate)
        print(label, "ACCEPT")
    except Exception as exc:
        print(label, "REJECT", str(exc))
