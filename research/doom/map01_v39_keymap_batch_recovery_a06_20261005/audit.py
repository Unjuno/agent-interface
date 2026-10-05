"""Independent raw/source audit for A06; does not import candidate code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "FREEZE.json").read_text())
errors = []
for path, expected in freeze["source_sha256"].items():
    if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
        errors.append("source_hash:" + path)
lines = (HERE / "results/A06/RAW.jsonl").read_text().splitlines()
cases = [json.loads(line) for line in lines]
if [case.get("case") for case in cases] != [
        "normal", "drop_explicit_space_once", "cleanup_query_unavailable_once"]:
    errors.append("case_order_or_incremental_persistence")
if len(cases) >= 1:
    normal = cases[0]
    if len(normal.get("release_rows", [])) != 2 or normal.get("close_error"):
        errors.append("normal_case_incomplete")
if len(cases) >= 2:
    dropped = cases[1]
    if (dropped.get("dropped_up_once") is not True
            or sum(e.get("event") == "key_up_dropped_once" for e in dropped.get("events", [])) != 1
            or dropped.get("close_error")
            or dropped.get("fake_keys_after_close") != []):
        errors.append("one_shot_cleanup_recovery")
if len(cases) >= 3:
    unavailable = cases[2]
    if (unavailable.get("disposition") != "HOLD_QUERY_UNAVAILABLE"
            or not any(e.get("event") == "query_keymap_unavailable"
                       for e in unavailable.get("events", []))):
        errors.append("query_failure_not_retained_as_hold")
result = {
    "status": "PASS_HARNESS_RESILIENCE_AND_RAW_CUSTODY" if not errors else "FAIL_A06_AUDIT",
    "errors": errors,
    "cases_persisted": len(cases),
    "raw_sha256": hashlib.sha256((HERE / "results/A06/RAW.jsonl").read_bytes()).hexdigest(),
    "scope": "fake-Xlib batch cleanup only; no physical or application authority",
}
(HERE / "results/A06/AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not errors else 1)
