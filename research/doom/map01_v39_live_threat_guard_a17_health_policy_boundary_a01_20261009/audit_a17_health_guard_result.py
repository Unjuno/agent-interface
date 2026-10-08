"""Reconcile A17 frozen policy-guard result and emit an aggregate-only summary."""
from __future__ import annotations

import json
from pathlib import Path

from audit_recovery_censoring import analyze

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a17-health-policy-boundary-20261009"
ROOT = REPO / "results-local/doom" / ALLOC
PROVENANCE = (
    "allocation_identity", "source_commit_is_verified_prelaunch_main",
    "runtime_source_closure_is_complete_and_frozen",
    "all_runtime_sources_match_local_and_frozen_main",
    "guest_host_source_mapping_is_frozen", "known_startup_dependencies_are_frozen",
    "no_preexisting_game_or_display_process", "runner_and_auditor_hashes_match_freeze",
    "fixture_hashes_match_freeze", "qualified_wad_hash_matches",
    "forwarded_images_host_receipts_valid",
)
SAFETY = (
    "all_accepted_programs_have_terminals", "per_key_release_rows_accounted",
    "terminal_releases_verified_empty", "no_stale_admission_after_guard",
)


def classify(audit, custody, censor):
    checks = audit.get("checks", {})
    provenance = all(checks.get(key) is True for key in PROVENANCE)
    safety = all(checks.get(key) is True for key in SAFETY)
    custody_ok = custody.get("custody_pass") is True
    counts = censor["classifications"]
    if not provenance or not safety or not custody_ok:
        status = "FAIL"
    elif audit.get("controller_failure") is not None:
        status = "STOP"
    elif (censor["hard_health_guard_count"] > 0 and
          counts["recovered_within_two_decisions"] > 0 and
          counts["observable_recovery_missed"] == 0):
        status = "PASS"
    else:
        status = "HOLD"
    return status, provenance, safety, custody_ok


def collect_action_health_rejections(report):
    """Deduplicate repeated report copies by action fingerprint."""
    unique = {}

    def contains_fingerprint(value, fingerprint):
        if isinstance(value, dict):
            if (value.get("contract") or {}).get("action_fingerprint") == fingerprint:
                return True
            return any(contains_fingerprint(child, fingerprint) for child in value.values())
        if isinstance(value, list):
            return any(contains_fingerprint(child, fingerprint) for child in value)
        return False

    def walk(value, iteration, decision):
        if isinstance(value, dict):
            if value.get("reason") == "health_max_decrease_from_source_failed":
                contract = value.get("contract") or {}
                source = (contract.get("source") or {}).get("signals", {}).get("health", {}).get("value")
                snapshot = value.get("snapshot") or {}
                fresh = snapshot.get("signals", {}).get("health", {}).get("value")
                checks = [item for item in value.get("checks", [])
                          if item.get("signal_id") == "health" and
                          item.get("operator") == "max_decrease_from_source"]
                fingerprint = contract.get("action_fingerprint")
                if (value.get("status") != "REJECTED_PREDICATE" or
                        not isinstance(fingerprint, str) or
                        type(source) is not int or type(fresh) is not int or
                        len(checks) != 1 or type(checks[0].get("expected")) is not int or
                        fresh > source - checks[0]["expected"]):
                    raise ValueError("malformed health action rejection")
                row = {"decision_iteration": iteration,
                       "action_fingerprint": fingerprint,
                       "source_health": source,
                       "fresh_health": fresh,
                       "maximum_allowed_decrease": checks[0]["expected"]}
                guard = decision.get("running_action_guard") or {}
                if contains_fingerprint(guard.get("invalidation"), fingerprint):
                    row["outcome"] = "revoked_after_executor_acceptance"
                elif contains_fingerprint((decision.get("final_action_admission") or {}).get("action_validity"), fingerprint):
                    row["outcome"] = "rejected_before_executor_admission"
                else:
                    raise ValueError("health rejection has no matching action outcome")
                if fingerprint in unique and unique[fingerprint] != row:
                    raise ValueError("conflicting duplicate health action receipt")
                unique[fingerprint] = row
            for child in value.values():
                walk(child, iteration, decision)
        elif isinstance(value, list):
            for child in value:
                walk(child, iteration, decision)

    for decision in report.get("decisions", []):
        iteration = decision.get("iteration")
        if type(iteration) is not int:
            raise ValueError("decision iteration missing")
        walk(decision, iteration, decision)
    return sorted(unique.values(), key=lambda row: row["decision_iteration"])


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    audit = json.loads((ROOT / "AUDIT.json").read_text())
    custody = json.loads((ROOT / "A17_CUSTODY_INDEPENDENT.json").read_text())
    report = json.loads((ROOT / "episode/report.json").read_text())
    host = json.loads((ROOT / "HOST.json").read_text())
    censor = analyze(report.get("decisions", []), freeze["runtime"]["iterations"])
    (ROOT / "A17_RECOVERY_CENSORING.json").write_text(json.dumps({
        "schema": "map01-v39-live-threat-guard-a17-health-guard-boundary-censoring-v1",
        "allocation": ALLOC, **censor,
    }, indent=2) + "\n")
    status, provenance, safety, custody_ok = classify(audit, custody, censor)
    action_rejections = collect_action_health_rejections(report)

    result = {
        "schema": "map01-v39-live-threat-guard-a17-health-guard-boundary-result-v1",
        "allocation": ALLOC,
        "status": status,
        "initial_audit_status_preserved": audit.get("status"),
        "provenance_checks_passed": provenance,
        "input_safety_checks_passed": safety,
        "independent_cancellation_custody_passed": custody_ok,
        "hard_health_guard_count": censor["hard_health_guard_count"],
        "distinct_action_health_predicate_rejections": len(action_rejections),
        "action_health_predicate_rejections": action_rejections,
        "recovery_classifications": censor["classifications"],
        "scope": (
            "One descriptive live boundary-exposure episode. PASS is limited to "
            "a fresh recovery within two decisions after a qualifying authored-cover "
            "hard-health policy guard with no observed miss. No guard means HOLD/unexposed; "
            "it does not establish monitor failure, useful feedback, causal benefit, "
            "MAP01 completion, hardware key state, or game consumption."
        ),
    }
    (ROOT / "A17_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")

    typed = [row for row in audit.get("health_values", []) if type(row) is int]
    ammo = [row for row in audit.get("ammo_values", []) if type(row) is int]
    counts = audit.get("counts", {})
    public = {
        "schema": "map01-v39-live-threat-guard-a17-health-guard-boundary-public-v1",
        "allocation": ALLOC,
        "issue": 59,
        "status": status,
        "source_main_sha": freeze.get("source_commit"),
        "experiment_tree_commit": freeze.get("experiment_tree_commit"),
        "fixture_seed": freeze.get("fixture_seed"),
        "model": freeze.get("runtime", {}).get("model"),
        "effort": freeze.get("runtime", {}).get("effort"),
        "runtime": {
            "vm": freeze.get("runtime", {}).get("vm"),
            "decisions_cap": freeze.get("runtime", {}).get("iterations"),
            "decisions_started": counts.get("model_turns_started"),
            "decisions_completed": counts.get("model_turns_completed"),
            "guest_exit": host.get("guest_exit"),
            "app_server_exit": host.get("app_server_exit"),
            "elapsed_seconds": host.get("elapsed_seconds"),
            "retry_count": host.get("retry_count"),
        },
        "episode": {
            "hard_health_guards": censor["hard_health_guard_count"],
            "distinct_action_health_predicate_rejections": len(action_rejections),
            "health_min": min(typed) if typed else None,
            "health_max": max(typed) if typed else None,
            "ammo_min": min(ammo) if ammo else None,
            "ammo_max": max(ammo) if ammo else None,
            "useful_events_during_model_wait": counts.get("useful_events_during_model_wait"),
            "kills": (audit.get("score") or {}).get("kill_count"),
            "deaths": (audit.get("score") or {}).get("death_count"),
            "map_exit": (audit.get("score") or {}).get("map_exit"),
            "episode_finished": (audit.get("score") or {}).get("episode_finished"),
        },
        "input_custody": {
            "independent_audit_pass": custody_ok,
            "unaccounted_cancellations": custody.get("unaccounted_cancellations"),
            "per_key_release_transitions": custody.get("per_key_release_transitions"),
            "verified_empty_terminals": custody.get("terminals_with_verified_empty_release"),
            "physical_key_state_claim": False,
        },
        "recovery": censor["classifications"],
        "scope": result["scope"],
    }
    (ROOT / "A17_RESULT_PUBLIC.json").write_text(json.dumps(public, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(json.dumps(public, indent=2))
    return 0 if status in ("PASS", "HOLD") else 1


if __name__ == "__main__":
    raise SystemExit(main())
