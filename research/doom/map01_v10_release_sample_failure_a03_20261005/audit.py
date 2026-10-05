"""Read-only integrity audit for the retained V10 A03 fake-X matrix."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
checks = []

base = subprocess.run(
    ["git", "show", f"{freeze['base_commit']}:research/live_control/input_owner_v10.py"],
    cwd=ROOT.parents[2], check=True, capture_output=True,
).stdout
checks.append(hashlib.sha256(base).hexdigest() ==
              freeze["sources"]["baseline"]["input_owner_v10.py"])

for variant in ("baseline", "candidate"):
    for filename, expected in freeze["sources"][variant].items():
        actual = hashlib.sha256((ROOT / "source" / variant / filename).read_bytes()).hexdigest()
        checks.append(actual == expected)

for filename, expected in freeze["sources"]["candidate"].items():
    current = (ROOT.parents[2] / "research/live_control" / filename).read_bytes()
    checks.append(hashlib.sha256(current).hexdigest() == expected)
    committed = subprocess.run(
        ["git", "show", f"{freeze['candidate_commit']}:research/live_control/{filename}"],
        cwd=ROOT.parents[2], check=True, capture_output=True,
    ).stdout
    checks.append(hashlib.sha256(committed).hexdigest() == expected)

checks.append(
    (ROOT / "source/baseline/test_input_owner_v10_release_retry.py").read_bytes()
    == (ROOT / "source/candidate/test_input_owner_v10_release_retry.py").read_bytes()
)
for variant in ("baseline", "candidate"):
    for mode in ("normal", "optimized"):
        result = json.loads((ROOT / "raw" / f"{variant}-{mode}.json").read_text(encoding="utf-8"))
        stream = result["stdout"] + result["stderr"]
        checks.extend((result["variant"] == variant, result["mode"] == mode,
                       "Ran 5 tests" in stream,
                       "test_wheel_retry_survives_a_transient_keymap_query_error" in stream,
                       "test_persistent_keymap_error_still_retries_button_and_records_unknown_keys" in stream))
        if variant == "candidate":
            checks.extend((result["exit_code"] == 0, "OK" in stream))
        else:
            checks.extend((result["exit_code"] == 1,
                           "FAILED (failures=3, errors=1)" in stream,
                           "Items in the first set but not the second" in stream))

candidate_source = (ROOT / "source/candidate/input_owner_v10.py").read_text(encoding="utf-8")
checks.extend(token in candidate_source for token in (
    "buttons_state_known=pointer_known", "keys_state_known=keymap_known",
    "keys_unknown=[] if keymap_known else sorted(touched)",
    "if not verified:",
))

for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    checks.append(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected)

result = {"checks": len(checks), "passed": sum(checks),
          "status": "PASS" if all(checks) else "FAIL",
          "scope": "retained fake-X source/output integrity only"}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks) else 1)
