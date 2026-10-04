"""Independent raw-derived checks for A03 result and unsupported-row handling."""
import hashlib
import json
from pathlib import Path


ROOT = Path("/src")
DOOM = ROOT / "research/doom"
HERE = DOOM / "results/v39_adapter_edge_cardinality_59_a01_20261005/a03-unknown-outer-event"
RAW = DOOM / "map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
record = json.loads((Path("/evidence") / "A03_RESULT.json").read_text(encoding="utf-8"))
fixture = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines() if line]
errors = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


check(record.get("experiment") == "V39_UNKNOWN_OUTER_EVENT_A03", "wrong experiment")
check(record.get("fixture_sha256") == hashlib.sha256(RAW.read_bytes()).hexdigest(),
      "raw fixture digest mismatch")
check(record.get("candidate_source_sha256") ==
      hashlib.sha256((DOOM / "map01_overlap_controller_v39.py").read_bytes()).hexdigest(),
      "candidate source digest mismatch")
check(record.get("test_sha256") == hashlib.sha256(
    (DOOM / "test_map01_v39_typed_state_feedback.py").read_bytes()).hexdigest(),
      "test source digest mismatch")
check(record.get("baseline", {}).get("expected_fail") is True,
      "baseline did not fail as preregistered")
check(record.get("candidate", {}).get("passed") is True,
      "candidate did not pass")
check(record.get("baseline", {}).get("tests") == 2 and
      record.get("candidate", {}).get("tests") == 2,
      "unexpected targeted test count")

down = next((row for row in fixture if row.get("event") == "input_admission"), None)
up = next((row for row in fixture if row.get("event") == "input_release_measurement"), None)
check(type(down) is dict and type(up) is dict, "frozen fixture lacks unique edge rows")
if type(down) is dict and type(up) is dict:
    identity = tuple(down.get(key) for key in ("id", "step", "key", "intent_token"))
    check(identity == tuple(up.get(key) for key in ("id", "step", "key", "intent_token")),
          "frozen edge rows do not share the exact outer identity")
    check(down.get("physical_key_measurement", {}).get("adapter_edge", {}).get("edge") == "down",
          "DOWN nested discriminator changed")
    check(up.get("physical_key_measurement", {}).get("adapter_edge", {}).get("edge") == "up",
          "UP nested discriminator changed")

baseline_text = record.get("baseline", {}).get("output", "")
candidate_text = record.get("candidate", {}).get("output", "")
check("duplicate_down_unknown_kind" in baseline_text and
      "duplicate_up_unknown_kind" in baseline_text,
      "baseline red output did not expose both ignored duplicate edges")
check(candidate_text.count(" ... ok") == 2 and candidate_text.rstrip().endswith("OK"),
      "candidate output is not two passing targeted tests")

report = {"audit": "PASS" if not errors else "FAIL", "checks": checks,
          "errors": errors,
          "scope": "one retained synthetic X-adapter fixture; deterministic projection only"}
Path("/audit/A03_AUDIT.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(bool(errors))
