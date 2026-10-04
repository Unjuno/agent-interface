"""Independent consistency audit for the frozen construction output."""
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
raw = (ROOT / "construction-run.txt").read_text(encoding="utf-8")
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
report = (ROOT / "README.md").read_text(encoding="utf-8")


def section(prefix):
    start = raw.find(prefix)
    if start < 0:
        return ""
    end = raw.find("\n$ ", start + len(prefix))
    return raw[start:] if end < 0 else raw[start:end]


compile_result = section("$ python -m py_compile")
monitor_result = section("$ $env:PYTHONPATH='outputs\\coast-interrupt-handoff-prototype'; python -m unittest discover -s outputs\\coast-interrupt-handoff-prototype -p 'test_unauthored_coast_liveness_v1.py' -v")
controller_result = section("$ $env:PYTHONPATH='outputs\\coast-interrupt-handoff-prototype'; python -m unittest discover -s outputs\\coast-interrupt-handoff-prototype -p 'test_map01_overlap_controller_v40.py' -v")

checks = {
    "freeze_schema": freeze.get("schema") == "unauthored-coast-typed-interrupt-construction-freeze-v1",
    "frozen_candidate_commit_in_raw": freeze.get("candidate_commit") in raw,
    "v39_source_identity_pinned": freeze.get("current_v39_blob") == "0f3dfcada36520acb24fceaf26a4124c96e050b3",
    "compile_exit_zero": "exit_code=0" in compile_result,
    "nine_monitor_tests_pass": "Ran 9 tests" in monitor_result and re.search(r"\nOK\s*$", monitor_result) is not None,
    "three_controller_tests_pass": "Ran 3 tests" in controller_result and re.search(r"\nOK\s*$", controller_result) is not None,
    "report_limits_claims": "No new model/game/live allocation ran" in report and "do not estimate false interrupts" in report,
}
result = {
    "schema": "unauthored-coast-typed-interrupt-construction-audit-v1",
    "checks": checks,
    "pass": all(checks.values()),
}
print(json.dumps(result, indent=2, sort_keys=True))
if not result["pass"]:
    raise SystemExit(1)

