"""Deterministic finite-state construction for Issue #5960; no runtime I/O."""
import hashlib
import json

POLICIES = ("IMMEDIATE_RECOVER", "PRE_RECOVERY_MINIMAL_CAPTURE", "CAPTURE_EVERYTHING")
SCENARIOS = ("cause_a", "cause_b", "null_cause", "hazard_held", "zero_slack",
             "privacy_forbidden", "stale_source", "lost_receipt", "observer_perturbation")


def run():
    rows = []
    for seed in range(32):
        for scenario in SCENARIOS:
            for policy in POLICIES:
                cause = {"cause_a": "A", "cause_b": "B", "null_cause": "C"}.get(scenario)
                signal = {"cause_a": "transient_focus_loss", "cause_b": "transient_modal_race",
                          "null_cause": None}.get(scenario)
                hazard = scenario == "hazard_held"
                privacy = scenario == "privacy_forbidden"
                zero_slack = scenario == "zero_slack"
                stale = scenario == "stale_source"
                lost = scenario == "lost_receipt"
                perturbs = scenario == "observer_perturbation"
                source = f"src-{seed}-{scenario}"
                snap = None
                events = []
                # Mandatory safety/deadline/privacy gates precede all capture attempts.
                if hazard or zero_slack or privacy:
                    events.append("safe_release_or_stop")
                    disposition = "SNAPSHOT_SKIPPED_SAFETY"
                elif stale:
                    events.append("recover")
                    disposition = "HOLD_STALE_SOURCE"
                elif lost:
                    events.append("recover")
                    disposition = "HOLD_RECEIPT_MISSING"
                elif perturbs:
                    events.append("recover")
                    disposition = "HOLD_OBSERVER_PERTURBATION"
                elif policy == "IMMEDIATE_RECOVER":
                    events.append("recover")
                    disposition = "NO_SNAPSHOT"
                elif policy == "PRE_RECOVERY_MINIMAL_CAPTURE":
                    snap = {"failure_id": f"failure-{seed}-{scenario}", "source_id": source,
                            "receipt_id": f"receipt-{seed}-{scenario}", "signal": signal,
                            "authority": False}
                    events.extend(("capture_minimal", "recover"))
                    disposition = "CAPTURED_MINIMAL"
                else:
                    snap = {"failure_id": f"failure-{seed}-{scenario}", "source_id": source,
                            "receipt_id": f"receipt-{seed}-{scenario}", "signal": signal,
                            "private_payload": "FORBIDDEN_SYNTHETIC_SECRET", "authority": False}
                    events.extend(("capture_everything", "recover"))
                    disposition = "CAPTURED_OVERBROAD"
                capture_cost = 1 if policy == "PRE_RECOVERY_MINIMAL_CAPTURE" and snap else (9 if policy == "CAPTURE_EVERYTHING" and snap else 0)
                slack_budget = 2
                # Recovery erases transient evidence. Stale/lost/perturbed cases cannot promote it.
                observed = snap.get("signal") if snap and snap.get("source_id") == source else None
                diagnosis = observed if cause and observed else None
                rows.append({"seed": seed, "scenario": scenario, "cause": cause, "policy": policy,
                             "source_id": source, "hazard": hazard, "privacy_forbidden": privacy,
                             "zero_slack": zero_slack, "slack_budget": slack_budget,
                             "capture_cost": capture_cost, "deadline_missed": capture_cost > slack_budget,
                             "stale_source": stale,
                             "receipt_missing": lost, "observer_perturbs": perturbs,
                             "events": events, "disposition": disposition, "snapshot": snap,
                             "post_recovery_signal": None, "diagnosis_signal": diagnosis,
                             "recovery_completed": "recover" in events,
                             "input_released_before_capture": "safe_release_or_stop" in events})
    return {"schema": "issue5960-presnapshot-t0-v1", "status": "CANDIDATE_COMPLETE",
            "rows": rows}


def canonical_sha(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
