#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #8668 T0 A03; no candidate imports."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_ID = "PHASE-CONTROL-DELAYS-8668-T0-A03-20261009"
BASE = "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385"
POST_EMIT = ("EMITTED", "CONSUMED")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def design_from_freeze() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze["allocation"] != RUN_ID or freeze["base_commit"] != BASE:
        raise ValueError("freeze identity/base mismatch")
    for name, expected in freeze["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"frozen source mismatch: {name}")
    return json.loads((ROOT / "design.json").read_text())


def expected_schedules(d: dict) -> list[dict]:
    rows: list[dict] = []
    for phase in d["phases"]:
        effects = d["post_emit_effect_states"] if phase in POST_EMIT else [False]
        for committed, (name, timeline), retry, release in itertools.product(
            effects,
            d["receipt_timelines"].items(),
            d["retry_requested"],
            d["neutral_release_observed"],
        ):
            if not consistent(phase, committed, timeline):
                continue
            receipts = []
            next_sequence: dict[tuple[str, int], int] = {}
            for pos, (owner, kind) in enumerate(timeline, start=1):
                if owner == "prior":
                    operation_id, attempt = d["prior_operation_id"], 1
                elif owner == "prior_reused":
                    operation_id, attempt = d["active_operation_id"], d["active_attempt"] - 1
                else:
                    operation_id, attempt = d["active_operation_id"], d["active_attempt"]
                identity = (operation_id, attempt)
                sequence = 1 if name.endswith("_replayed") else next_sequence.get(identity, 0) + 1
                next_sequence[identity] = sequence
                receipts.append({
                    "ack_id": f"ack-{operation_id}-attempt-{attempt}-{kind}-{sequence}",
                    "operation_id": operation_id,
                    "logical_action_id": d["active_logical_action"],
                    "attempt": attempt,
                    "kind": kind,
                    "asserted_phase": "CONSUMED" if kind == "EFFECT_CONFIRMED" else "QUEUED",
                    "sequence": sequence,
                    "arrival_order": pos,
                })
            rows.append({
                "phase": phase,
                "effect_committed": committed,
                "retry_requested": retry,
                "neutral_release_observed": release,
                "receipts": receipts,
                "timeline": name,
            })
    rows.append({
        "phase": None,
        "effect_committed": False,
        "retry_requested": False,
        "neutral_release_observed": False,
        "receipts": [],
        "timeline": "no_input_control",
    })
    return rows


def consistent(phase: str, committed: bool, timeline: list[list[str]]) -> bool:
    for owner, kind in timeline:
        if owner == "active" and kind == "EFFECT_CONFIRMED" and (phase not in POST_EMIT or not committed):
            return False
        if owner == "active" and kind == "CANCEL_CONFIRMED" and (phase not in POST_EMIT and committed):
            return False
    return True


def oracle(raw: dict, d: dict, *, identity: bool) -> dict:
    if raw["phase"] is None:
        return {"status": "NO_ACTION", "retry_admitted": False, "accepted_ack_ids": [], "ignored_stale": 0}
    status = "UNKNOWN" if raw["phase"] in POST_EMIT else "PENDING"
    accepted: list[str] = []
    ignored = 0
    seen: set[tuple[str, int, int]] = set()
    active_kinds: set[str] = set()
    for ack in sorted(raw["receipts"], key=lambda x: x["arrival_order"]):
        matches = (
            ack["operation_id"] == d["active_operation_id"]
            and ack["attempt"] == d["active_attempt"]
        )
        if identity and not matches:
            ignored += 1
            continue
        event_key = (ack["operation_id"], ack["attempt"], ack["sequence"])
        if event_key in seen:
            continue
        seen.add(event_key)
        if matches:
            active_kinds.add(ack["kind"])
            if len(active_kinds) > 1:
                status = "CONFLICT_UNKNOWN"
                accepted.clear()
                continue
        if status == "CONFLICT_UNKNOWN":
            continue
        if ack["kind"] == "EFFECT_CONFIRMED" and raw["phase"] in POST_EMIT:
            status = "COMPLETED"
            accepted.append(ack["ack_id"])
        elif ack["kind"] == "EFFECT_CONFIRMED" and matches:
            status = "CONFLICT_UNKNOWN"
        elif ack["kind"] == "CANCEL_CONFIRMED" and raw["phase"] not in POST_EMIT:
            status = "CANCELLED_BEFORE_EMIT"
            accepted.append(ack["ack_id"])
        elif ack["kind"] == "CANCEL_CONFIRMED" and matches:
            status = "UNKNOWN"
    retry = bool(raw["retry_requested"] and status == "CANCELLED_BEFORE_EMIT")
    return {"status": status, "retry_admitted": retry, "accepted_ack_ids": accepted, "ignored_stale": ignored}


def independently_safe_retry(raw: dict, d: dict) -> bool:
    if not raw["retry_requested"] or raw["phase"] is None or raw["phase"] in POST_EMIT:
        return False
    return any(
        ack["operation_id"] == d["active_operation_id"]
        and ack["attempt"] == d["active_attempt"]
        and ack["kind"] == "CANCEL_CONFIRMED"
        for ack in raw["receipts"]
    )


def audit(candidate: dict) -> dict:
    d = design_from_freeze()
    errors: list[str] = []
    expected = expected_schedules(d)
    rows = candidate.get("rows")
    if candidate.get("schema") != "8668-a03-raw-v1" or candidate.get("allocation") != RUN_ID or candidate.get("base_commit") != BASE:
        errors.append("raw_identity_mismatch")
    if not isinstance(rows, list) or candidate.get("row_count") != len(rows):
        errors.append("raw_row_count_mismatch")
        rows = rows if isinstance(rows, list) else []
    if len(rows) != len(expected):
        errors.append(f"schedule_coverage_mismatch:{len(rows)}!={len(expected)}")
    support = 0
    strict_false = strict_unsafe = latest_false = latest_unsafe = strict_false_cancel = neutral_release_aborts = conflict_gate_failures = 0
    for i, expected_schedule in enumerate(expected):
        if i >= len(rows):
            break
        row = rows[i]
        if row.get("schedule_id") != f"a03-{i:04d}":
            errors.append(f"schedule_id_mismatch:{i}")
        if row.get("exogenous") != expected_schedule:
            errors.append(f"schedule_or_raw_mutation:{i}")
        strict = oracle(expected_schedule, d, identity=True)
        latest = oracle(expected_schedule, d, identity=False)
        if row.get("strict") != strict:
            errors.append(f"strict_decision_mismatch:{i}")
        if row.get("latest_receipt_comparator") != latest:
            errors.append(f"latest_decision_mismatch:{i}")
        derived = row.get("derived", {})
        expected_derived = {
            "strict_false_completion": strict["status"] == "COMPLETED" and not expected_schedule["effect_committed"],
            "strict_unsafe_retry": strict["retry_admitted"] and not independently_safe_retry(expected_schedule, d),
            "latest_false_completion": latest["status"] == "COMPLETED" and not expected_schedule["effect_committed"],
            "latest_unsafe_retry": latest["retry_admitted"] and not independently_safe_retry(expected_schedule, d),
        }
        if derived != expected_derived:
            errors.append(f"derived_claim_mismatch:{i}")
        strict_false += expected_derived["strict_false_completion"]
        strict_unsafe += expected_derived["strict_unsafe_retry"]
        latest_false += expected_derived["latest_false_completion"]
        latest_unsafe += expected_derived["latest_unsafe_retry"]
        if expected_schedule["neutral_release_observed"] and strict["status"] == "CANCELLED_BEFORE_EMIT" and not any(a["operation_id"] == d["active_operation_id"] and a["kind"] == "CANCEL_CONFIRMED" for a in expected_schedule["receipts"]):
            neutral_release_aborts += 1
        if strict["status"] == "CANCELLED_BEFORE_EMIT" and not any(a["operation_id"] == d["active_operation_id"] and a["attempt"] == d["active_attempt"] and a["kind"] == "CANCEL_CONFIRMED" for a in expected_schedule["receipts"]):
            strict_false_cancel += 1
        if expected_schedule["timeline"] in ("current_effect_then_current_cancel", "current_cancel_then_current_effect") and (
            strict["status"] != "CONFLICT_UNKNOWN" or strict["retry_admitted"]
        ):
            conflict_gate_failures += 1
        if latest["status"] != strict["status"] or latest["retry_admitted"] != strict["retry_admitted"]:
            support += 1

    controls = mutation_controls(expected, d)
    rejected = 0
    for name, mutator in controls:
        altered = json.loads(json.dumps(candidate))
        if not mutator(altered):
            errors.append(f"mutation_not_applicable:{name}")
            continue
        if audit_without_mutations(altered, expected, d):
            errors.append(f"mutation_accepted:{name}")
        else:
            rejected += 1
    decision = "SUPPORT_FOR_PHASE_REFINEMENT_SCOPED" if support else "NO_INCREMENTAL_VALUE_SCOPED"
    method = "PASS_METHOD_SCOPED" if not errors and rejected == len(controls) and strict_false == 0 and strict_unsafe == 0 and strict_false_cancel == 0 and neutral_release_aborts == 0 and conflict_gate_failures == 0 else "FAIL_METHOD"
    return {
        "schema": "8668-a03-audit-v1",
        "allocation": RUN_ID,
        "raw_rows": len(rows),
        "oracle_rows": len(expected),
        "errors": errors,
        "mutation_controls": {"rejected": rejected, "total": len(controls)},
        "strict_false_completions": strict_false,
        "strict_unsafe_retries": strict_unsafe,
        "strict_false_cancellations": strict_false_cancel,
        "contradictory_ack_gate_failures": conflict_gate_failures,
        "latest_false_completions": latest_false,
        "latest_unsafe_retries": latest_unsafe,
        "neutral_release_aborts": neutral_release_aborts,
        "schedules_with_policy_difference": support,
        "method_gate": method,
        "decision": decision if method == "PASS_METHOD_SCOPED" else "HOLD_AUDIT_OR_METHOD_FAILURE",
    }


def audit_without_mutations(candidate: dict, expected: list[dict], d: dict) -> bool:
    rows = candidate.get("rows", [])
    if len(rows) != len(expected):
        return False
    for i, sched in enumerate(expected):
        row = rows[i]
        if row.get("exogenous") != sched:
            return False
        if row.get("strict") != oracle(sched, d, identity=True):
            return False
    return True


def mutation_controls(expected: list[dict], d: dict):
    def find(predicate):
        return next((i for i, s in enumerate(expected) if predicate(s)), None)

    stale_effect = find(lambda s: any(a["operation_id"] == d["prior_operation_id"] and a["kind"] == "EFFECT_CONFIRMED" for a in s["receipts"]) and s["phase"] in POST_EMIT)
    same_id_stale = find(lambda s: s["timeline"] == "same_id_stale_effect" and s["phase"] in POST_EMIT and not s["effect_committed"])
    stale_cancel = find(lambda s: any(a["operation_id"] == d["prior_operation_id"] and a["kind"] == "CANCEL_CONFIRMED" for a in s["receipts"]) and s["phase"] not in POST_EMIT and s["retry_requested"])
    conflict = find(lambda s: s["timeline"] == "current_effect_then_current_cancel" and s["phase"] in POST_EMIT and s["effect_committed"])
    neutral = find(lambda s: s["neutral_release_observed"] and s["phase"] not in POST_EMIT and not any(a["operation_id"] == d["active_operation_id"] and a["kind"] == "CANCEL_CONFIRMED" for a in s["receipts"]))
    active_dup = find(lambda s: s["timeline"] == "current_effect_replayed")
    unsafe = find(lambda s: s["effect_committed"] and s["retry_requested"])
    valid_effect = find(lambda s: s["timeline"] == "current_effect" and s["phase"] in POST_EMIT and s["effect_committed"])

    def accept_prior_attempt_as_current(c):
        if stale_effect is None:
            return False
        row = c["rows"][stale_effect]
        stale_id = next(a["ack_id"] for a in row["exogenous"]["receipts"] if a["operation_id"] == d["prior_operation_id"])
        row["strict"]["status"] = "COMPLETED"
        row["strict"]["accepted_ack_ids"].append(stale_id)
        return True

    def accept_same_id_wrong_attempt(c):
        if same_id_stale is None:
            return False
        row = c["rows"][same_id_stale]
        stale_id = row["exogenous"]["receipts"][0]["ack_id"]
        row["strict"]["status"] = "COMPLETED"
        row["strict"]["accepted_ack_ids"].append(stale_id)
        return True

    def stale_cancel_retry(c):
        if stale_cancel is None:
            return False
        c["rows"][stale_cancel]["strict"]["status"] = "CANCELLED_BEFORE_EMIT"
        c["rows"][stale_cancel]["strict"]["retry_admitted"] = True
        return True

    def conflict_as_complete(c):
        if conflict is None:
            return False
        c["rows"][conflict]["strict"]["status"] = "COMPLETED"
        return True

    def conflict_as_cancel(c):
        if conflict is None:
            return False
        c["rows"][conflict]["strict"]["status"] = "CANCELLED_BEFORE_EMIT"
        c["rows"][conflict]["strict"]["retry_admitted"] = True
        return True

    def duplicate_accept(c):
        if active_dup is None:
            return False
        ack_id = c["rows"][active_dup]["strict"]["accepted_ack_ids"][0]
        c["rows"][active_dup]["strict"]["accepted_ack_ids"].append(ack_id)
        return True

    def release_abort(c):
        if neutral is None:
            return False
        c["rows"][neutral]["strict"]["status"] = "CANCELLED_BEFORE_EMIT"
        c["rows"][neutral]["strict"]["retry_admitted"] = True
        return True

    def unsafe_retry(c):
        if unsafe is None:
            return False
        c["rows"][unsafe]["strict"]["retry_admitted"] = True
        return True

    def drop_valid_effect(c):
        if valid_effect is None:
            return False
        c["rows"][valid_effect]["strict"]["status"] = "UNKNOWN"
        c["rows"][valid_effect]["strict"]["accepted_ack_ids"] = []
        return True

    return [
        ("accept_prior_ack_as_active", accept_prior_attempt_as_current),
        ("accept_same_id_wrong_attempt", accept_same_id_wrong_attempt),
        ("accept_stale_cancel_for_retry", stale_cancel_retry),
        ("resolve_contradictory_acks_as_complete", conflict_as_complete),
        ("resolve_contradictory_acks_as_cancel_and_retry", conflict_as_cancel),
        ("neutral_release_as_abort", release_abort),
        ("duplicate_active_ack_reapplied", duplicate_accept),
        ("retry_after_committed_effect", unsafe_retry),
        ("drop_valid_active_effect_ack", drop_valid_effect),
    ]


def main() -> int:
    try:
        candidate = json.loads(sys.stdin.read())
        result = audit(candidate)
    except Exception as exc:  # Fail closed and preserve one auditor output.
        result = {"schema": "8668-a03-audit-v1", "allocation": RUN_ID, "errors": [f"auditor_exception:{type(exc).__name__}:{exc}"], "method_gate": "FAIL_AUDITOR", "decision": "HOLD_AUDIT_OR_METHOD_FAILURE"}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("method_gate") == "PASS_METHOD_SCOPED" and result.get("errors") == [] else 1


if __name__ == "__main__":
    raise SystemExit(main())
