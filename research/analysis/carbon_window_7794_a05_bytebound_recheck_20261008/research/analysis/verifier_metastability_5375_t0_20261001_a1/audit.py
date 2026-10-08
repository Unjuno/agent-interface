"""Independent raw-only arithmetic audit; imports neither candidate nor source."""
import json
import sys
from collections import defaultdict
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("candidate.jsonl")
groups = defaultdict(list)
errors = []
for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    try:
        r = json.loads(line)
    except Exception as exc:
        errors.append((line_no, "json", str(exc)))
        continue
    required = {"tick", "case", "policy", "offered", "queue_before", "admitted", "queue_after", "safety_service", "authority_admissions"}
    if not required.issubset(r):
        errors.append((line_no, "missing_fields"))
        continue
    if r["queue_before"] + r["offered"] - r["admitted"] != r["queue_after"]:
        errors.append((line_no, "queue_conservation"))
    if r["admitted"] < 0 or r["admitted"] > r["service_capacity"]:
        errors.append((line_no, "service_capacity"))
    if r["safety_service"] < 0 or r["safety_service"] > r["service_capacity"]:
        errors.append((line_no, "safety_capacity"))
    if r["authority_admissions"] != 0:
        errors.append((line_no, "authority_nonzero"))
    groups[(r["case"], r["policy"])].append(r)

for key, rows in groups.items():
    rows.sort(key=lambda r: r["tick"])
    if [r["tick"] for r in rows] != list(range(len(rows))):
        errors.append((key, "tick_sequence"))
    for prev, cur in zip(rows, rows[1:]):
        if cur["queue_before"] != prev["queue_after"]:
            errors.append((key, cur["tick"], "queue_link"))
        if cur["retry_debt"] != prev["retry_debt"] + cur["retry_added"] - cur["shed"]:
            errors.append((key, cur["tick"], "debt_conservation"))

summary = {"rows": sum(map(len, groups.values())), "groups": len(groups), "errors": errors}
print(json.dumps(summary, sort_keys=True))
if errors:
    raise SystemExit(1)
