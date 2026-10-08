"""Independent arithmetic/provenance audit for the retained boundary result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def validate(result):
    for label in ("controller", "guard", "motivating_evidence"):
        spec = FREEZE[label]
        data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if len(data) == 0 or hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
            raise ValueError(f"frozen source mismatch: {label}")
    expected_top = {"schema": "issue59-authored-health-loss-boundary-result-v1",
                    "status": "CONSTRUCTION_OBSERVATION",
                    "main_commit": FREEZE["main_commit"],
                    "controller_sha256": FREEZE["controller"]["sha256"],
                    "guard_sha256": FREEZE["guard"]["sha256"],
                    "motivating_triage_sha256": FREEZE["motivating_evidence"]["sha256"],
                    "pending_model": True, "synthetic_typed_health_source": 100,
                    "critical_health_minimum": 80, "maximum_health_loss_values": [0, 20],
                    "scope": "Current-source construction boundary only; no live threat, timing, input, recovery, or task-effect evidence."}
    for key, value in expected_top.items():
        if result.get(key) != value:
            raise ValueError(f"top-level mismatch: {key}")
    if set(result) != set(expected_top) | {"rows"}:
        raise ValueError("unexpected or missing result fields")
    if len(result["rows"]) != 21:
        raise ValueError("expected exhaustive 0..20 loss sweep")
    for loss, row in enumerate(result["rows"]):
        floor = max(80, 100 - loss)
        if row.get("maximum_health_loss") != loss or row.get("hard_minimum") != floor:
            raise ValueError(f"sweep identity mismatch at loss={loss}")
        for label, value in (("triage_value_84", 84), ("exact_floor", floor),
                             ("one_below_floor", floor - 1)):
            got = row.get(label)
            expected_status = ("HARD_INVALIDATED" if value < floor else
                               "UNCHANGED" if value == 100 else "SOFT_CHANGED")
            expected_reason = {"HARD_INVALIDATED": "below_hard_minimum",
                               "UNCHANGED": "signal_unchanged",
                               "SOFT_CHANGED": "within_validity_envelope"}[expected_status]
            if got != {"health": value, "status": expected_status, "reason": expected_reason,
                      "requires_new_decision": expected_status == "HARD_INVALIDATED",
                      "grants_input_authority": False, "hard_minimum": floor}:
                raise ValueError(f"boundary mismatch at loss={loss} point={label}")
    return True


def main():
    result_path = HERE / "RESULT.json"
    output_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validate(result)
    if output_path.exists():
        raise SystemExit(f"refusing to overwrite {output_path}")
    audit = {"schema": "issue59-authored-health-loss-boundary-audit-v1",
             "status": "PASS_CONSTRUCTION_BOUNDARY",
             "checks": {"frozen_source_and_triage_identities": True,
                        "all_21_authored_loss_settings_reconstructed": True,
                        "strict_floor_and_below_floor_boundaries": True,
                        "triage_100_to_84_threshold_classified": True,
                        "no_input_authority_granted": True,
                        "scope_limited_to_synthetic_construction": True},
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}
    output_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
