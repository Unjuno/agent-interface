#!/usr/bin/env python3
"""Independent raw-only checks for the frozen case deck and critical counterexample."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def audit(raw):
    errors = []
    expected = {"coast_only_kill_recovery_survives", "both_arms_kill_recovery_survives",
                "no_positive_effect", "no_threat_contact", "overlapping_exposure"}
    cases = raw.get("cases") if isinstance(raw, dict) else None
    if not isinstance(cases, dict) or set(cases) != expected:
        return ["case_inventory"]
    for name, item in cases.items():
        rows = item.get("input")
        out = item.get("adjudication")
        if not isinstance(rows, list) or len(rows) != 6 or not isinstance(out, dict):
            errors.append(name + ":shape")
            continue
        recovery = [r for r in rows if r.get("arm") == "recovery"]
        coast = [r for r in rows if r.get("arm") == "coast"]
        rec_effect = sum(bool(r.get("map_exit") or r.get("kill_count_gain", 0) > 0) for r in recovery)
        coast_effect = sum(bool(r.get("map_exit") or r.get("kill_count_gain", 0) > 0) for r in coast)
        both_threat = all(
            next(r for r in recovery if r["pair_id"] == p)["threat_contact_confirmed"] and
            next(r for r in coast if r["pair_id"] == p)["threat_contact_confirmed"]
            for p in (1, 2, 3))
        if name == "coast_only_kill_recovery_survives":
            if rec_effect != 0 or coast_effect != 3 or not both_threat:
                errors.append(name + ":fixture_semantics")
            if out.get("comparative_status") != "PASS_DIRECTIONAL_FIXTURE_SCOPED":
                errors.append(name + ":expected_pass")
            if out.get("progress_pair_signs") != [1, 1, 1] or out.get("exposure_pair_signs") != [-1, -1, -1]:
                errors.append(name + ":directional_signs")
        elif name == "both_arms_kill_recovery_survives":
            if rec_effect != 3 or out.get("comparative_status") != "PASS_DIRECTIONAL_FIXTURE_SCOPED":
                errors.append(name + ":positive_control")
        elif name in ("no_positive_effect", "no_threat_contact"):
            if out.get("comparative_status") != "HOLD_NOT_EVALUATED":
                errors.append(name + ":hold_control")
        elif name == "overlapping_exposure":
            if out.get("comparative_status") == "PASS_DIRECTIONAL_FIXTURE_SCOPED":
                errors.append(name + ":overlap_must_not_pass")
    return errors

raw = json.loads((HERE / "RAW.json").read_text(encoding="utf-8"))
errors = audit(raw)
mutations = {}
for name, mutate in {
    "drop_case": lambda d: d["cases"].pop("no_threat_contact"),
    "forge_pass": lambda d: d["cases"]["no_positive_effect"]["adjudication"].update(comparative_status="PASS_DIRECTIONAL_FIXTURE_SCOPED"),
    "forge_recovery_effect": lambda d: d["cases"]["coast_only_kill_recovery_survives"]["input"][0].update(kill_count_gain=1),
}.items():
    probe = copy.deepcopy(raw)
    mutate(probe)
    mutations[name] = audit(probe)
if any(not value for value in mutations.values()):
    errors.append("mutation_not_rejected")
result = {"schema": "r133-useful-effect-audit-result-v1",
          "status": "COUNTEREXAMPLE_SCOPED" if not errors else "FAIL_AUDIT",
          "errors": errors, "mutation_errors": mutations,
          "counterexample": {"recovery_positive_pairs": 0, "coast_positive_pairs": 3,
                             "adjudication": raw["cases"]["coast_only_kill_recovery_survives"]["adjudication"]["comparative_status"]}}
(HERE / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
