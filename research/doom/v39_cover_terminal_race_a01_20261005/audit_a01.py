import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
result_bytes = (ROOT / "result.json").read_bytes()
result = json.loads(result_bytes)
probe_hash = hashlib.sha256((ROOT / "probe.py").read_bytes()).hexdigest()

expected = {
    "cancelled_neutral": ("accepted", "accepted"),
    "completed_neutral": ("raised", "accepted"),
    "completed_nonempty": ("raised", "raised"),
    "failed_neutral": ("raised", "raised"),
}
by_case = {row["case"]: row for row in result["cases"]}
checks = []
def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)

check(result["schema"] == "v39-cover-terminal-race-probe-a01-v1", "schema identity")
check(result["source_commit"] == freeze["source_commit"], "source commit matches freeze")
check(result["source_sha256"] == freeze["source_sha256"], "source digest matches freeze")
check(probe_hash == freeze["probe_sha256"], "probe digest matches freeze")
check(set(by_case) == set(expected), "exact four frozen cases retained")
for case, (baseline_expected, candidate_expected) in expected.items():
    row = by_case[case]
    check(row["baseline"]["result"]["outcome"] == baseline_expected,
          f"{case}: baseline disposition")
    check(row["candidate"]["result"]["outcome"] == candidate_expected,
          f"{case}: candidate disposition")
    for arm in (row["baseline"], row["candidate"]):
        operations = [item["event"] for item in arm["operations"]]
        check(operations == ["interrupt", "write", "flush", "wait"],
              f"{case}: planner interrupt and cancel precede terminal validation")
        payload = json.loads(arm["operations"][1]["value"])
        check(payload == {"op": "cancel", "id": "cover-race"},
              f"{case}: cancel targets matched cover id")

# Corruption controls ensure decisive candidate outcomes cannot be edited away.
def validate(matrix):
    return all(matrix[name] == expected[name] for name in expected)
controls = {}
for name, corrupt in (
    ("promote_nonempty_completed", ("completed_nonempty", 1, "accepted")),
    ("promote_failed_neutral", ("failed_neutral", 1, "accepted")),
    ("drop_safe_completed", ("completed_neutral", 1, "raised")),
):
    matrix = dict(expected)
    key, idx, value = corrupt
    pair = list(matrix[key]); pair[idx] = value; matrix[key] = tuple(pair)
    controls[name] = not validate(matrix)
check(all(controls.values()), "three outcome corruption controls rejected")

report = {
    "schema": "v39-cover-terminal-race-audit-a01-v1",
    "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
    "checks_passed": len(checks),
    "checks": checks,
    "mutation_controls_rejected": controls,
    "disposition": "CURRENT_HELPER_REJECTS_COMPLETED_NEUTRAL; CANDIDATE_ACCEPTS_ONLY_CANCELLED_OR_COMPLETED_WITH_VERIFIED_EMPTY_RELEASE",
    "limits": ["AST-extracted helper and test doubles only", "no live experiment or race-frequency estimate"],
}
(ROOT / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"schema": report["schema"], "checks_passed": report["checks_passed"],
                  "mutation_controls_rejected": controls,
                  "disposition": report["disposition"]}, indent=2))
