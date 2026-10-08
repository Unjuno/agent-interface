import json
import sys
from collections import defaultdict
from pathlib import Path

CAP = 20
EXPECTED = 4 * 4 * 30
errors = []
groups = defaultdict(list)
raw = Path("/out/raw.jsonl")
for n, line in enumerate(raw.read_text(encoding="utf-8").splitlines(), 1):
    try:
        x = json.loads(line)
        if set(x) != {"policy", "condition", "tick", "offered", "admitted", "deferred", "completed", "safety", "cost", "dropped", "authority", "capacity", "total_cost"}:
            errors.append(f"row {n}: schema")
            continue
        if x["capacity"] != CAP or sum(x["cost"].values()) != x["total_cost"]:
            errors.append(f"row {n}: accounting")
        if x["total_cost"] > CAP or x["safety"] != int(x["cost"]["safety_service"] == 1):
            errors.append(f"row {n}: capacity/safety")
        if x["authority"] != 0 or x["dropped"] not in (0, 1):
            errors.append(f"row {n}: authority/drop type")
        if x["admitted"] + x["deferred"] + x["dropped"] < 0:
            errors.append(f"row {n}: obligation conservation")
        groups[(x["policy"], x["condition"])].append(x)
    except Exception as e:
        errors.append(f"row {n}: {type(e).__name__}")
if len(groups) != 16 or any(len(v) != 30 for v in groups.values()) or sum(map(len, groups.values())) != EXPECTED:
    errors.append("coverage")
for key, rows in groups.items():
    rows.sort(key=lambda x: x["tick"])
    if [x["tick"] for x in rows] != list(range(30)):
        errors.append(f"{key}: chronology")
    for a, b in zip(rows, rows[1:]):
        if b["deferred"] > a["deferred"] + b["offered"]:
            errors.append(f"{key}: deferred conservation")

def all_safety(policy, condition, ticks):
    return all(x["safety"] == 1 for x in groups[(policy, condition)] if x["tick"] in ticks)

storm_ticks = range(1, 8)
benefit = (not all_safety("backend", "storm", storm_ticks)
           and all_safety("upstream", "storm", storm_ticks))
null_clean = all_safety("backend", "zero_reject", storm_ticks)
bounded_clean = all_safety("backend", "bounded", range(0, 8))
drop_detected = any(x["dropped"] for x in groups[("upstream", "planted_drop")])
status = "PASS_METHOD_SCOPED" if not errors and benefit and null_clean and bounded_clean and drop_detected else "FAIL_OR_HOLD"
result = {"status": status, "rows": sum(map(len, groups.values())), "errors": errors,
          "benefit_fixture": benefit, "zero_cost_null_clean": null_clean,
          "bounded_control_clean": bounded_clean, "planted_drop_detected": drop_detected,
          "authority_admissions": sum(x["authority"] for v in groups.values() for x in v)}
Path("/out/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
sys.exit(0 if status == "PASS_METHOD_SCOPED" else 1)

