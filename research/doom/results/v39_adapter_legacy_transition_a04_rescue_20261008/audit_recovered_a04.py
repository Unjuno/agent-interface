"""Verify the recovered A04 archive without rerunning its experiment."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SNAPSHOTS = ROOT / "source_snapshots"
RESULT = json.loads((ROOT / "A04_RESULT.json").read_text(encoding="utf-8"))
SAVED_AUDIT = json.loads((ROOT / "A04_AUDIT.json").read_text(encoding="utf-8"))
EXECUTION = json.loads((ROOT / "A04_EXECUTION.json").read_text(encoding="utf-8"))
errors = []
checks = 0


def check(condition, label):
    global checks
    checks += 1
    if not condition:
        errors.append(label)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source_map = {
    "research/doom/map01_overlap_controller_v39.py": SNAPSHOTS / "candidate_source.py",
    "research/doom/test_map01_v39_typed_state_feedback.py": SNAPSHOTS / "test_source.py",
    "research/doom/map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl": SNAPSHOTS / "candidate-events.jsonl",
}
old_a04_prefix = (
    "research/doom/results/v39_adapter_edge_cardinality_59_a01_20261005/"
    "a04-legacy-transition-outer-event/"
)

check(RESULT.get("experiment") == "V39_LEGACY_TRANSITION_A04", "experiment identity")
check(RESULT.get("baseline_commit") == "46bed14701c6ba7d509c620bf6f582c84993f949", "baseline commit")
check(digest(ROOT / "BASELINE_SOURCE.py") == RESULT.get("baseline_source_sha256"), "baseline source hash")
for recorded_path, snapshot in source_map.items():
    expected_field = {
        "research/doom/map01_overlap_controller_v39.py": "candidate_source_sha256",
        "research/doom/test_map01_v39_typed_state_feedback.py": "test_sha256",
        "research/doom/map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl": "fixture_sha256",
    }[recorded_path]
    check(digest(snapshot) == RESULT.get(expected_field), f"snapshot hash: {recorded_path}")

manifest_checks = 0
for line in (ROOT / "SHA256SUMS_A04.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    expected, recorded_path = line.split(maxsplit=1)
    recorded_path = recorded_path.strip()
    if recorded_path.startswith(old_a04_prefix):
        local_path = ROOT / recorded_path[len(old_a04_prefix):]
    else:
        local_path = source_map.get(recorded_path)
    check(local_path is not None and local_path.is_file() and digest(local_path) == expected,
          f"original manifest: {recorded_path}")
    manifest_checks += 1
check(manifest_checks == 12, "all original manifest entries present")

baseline = RESULT.get("baseline", {})
candidate = RESULT.get("candidate", {})
check(baseline.get("expected_fail") is True and baseline.get("tests") == 2
      and baseline.get("failed_tests") == 1, "retained baseline red outcome")
check(candidate.get("passed") is True and candidate.get("tests") == 2
      and candidate.get("failed_tests") == 0, "retained candidate green outcome")
check("duplicate_up_as_legacy_transition" in baseline.get("output", "")
      and "adapter_edge_brackets_paired" in baseline.get("output", ""),
      "baseline exposes legacy duplicate pair")
candidate_output = candidate.get("output", "")
check(candidate_output.count(" ... ok") == 2 and candidate_output.rstrip().endswith("OK"),
      "candidate saved output")
check(SAVED_AUDIT.get("audit") == "PASS" and SAVED_AUDIT.get("checks") == 14
      and SAVED_AUDIT.get("errors") == [], "original independent audit")
check(EXECUTION.get("image") == "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
      and EXECUTION.get("container_policy", {}).get("network") == "none",
      "recorded isolated execution provenance")
check("swap-limit" in EXECUTION.get("resource_warning", "")
      or "cgroup" in EXECUTION.get("resource_warning", ""), "host resource warning retained")

fixture_rows = [
    json.loads(line)
    for line in (SNAPSHOTS / "candidate-events.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
down = next((row for row in fixture_rows if row.get("event") == "input_admission"), None)
up = next((row for row in fixture_rows if row.get("event") == "input_release_measurement"), None)
check(type(down) is dict and type(up) is dict, "raw input edges present")
if type(down) is dict and type(up) is dict:
    identity = ("id", "step", "key", "intent_token")
    check(tuple(down.get(key) for key in identity) == tuple(up.get(key) for key in identity),
          "raw pair identity")
    check(up.get("physical_key_measurement", {}).get("adapter_edge", {}).get("edge") == "up",
          "raw UP discriminator")

report = {
    "audit": "PASS" if not errors else "FAIL",
    "checks": checks,
    "errors": errors,
    "experiment_replayed": False,
    "scope": "saved A04 evidence integrity; one synthetic X-adapter fixture only",
}
output = ROOT / "RECOVERY_AUDIT.json"
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(bool(errors))
