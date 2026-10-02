"""Raw-only independent decision-gate audit for Issue #5795 T0.

This file deliberately imports no candidate, protocol, or runner code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal


SCHEDULE = (
    ("pre_write", "A", "READY_BEFORE_WRITE", "ADMIT_STALE", "NOT_ACKNOWLEDGED"),
    ("pre_write", "B", "READY_BEFORE_WRITE", "ADMIT_STALE", "NOT_ACKNOWLEDGED"),
    ("pre_write", "C", "READY_BEFORE_WRITE", "UNKNOWN", "NOT_ACKNOWLEDGED"),
    ("partial_split_write", "B", "CANDIDATE_WRITTEN", "ADMIT_STALE", "NOT_ACKNOWLEDGED"),
    ("pre_commit", "C", "PRE_COMMIT", "UNKNOWN", "NOT_ACKNOWLEDGED"),
    ("post_commit_pre_ack", "C", "POST_COMMIT_PRE_ACK", "DENY_SUPPRESSED", "UNKNOWN"),
    ("acknowledged_restart", "A", None, "ADMIT_STALE", "ACKNOWLEDGED"),
    ("acknowledged_restart", "B", None, "DENY_SUPPRESSED", "ACKNOWLEDGED"),
    ("acknowledged_restart", "C", None, "DENY_SUPPRESSED", "ACKNOWLEDGED"),
    ("new_generation_same_fingerprint", "C", None, "ALLOW_FRESH", "ACKNOWLEDGED"),
    ("changed_target_same_label", "C", None, "UNKNOWN", "ACKNOWLEDGED"),
    ("reactivation", "C", None, "ALLOW_FRESH", "ACKNOWLEDGED"),
    ("expiry_gc_tombstone", "C", None, "EXPIRY_GC_SEQUENCE", "ACKNOWLEDGED"),
    ("malformed_record", "C", None, "UNKNOWN", "NOT_ACKNOWLEDGED"),
    ("repeated_restart", "C", None, "DENY_SUPPRESSED", "ACKNOWLEDGED"),
)


def canonical_identity(fields: dict[str, str]) -> str:
    encoded = json.dumps(
        (fields["fingerprint"], fields["target"], fields["label"]),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    baseline_failures: list[str] = []
    if len(rows) != len(SCHEDULE):
        errors.append(f"row_count:{len(rows)}!=frozen:{len(SCHEDULE)}")

    by_candidate: list[bool] = []
    for index, spec in enumerate(SCHEDULE):
        if index >= len(rows):
            break
        case, policy, cut, expected, expected_ack = spec
        row = rows[index]
        label = f"row[{index}]/{case}/{policy}"
        if row.get("case") != case or row.get("policy") != policy:
            errors.append(f"{label}:schedule_order_or_identity")
            continue
        fields = row.get("fields")
        if not isinstance(fields, dict) or not all(
            isinstance(fields.get(k), str) and fields.get(k)
            for k in ("fingerprint", "target", "label")
        ):
            errors.append(f"{label}:identity_fields")
            continue
        identity = canonical_identity(fields)
        if row.get("identity_sha256") != identity:
            errors.append(f"{label}:identity_hash")
        persist = row.get("persist")
        if case == "malformed_record":
            if persist is not None:
                errors.append(f"{label}:unexpected_persist")
        elif not isinstance(persist, dict):
            errors.append(f"{label}:missing_persist_receipt")
        else:
            events = persist.get("events")
            if not isinstance(events, list) or not events:
                errors.append(f"{label}:missing_process_events")
            elif cut is None:
                if persist.get("returncode") != 0 or persist.get("acknowledged") is not True:
                    errors.append(f"{label}:acknowledged_process_exit")
                if not isinstance(events[-1], dict) or events[-1].get("event") != "ACKNOWLEDGED":
                    errors.append(f"{label}:acknowledgment_event")
            else:
                if persist.get("returncode") != -signal.SIGKILL:
                    errors.append(f"{label}:process_was_not_SIGKILLed")
                if not isinstance(events[-1], dict) or events[-1].get("event") != cut:
                    errors.append(f"{label}:wrong_crash_cutpoint")
                if persist.get("acknowledged") is not False:
                    errors.append(f"{label}:crash_mislabeled_acknowledged")

        if row.get("ack_state") != expected_ack:
            errors.append(f"{label}:ack_state")
        probes = row.get("probes")
        expected_list = (["DENY_SUPPRESSED", "UNKNOWN", "DENY_RETIRED"] if case == "expiry_gc_tombstone"
                         else [expected, expected] if case == "repeated_restart" else [expected])
        if not isinstance(probes, list) or len(probes) != len(expected_list):
            errors.append(f"{label}:probe_count")
            observed: list[object] = []
        else:
            observed = [p.get("disposition") if isinstance(p, dict) else None for p in probes]
            if observed != expected_list:
                errors.append(f"{label}:disposition:{observed!r}!={expected_list!r}")

        if case == "changed_target_same_label":
            changed = dict(fields)
            changed["target"] = "target-02"
            if row.get("probe_identity_sha256") != canonical_identity(changed):
                errors.append(f"{label}:changed_target_identity_not_bound")
        if case == "reactivation":
            mutation = row.get("mutation")
            if not isinstance(mutation, dict) or mutation.get("event") != "MUTATION_ACKNOWLEDGED" or mutation.get("changed") != 1:
                errors.append(f"{label}:reactivation_receipt")
        if case == "expiry_gc_tombstone":
            ttl = row.get("ttl")
            gc = row.get("gc")
            pre_gc = row.get("pre_expiry_gc")
            pre_state = row.get("pre_expiry_state")
            pre = row.get("pre_expiry_probe")
            post = row.get("post_expiry_probe")
            if ttl != {"issued_at": 100, "duration": 50, "expires_at": 150,
                       "pre_probe_at": 149, "gc_at": 150, "post_probe_at": 150}:
                errors.append(f"{label}:frozen_ttl_clock")
            if not isinstance(pre, dict) or pre.get("disposition") != "DENY_SUPPRESSED" or pre.get("reason") != "unexpired_generation_match":
                errors.append(f"{label}:pre_expiry_probe")
            expired_probe = row.get("expired_pre_gc_probe")
            if not isinstance(expired_probe, dict) or expired_probe.get("disposition") != "UNKNOWN" or expired_probe.get("reason") != "expired_pending_gc":
                errors.append(f"{label}:expired_pre_gc_probe")
            if not isinstance(pre_gc, dict) or pre_gc.get("event") != "GC_ACKNOWLEDGED" or pre_gc.get("changed") != 0 or pre_gc.get("retained") is not True or pre_gc.get("disposition") != "SUPPRESSED":
                errors.append(f"{label}:pre_expiry_gc_control")
            if not isinstance(pre_state, dict) or pre_state.get("event") != "TOMBSTONE_STATE" or pre_state.get("retained") is not True or pre_state.get("disposition") != "SUPPRESSED" or pre_state.get("expires_at") != 150 or pre_state.get("retired_at") is not None:
                errors.append(f"{label}:pre_expiry_state")
            if not isinstance(gc, dict) or gc.get("event") != "GC_ACKNOWLEDGED" or gc.get("changed") != 1 or gc.get("retained") is not True or gc.get("disposition") != "RETIRED" or gc.get("retired_at") != 150:
                errors.append(f"{label}:gc_tombstone_retention")
            if not isinstance(post, dict) or post.get("disposition") != "DENY_RETIRED" or post.get("reason") != "retirement_tombstone":
                errors.append(f"{label}:post_gc_probe")

        pass_row = observed == expected_list and row.get("ack_state") == expected_ack
        if policy == "C":
            by_candidate.append(pass_row)
        elif not pass_row:
            errors.append(f"{label}:baseline_control_did_not_reproduce")
        else:
            if expected in {"ADMIT_STALE"}:
                baseline_failures.append(label)

    complete_candidate = len(by_candidate) == 10 and all(by_candidate)
    decision = "PASS_CRASH_ATOMIC_SUPPRESSION_T0_SCOPED" if not errors and complete_candidate else "HOLD_OR_FAIL_AUDIT"
    return {
        "decision": decision,
        "rows": len(rows),
        "candidate_rows": len(by_candidate),
        "candidate_rows_matching_frozen_gate": sum(by_candidate),
        "baseline_failures_reproduced": baseline_failures,
        "errors": errors,
        "scope": "single-process-kill/restart fixture only; no power-loss, concurrency, GUI, or product claim",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if os.environ.get("OBSTAC_RUN_KIND") != "formal":
        raise SystemExit("STOP_AUDIT_RUN_KIND")
    if os.environ.get("OBSTAC_PLATFORM") != "linux/arm64":
        raise SystemExit("STOP_AUDIT_PLATFORM")
    if os.environ.get("OBSTAC_AUDIT_SHA256") != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise SystemExit("STOP_AUDIT_SOURCE_HASH")
    raw_path = Path(args.raw)
    output = Path(args.out)
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise SystemExit("STOP_NONEMPTY_AUDIT_OUTPUT")
    else:
        output.mkdir(parents=True)
    output_file = output / "audit.json"
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
    result = audit_rows(rows)
    result["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    output_file.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PASS_CRASH_ATOMIC_SUPPRESSION_T0_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
