"""Post-hoc reconciliation of action-health validity rejections in A14.

This addendum deliberately does not alter the frozen A14 audit or result.
It reads the retained private episode report and emits only deduplicated,
aggregate decision evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a14-recovery-20261009"
RAW_REPORT = REPO / "results-local/doom" / ALLOC / "episode/report.json"
OUT = HERE / "A14_RECONCILIATION_V2.json"


def collect_action_health_rejections(report: dict) -> list[dict]:
    """Return unique rejected action fingerprints; reject conflicting duplicates."""
    unique: dict[str, dict] = {}

    def contains_fingerprint(value, fingerprint):
        if isinstance(value, dict):
            contract = value.get("contract") or {}
            if contract.get("action_fingerprint") == fingerprint:
                return True
            return any(contains_fingerprint(child, fingerprint) for child in value.values())
        if isinstance(value, list):
            return any(contains_fingerprint(child, fingerprint) for child in value)
        return False

    def walk(value, iteration, decision):
        if isinstance(value, dict):
            if value.get("reason") == "health_max_decrease_from_source_failed":
                contract = value.get("contract") or {}
                snapshot = value.get("snapshot") or {}
                source_health = (contract.get("source") or {}).get("signals", {}).get("health", {}).get("value")
                fresh_health = snapshot.get("signals", {}).get("health", {}).get("value")
                checks = [check for check in value.get("checks", [])
                          if check.get("signal_id") == "health" and
                          check.get("operator") == "max_decrease_from_source"]
                expected = checks[0].get("expected") if len(checks) == 1 else None
                fingerprint = contract.get("action_fingerprint")
                if (value.get("status") != "REJECTED_PREDICATE" or
                        not isinstance(fingerprint, str) or
                        type(source_health) is not int or type(fresh_health) is not int or
                        type(expected) is not int or fresh_health > source_health - expected):
                    raise ValueError("malformed or non-rejecting health predicate receipt")
                row = {
                    "decision_iteration": iteration,
                    "action_fingerprint": fingerprint,
                    "rejection_sequence": snapshot.get("sequence"),
                    "source_health": source_health,
                    "fresh_health": fresh_health,
                    "maximum_allowed_decrease": expected,
                    "action_admissible": False,
                    "requires_new_decision": value.get("requires_new_decision") is True,
                }
                running_guard = decision.get("running_action_guard") or {}
                if contains_fingerprint(running_guard.get("invalidation"), fingerprint):
                    row["outcome"] = "revoked_after_executor_acceptance"
                elif contains_fingerprint((decision.get("final_action_admission") or {}).get("action_validity"), fingerprint):
                    row["outcome"] = "rejected_before_executor_admission"
                else:
                    raise ValueError("rejection receipt has no matching action outcome")
                previous = unique.get(fingerprint)
                if previous is not None and previous != row:
                    raise ValueError("conflicting duplicate action-health receipts")
                unique[fingerprint] = row
            for child in value.values():
                walk(child, iteration, decision)
        elif isinstance(value, list):
            for child in value:
                walk(child, iteration, decision)

    decisions = report.get("decisions", [])
    for decision in decisions:
        iteration = decision.get("iteration")
        if type(iteration) is not int:
            raise ValueError("decision iteration missing")
        walk(decision, iteration, decision)
    rows = sorted(unique.values(), key=lambda row: row["decision_iteration"])
    for row in rows:
        followups = [decision for decision in decisions
                     if type(decision.get("iteration")) is int and
                     row["decision_iteration"] < decision["iteration"] <= row["decision_iteration"] + 2 and
                     type(decision.get("fresh_sequence_at_plan")) is int and
                     type(row["rejection_sequence"]) is int and
                     decision["fresh_sequence_at_plan"] > row["rejection_sequence"] and
                     decision.get("model_action_discarded") is not True and
                     (decision.get("final_action_admission") or {}).get("status") == "INPUT_ADMITTED"]
        row["fresh_admitted_followup_iterations_within_two"] = [
            decision["iteration"] for decision in followups]
        row["fresh_admitted_followup_within_two"] = bool(followups)
    return rows


def build(report: dict, report_sha256: str) -> dict:
    rows = collect_action_health_rejections(report)
    return {
        "schema": "map01-v39-live-threat-guard-a14-reconciliation-v2",
        "allocation": ALLOC,
        "disposition": "ADDENDUM; original A14 HOLD and initial audit FAIL remain unchanged",
        "source_report_sha256": report_sha256,
        "original_frozen_interpretation": {
            "hard_health_guard_count": 0,
            "recovery_question": "not exercised",
            "trigger_definition": (
                "audit_recovery_censoring.is_hard_health_guard accepts only "
                "policy_invalidation reason health:below_hard_minimum or an "
                "outcomes.health HARD_INVALIDATED/below_hard_minimum receipt"
            ),
            "preserved_artifacts": [
                {"path": "AUDIT.json", "sha256": "6dc3b232c8cfca0709c5337a8fd9d2fa609ccf985f2f83201ac4ece4e010a1bc", "status": "FAIL"},
                {"path": "A14_RESULT.json", "sha256": "9620785873143629ee92b0f234cbbcafd56d302040ac1546a7470e9e3a0d3b7f", "status": "HOLD"},
                {"path": "A14_RECOVERY_CENSORING.json", "sha256": "4dae23f0c9b4cdbbc7b5ba82b5d2855e8944d441aaa002132db0dfdc184fd14f", "hard_health_guard_count": 0},
                {"path": "A14_RESULT_PUBLIC.json", "sha256": "2c0064255ea5339c50ac3414c29f445b763bfc5480f6cbc17d10732f712e5ffe", "status": "HOLD"},
                {"path": "A14_RESULT.md", "sha256": "d57b7418e222bde8d34325b9edeefa26e8d54f02af17411e8695b200515ad837", "status": "HOLD"},
            ],
        },
        "additional_action_validity_evidence": {
            "distinct_rejected_action_count": len(rows),
            "deduplication_key": "contract.action_fingerprint",
            "deduplicated_actions": rows,
            "interpretation": (
                "These are action-validity max-decrease predicate rejections, "
                "not the preregistered policy hard-minimum recovery trigger. "
                "One action was revoked after executor acceptance; a second "
                "was rejected before executor admission. Both crossed their "
                "authored health decrease bound. Each was followed by an "
                "admitted plan on a fresh observation within two later decisions; "
                "this is post-hoc and not the preregistered recovery endpoint."
            ),
        },
        "scope": "Post-hoc reconciliation only; no replay, retry, or change to frozen audit outputs.",
    }


def main() -> int:
    raw = RAW_REPORT.read_bytes()
    result = build(json.loads(raw), hashlib.sha256(raw).hexdigest())
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
