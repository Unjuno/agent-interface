#!/usr/bin/env python3
"""Apply the frozen v2 adjudicator to the preregistered synthetic deck."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "research/doom/map01_r133_recovery_coast_t1_v1/decision_rule_construction_v2/adjudicator.py"
spec = importlib.util.spec_from_file_location("frozen_adjudicator", SOURCE)
adjudicator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adjudicator)

def rows(case):
    result = []
    for pair in (1, 2, 3):
        for order, arm in enumerate(("recovery", "coast"), start=1):
            recovery = arm == "recovery"
            no_effect = case == "no_positive_effect"
            rec_zero = case == "coast_only_kill_recovery_survives"
            threat = case != "no_threat_contact"
            rec_alive = recovery
            if case == "both_arms_kill_recovery_survives":
                kill = 1
            elif no_effect:
                kill = 0
            else:
                kill = 0 if recovery else 1
            if case == "overlapping_exposure":
                unsafe_lower, unsafe_upper = (0, 20) if recovery else (10, 30)
            else:
                unsafe_lower, unsafe_upper = (0, 5) if recovery else (20, 30)
            result.append({
                "session_id": f"{case}-{pair}-{arm}",
                "session_order": (pair - 1) * 2 + order,
                "pair_id": pair,
                "arm": arm,
                "fixture_sha256": "1" * 64,
                "source_bundle_sha256": "2" * 64,
                "model_contract_sha256": "3" * 64,
                "seed": 992600,
                "map": "map01-threat-contact-v2",
                "skill": 1,
                "start_fingerprint": f"start-{pair}",
                "ready_ns": 1000000,
                "horizon_ms": 60000,
                "threat_contact_confirmed": threat,
                "map_exit": False,
                "alive_at_horizon": rec_alive if recovery else False,
                "kill_count_gain": kill,
                "death_count_gain": 0 if recovery else 1,
                "health_loss": 2 if recovery else 20,
                "ammo_spent": 0 if no_effect or rec_zero and recovery else 1,
                "unsafe_lower_ms": unsafe_lower,
                "unsafe_upper_ms": unsafe_upper,
                "terminal_neutral": True,
                "stale_action_after_invalidation": False,
                "complete": True,
                "audit_error_count": 0,
            })
    return result

raw = {"schema": "r133-useful-effect-audit-raw-v1", "cases": {}}
for case in ("coast_only_kill_recovery_survives", "both_arms_kill_recovery_survives",
             "no_positive_effect", "no_threat_contact", "overlapping_exposure"):
    case_rows = rows(case)
    raw["cases"][case] = {"input": case_rows, "adjudication": adjudicator.adjudicate(case_rows)}
(HERE / "RAW.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "CANDIDATE_COMPLETE", "case_count": len(raw["cases"])}, sort_keys=True))
