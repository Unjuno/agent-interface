"""Construction-only checks; never substitute these for the frozen container run."""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
subprocess.run([sys.executable, str(ROOT / "candidate.py")], check=True, capture_output=True, text=True)
subprocess.run([sys.executable, str(ROOT / "auditor.py")], check=True, capture_output=True, text=True)
traces = json.loads((ROOT / "traces.json").read_text())
key = json.loads((ROOT / "key.json").read_text())
result = json.loads((ROOT / "candidate_result.json").read_text())
from auditor import validate
assert validate(traces, key, result) == []
audit = json.loads((ROOT / "audit_result.json").read_text())
assert audit["decision"] == "METHOD_PASS_SCOPED"
assert audit["attempts"] == 24
assert audit["mutation_controls_rejected"] == audit["mutation_controls_total"] == 4
assert sum(len(s["rows"]) for s in traces["scenarios"]) == 24
mix = next(s for s in result["scenarios"] if s["id"] == "shortcut_mixture")
assert mix["horizon_sensitivity"] == {
    "1": {"H": 57000, "A": 34000},
    "4": {"H": 123000, "A": 136000},
    "10": {"H": 255000, "A": 340000},
}
assert {x["mean_elapsed_ms"] for x in mix["method_summary"] if x["method"] == "shortcut"} == {4000}
assert {x["mean_elapsed_ms"] for x in mix["method_summary"] if x["method"] == "ordinary"} == {10000}
null = next(s for s in result["scenarios"] if s["id"] == "equal_method_null")
assert null["arms"]["H"]["scored_ms"] == null["arms"]["A"]["scored_ms"] == 72000
switch = next(s for s in result["scenarios"] if s["id"] == "switch_and_failure")
assert switch["arms"]["H"]["elapsed_ms"] == 24000
unfinished = next(s for s in result["scenarios"] if s["id"] == "unfinished_attempts")
assert unfinished["arms"]["H"]["elapsed_ms"] == 16000
assert unfinished["arms"]["H"]["penalty_ms"] == 240000

drop_failure = copy.deepcopy(result)
row = next(p for p in drop_failure["scenarios"] if p["id"] == "switch_and_failure")
row["attempt_ids"].remove("switch01-H")
row["annotation_pairs"] = [pair for pair in row["annotation_pairs"] if pair["row_id"] != "switch01-H"]
row["attempt_count"] -= 1
assert validate(traces, key, drop_failure)

omit_cost = copy.deepcopy(result)
mix_mut = next(s for s in omit_cost["scenarios"] if s["id"] == "shortcut_mixture")
mix_mut["horizon_sensitivity"]["4"]["H"] -= mix_mut["arms"]["H"]["acquisition_ms"]
assert validate(traces, key, omit_cost)

prohibited = copy.deepcopy(result)
null_mut = next(s for s in prohibited["scenarios"] if s["id"] == "equal_method_null")
ann = next(p for p in null_mut["annotation_pairs"] if p["row_id"] == "null01-H")
ann["a"]["segments"][0]["method"] = "shortcut"
assert validate(traces, key, prohibited)

arm_visible = copy.deepcopy(traces["scenarios"][1]["rows"][0])
arm_visible["arm"] = "H"
from coder_a import annotate
try:
    annotate(arm_visible, traces["unfinished_penalty_ms"])
    raise AssertionError("arm-visible input accepted")
except ValueError:
    pass

print("PASS construction assertions=15 mutation_controls=4; this suite does not invoke the formal candidate or auditor")
