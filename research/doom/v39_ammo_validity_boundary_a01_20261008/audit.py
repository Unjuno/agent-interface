"""Independent arithmetic/source auditor for the V39 ammo boundary result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def validate(result):
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
            raise ValueError(f"frozen source mismatch: {name}")
    expected_top = {"schema": "issue59-v39-ammo-validity-boundary-result-v1",
                    "status": "CONSTRUCTION_OBSERVATION", "main_commit": FREEZE["main_commit"],
                    "source_ammo": 50, "source_health": 100,
                    "critical_health_minimum": 80, "maximum_health_loss": 12,
                    "scope": "Synthetic paired typed-HUD monitor behavior only; no live or tactical efficacy claim."}
    if set(result) != set(expected_top) | {"rows"}:
        raise ValueError("top-level result fields differ")
    for key, value in expected_top.items():
        if result.get(key) != value:
            raise ValueError(f"result field mismatch: {key}")
    if len(result["rows"]) != 3:
        raise ValueError("expected three sequential ammo observations")
    expected = [
        {"sequence": 2, "health": 100, "ammo": 39, "health_hard_minimum": 88,
         "ammo_hard_minimum": 1, "disposition": "soft_change", "invalidation_reason": None,
         "soft_event_count": 1,
         "latest_soft_event": {"signal_id": "ammo", "value": 39, "status": "SOFT_CHANGED",
                               "reason": "within_validity_envelope"},
         "requires_new_decision": False, "grants_input_authority": False},
        {"sequence": 3, "health": 100, "ammo": 1, "health_hard_minimum": 88,
         "ammo_hard_minimum": 1, "disposition": "soft_change", "invalidation_reason": None,
         "soft_event_count": 2,
         "latest_soft_event": {"signal_id": "ammo", "value": 1, "status": "SOFT_CHANGED",
                               "reason": "within_validity_envelope"},
         "requires_new_decision": False, "grants_input_authority": False},
        {"sequence": 4, "health": 100, "ammo": 0, "health_hard_minimum": 88,
         "ammo_hard_minimum": 1, "disposition": "hard_invalidation",
         "invalidation_reason": "ammo:below_hard_minimum", "soft_event_count": 2,
         "latest_soft_event": {"signal_id": "ammo", "value": 1, "status": "SOFT_CHANGED",
                               "reason": "within_validity_envelope"},
         "requires_new_decision": True, "grants_input_authority": False},
    ]
    if result["rows"] != expected:
        raise ValueError("sequential ammo soft/hard boundary mismatch")
    return True


def main():
    result_path = HERE / "RESULT.json"
    output_path = HERE / "AUDIT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    validate(result)
    if output_path.exists():
        raise SystemExit(f"refusing to overwrite {output_path}")
    audit = {"schema": "issue59-v39-ammo-validity-boundary-audit-v1",
             "status": "PASS_CONSTRUCTION_BOUNDARY",
             "checks": {"frozen_source_and_triage_identities": True,
                        "large_ammo_drop_is_soft": True,
                        "positive_floor_is_soft": True,
                        "zero_ammo_invalidates": True,
                        "health_remains_above_authored_floor": True,
                        "soft_event_history_is_retained": True,
                        "no_input_authority_granted": True},
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}
    output_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
