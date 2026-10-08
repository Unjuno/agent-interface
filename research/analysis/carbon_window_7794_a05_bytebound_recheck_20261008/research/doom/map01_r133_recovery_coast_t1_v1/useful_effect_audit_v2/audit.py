#!/usr/bin/env python3
"""Independent raw-only audit; does not import the candidate or adjudicator."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_ORDER = [(1, "recovery"), (1, "coast"), (2, "coast"),
                  (2, "recovery"), (3, "recovery"), (3, "coast")]
EXPECTED_CASES = {"coast_only_kill_recovery_survives", "both_arms_kill_recovery_survives",
                  "no_positive_effect", "no_threat_contact", "overlapping_exposure"}

def audit(raw):
    errors = []
    cases = raw.get("cases") if isinstance(raw, dict) else None
    if raw.get("schema") != "r133-useful-effect-audit-raw-v2" or not isinstance(cases, dict) or set(cases) != EXPECTED_CASES:
        return ["case_inventory_or_schema"]
    for name, item in cases.items():
        rows, out = item.get("input"), item.get("adjudication")
        if not isinstance(rows, list) or len(rows) != 6 or not isinstance(out, dict):
            errors.append(name + ":shape"); continue
        if [(r.get("pair_id"), r.get("arm")) for r in rows] != EXPECTED_ORDER:
            errors.append(name + ":counterbalance")
        rec = [r for r in rows if r.get("arm") == "recovery"]
        coast = [r for r in rows if r.get("arm") == "coast"]
        rec_positive = sum(bool(r.get("map_exit") or r.get("kill_count_gain", 0) > 0) for r in rec)
        coast_positive = sum(bool(r.get("map_exit") or r.get("kill_count_gain", 0) > 0) for r in coast)
        status = out.get("comparative_status")
        if name == "coast_only_kill_recovery_survives":
            if (rec_positive, coast_positive, status) != (0, 3, "PASS_DIRECTIONAL_FIXTURE_SCOPED"):
                errors.append(name + ":counterexample_outcome")
            if out.get("progress_pair_signs") != [1, 1, 1] or out.get("exposure_pair_signs") != [-1, -1, -1]:
                errors.append(name + ":pair_directions")
        elif name == "both_arms_kill_recovery_survives":
            if (rec_positive, coast_positive, status) != (3, 3, "PASS_DIRECTIONAL_FIXTURE_SCOPED"):
                errors.append(name + ":positive_control")
        elif name == "no_positive_effect":
            if status != "HOLD_NOT_EVALUATED": errors.append(name + ":hold_control")
        elif name == "no_threat_contact":
            if status != "HOLD_NOT_EVALUATED": errors.append(name + ":hold_control")
        elif name == "overlapping_exposure":
            if status == "PASS_DIRECTIONAL_FIXTURE_SCOPED": errors.append(name + ":overlap_passed")
    return errors

raw = json.loads((HERE / "RAW.json").read_text(encoding="utf-8"))
errors = audit(raw)
mutations = {}
for name, mutate in {
    "drop_case": lambda d: d["cases"].pop("no_threat_contact"),
    "forge_pass": lambda d: d["cases"]["no_positive_effect"]["adjudication"].update(comparative_status="PASS_DIRECTIONAL_FIXTURE_SCOPED"),
    "forge_recovery_effect": lambda d: d["cases"]["coast_only_kill_recovery_survives"]["input"][0].update(kill_count_gain=1),
}.items():
    probe = copy.deepcopy(raw); mutate(probe); mutations[name] = audit(probe)
if any(not value for value in mutations.values()): errors.append("mutation_not_rejected")
result = {"schema": "r133-useful-effect-audit-result-v2",
          "status": "COUNTEREXAMPLE_SCOPED" if not errors else "FAIL_AUDIT",
          "errors": errors, "mutation_errors": mutations,
          "scope": "synthetic decision-rule construction only; not empirical task-effect evidence"}
(HERE / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
