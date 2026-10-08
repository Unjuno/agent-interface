"""Independent raw-only policy/result audit for Issue #6680."""

import json
import sys
from pathlib import Path


def expected_rows(fixture, oracle):
    result = []
    for case in fixture["cases"]:
        truth = oracle["hidden_worlds"][case["id"]]
        for policy in fixture["policies"]:
            observations = 0
            if policy == "always_reobserve":
                action, observations = "reobserve", 1
            elif policy == "always_reset":
                action = "reset"
            elif policy == "immediate_yield":
                action = "yield"
            elif policy == "bounded_diagnose":
                probe = fixture["probe"]
                observed = case["observed"]
                if case["probe_admissible"] and probe["admissible"] and not probe["effectful"] and not probe["lease_extension"]:
                    observations = 1
                    compatible = [h for h, outputs in probe["response_sets"].items() if observed in outputs]
                    if len(compatible) == 1 and observed != "unsupported":
                        action = {"H_OBSERVATION": "reobserve", "H_DYNAMICS": "reset"}.get(compatible[0], "yield")
                    else:
                        action = "yield"
                else:
                    action = "yield"
            else:
                raise ValueError(f"unknown policy {policy}")
            correct = truth["correct_recovery"]
            result.append({
                "case_id": case["id"],
                "policy": policy,
                "action": action,
                "diagnostic_observations": observations,
                "release_tick": oracle["safety"]["required_release_tick"],
                "wrong_recovery": action in ("reobserve", "reset") and action != correct,
                "repeated_residual": action in ("reobserve", "reset") and action != correct,
                "useful_effect": action == correct and truth["effect_recoverable"],
                "forbidden_transition": (
                    action not in ("reobserve", "reset", "yield")
                    or observations > fixture["max_diagnostic_observations"]
                    or policy == "bounded_diagnose" and observations > 0
                    and (not case["probe_admissible"] or not probe["admissible"] or probe["effectful"] or probe["lease_extension"])
                ),
            })
    return result


def audit(raw, fixture, oracle):
    got = raw.get("rows")
    want = expected_rows(fixture, oracle)
    errors = []
    if raw.get("schema") != "safe-discriminating-observation-6680-raw-v1":
        errors.append("raw schema mismatch")
    if got != [{k: row[k] for k in ("case_id", "policy", "action", "diagnostic_observations", "release_tick", "forbidden_transition")} for row in want]:
        errors.append("raw rows do not match independently reconstructed policy actions")
    if len(got or []) != len(fixture["cases"]) * len(fixture["policies"]):
        errors.append("row coverage mismatch")
    # Oracle-backed gates are audited from the independent reconstruction.
    for row in want:
        if row["release_tick"] > oracle["safety"]["required_release_tick"]:
            errors.append("release tick violated")
        if row["forbidden_transition"]:
            errors.append("forbidden transition")
    identifiable = {"c01", "c02"}
    diagnostic = [r for r in want if r["policy"] == "bounded_diagnose" and r["case_id"] in identifiable]
    fixed = {p: [r for r in want if r["policy"] == p and r["case_id"] in identifiable] for p in ("always_reobserve", "always_reset")}
    if any(r["action"] != oracle["hidden_worlds"][r["case_id"]]["correct_recovery"] for r in diagnostic):
        errors.append("diagnostic policy failed an identifiable world")
    if not all(sum(r["wrong_recovery"] for r in diagnostic) < sum(r["wrong_recovery"] for r in rows) for rows in fixed.values()):
        errors.append("diagnosis did not strictly reduce wrong recovery against both fixed arms")
    if any(r["action"] != "yield" for r in want if r["policy"] == "bounded_diagnose" and r["case_id"] in {"c03", "c04", "c05"}):
        errors.append("diagnosis acted on non-identifiable, ineligible, or unsupported evidence")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(want), "errors": errors}


if __name__ == "__main__":
    base = Path(__file__).parent
    raw = json.loads(Path(sys.argv[1]).read_text())
    result = audit(raw, json.loads((base / "fixture.json").read_text()), json.loads((base / "oracle.json").read_text()))
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
