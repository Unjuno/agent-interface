import json
from pathlib import Path

path = Path(__file__).with_name("candidate_raw.json")
payload = json.loads(path.read_text(encoding="utf-8"))
states = (0, 1, 2, 3)
ops = ("perfect", "minimal", "partial")
errors = []
expected = []
for initial in states:
    before = initial + 1
    for op in ops:
        post = 0 if op == "perfect" else before if op == "minimal" else max(0, before - 2)
        recurrence = None
        for tick in range(1, 3):
            if post + tick >= 4:
                recurrence = tick
                break
        expected.append((initial, op, before, post, recurrence))
actual = payload.get("rows", [])
if len(actual) != 12:
    errors.append("wrong row count")
seen = set()
for row in actual:
    key = (row.get("initial_state"), row.get("operator"))
    if key in seen:
        errors.append(f"duplicate cell {key}")
    seen.add(key)
    match = next((e for e in expected if e[:2] == key), None)
    if match is None:
        errors.append(f"unexpected cell {key}")
        continue
    _, op, before, post, recurrence = match
    if (row.get("pre_repair_state"), row.get("post_repair_state"), row.get("recurrence_tick")) != (before, post, recurrence):
        errors.append(f"raw transition mismatch {key}")
    if row.get("fault_before") is not (before >= 4):
        errors.append(f"fault label mismatch {key}")
    censored = recurrence is None
    if row.get("censored") is not censored or row.get("censor_horizon") != (2 if censored else None):
        errors.append(f"censor mismatch {key}")
if seen != {(s, o) for s in states for o in ops}:
    errors.append("incomplete cell coverage")
summary = payload.get("summary", {})
for op in ops:
    rows = [r for r in actual if r.get("operator") == op]
    want = {
        "episodes": 4,
        "recurrence_count": sum(r["recurrence_tick"] is not None for r in rows),
        "censored_count": sum(r["censored"] is True for r in rows),
        "fault_before_count": sum(r["fault_before"] is True for r in rows),
        "recurrence_ticks": [r["recurrence_tick"] for r in rows],
    }
    if summary.get(op) != want:
        errors.append(f"summary mismatch {op}")
print(json.dumps({"expected_rows": len(expected), "audited_rows": len(actual), "errors": errors}, sort_keys=True))
raise SystemExit(bool(errors))
