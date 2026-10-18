"""Exercise the frozen PR #7695 completeness wrapper under inventory mutations."""
import copy
import json
from pathlib import Path

from candidate import summarize_complete

HERE = Path(__file__).resolve().parent
raw = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
full = copy.deepcopy(raw["events"])
omitted = [row for row in copy.deepcopy(full)
           if not (row.get("kind") == "key_interval" and row.get("key") == "SPACE")]
outcomes = {
    "complete_correct_inventory": summarize_complete(full),
    "omitted_correct_inventory": summarize_complete(omitted),
    "omitted_underdeclared_inventory": summarize_complete(omitted, ("W",)),
    "complete_underdeclared_inventory": summarize_complete(full, ("W",)),
}
passed = (
    outcomes["complete_correct_inventory"]["status"] == "BOUNDED"
    and outcomes["omitted_correct_inventory"]["status"] == "UNKNOWN"
    and outcomes["omitted_underdeclared_inventory"]["status"] == "BOUNDED"
    and outcomes["omitted_underdeclared_inventory"]["intervals"] == [
        {"action_id": "act-1", "epoch": 7, "key": "W", "lower_ns": 70, "upper_ns": 90}
    ]
    and outcomes["complete_underdeclared_inventory"]["status"] == "UNKNOWN"
)
report = {
    "allocation": "MAP01-EXPECTED-INVENTORY-PROVENANCE-A01-20261005",
    "status": "PASS_INVENTORY_PROVENANCE_COUNTEREXAMPLE" if passed else "FAIL",
    "cases": outcomes,
    "scope": "deterministic retained synthetic fixture; candidate wrapper behavior only",
}
(HERE / "experiment-output.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 1)
