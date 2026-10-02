import json
import copy
import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent
subprocess.run([sys.executable, str(root / "candidate.py")], check=True, capture_output=True, text=True)
raw = json.loads((root / "candidate.json").read_text())
from auditor import validate
cases = json.loads((root / "cases.json").read_text())
key = json.loads((root / "key.json").read_text())
assert validate(cases, key, raw) == []
drop = copy.deepcopy(raw)
failed = next(r["row_id"] for s in cases["scenarios"] if s["id"] == "switch_and_failure" for r in s["rows"] if r["outcome"] == "failed")
switch = next(r for r in drop["scenario_results"] if r["scenario"] == "switch_and_failure")
switch["row_ids"].remove(failed)
assert validate(cases, key, drop)
erase = copy.deepcopy(raw)
switch = next(r for r in erase["scenario_results"] if r["scenario"] == "switch_and_failure")
pair = next(p for p in switch["annotation_pairs"] if p["row_id"] == "s2-h-fail")
pair["a"]["switches"] = 0
assert validate(cases, key, erase)
from annotator_a import annotate
row = copy.deepcopy(cases["scenarios"][1]["rows"][0])
row["arm"] = "H"
try:
    annotate(row)
    raise AssertionError("arm-visible coder input was accepted")
except ValueError:
    pass
assert all(x["coder_agreement"] >= 0.90 and x["all_rows_preserved"] for x in raw["scenario_results"])
assert raw["horizon_sensitivity"]["4"] == {"H": 51000, "A": 40000}
assert raw["horizon_sensitivity"]["10"] == {"H": 75000, "A": 100000}
first = next(x for x in raw["scenario_results"] if x["scenario"] == "shortcut_asymmetry")
assert first["acquisition_inclusive_horizon_ms"] == {"H": 51000, "A": 40000}
null = next(x for x in raw["scenario_results"] if x["scenario"] == "equal_method_null")
assert null["natural_method_elapsed_ms"] == {"H": 22000, "A": 22000}
sw = next(x for x in raw["scenario_results"] if x["scenario"] == "switch_and_failure")
assert sum(x["failed"] for x in sw["method_summary"]) == 1
assert sum(x["switches"] for x in sw["method_summary"]) == 1
print("PASS construction=11 assertions incl 3 rejected mutations")
