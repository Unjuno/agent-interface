"""Independent raw-output auditor. Deliberately imports no candidate module."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path


SAFE = {"ADD_EVIDENCE", "REVOKE_CLAIM", "RECORD_IDEMPOTENT_RECEIPT"}
OPS = {
    "ADD_EVIDENCE": ["e0", "e1"],
    "REVOKE_CLAIM": ["c0", "c1"],
    "RECORD_IDEMPOTENT_RECEIPT": ["r0", "r1"],
    "REFRESH_EPOCH": [None],
    "RESERVE_QUOTA": ["r-left", "r-right"],
    "COMMIT_EFFECT": [None],
}


def state_for(op: str, value: str | None) -> dict:
    state = {"evidence": set(), "admitted_claims": set(), "revoked_claims": set(),
             "authority_epoch": 0, "quota_reservations": set(), "effect_committed": False}
    if op == "ADD_EVIDENCE":
        state["evidence"].add(value)
    elif op == "REVOKE_CLAIM":
        state["revoked_claims"].add(value)
    elif op == "RECORD_IDEMPOTENT_RECEIPT":
        state["evidence"].add(f"receipt:{value}")
    elif op == "REFRESH_EPOCH":
        state["authority_epoch"] = 1
    elif op == "RESERVE_QUOTA":
        state["quota_reservations"].add(str(value))
    elif op == "COMMIT_EFFECT":
        state["effect_committed"] = True
    else:
        raise AssertionError(f"unrecognized input operation {op}")
    return state


def merge_oracle(a: dict, b: dict) -> dict:
    return {
        "evidence": set(a["evidence"]) | set(b["evidence"]),
        "admitted_claims": set(a["admitted_claims"]) | set(b["admitted_claims"]),
        "revoked_claims": set(a["revoked_claims"]) | set(b["revoked_claims"]),
        "authority_epoch": max(a["authority_epoch"], b["authority_epoch"]),
        "quota_reservations": set(a["quota_reservations"]) | set(b["quota_reservations"]),
        "effect_committed": bool(a["effect_committed"] or b["effect_committed"]),
    }


def safe_oracle(s: dict) -> bool:
    if len(s["quota_reservations"]) > 1:
        return False
    if set(s["admitted_claims"]) & set(s["revoked_claims"]):
        return False
    return not s["effect_committed"] or (s["authority_epoch"] == 1 and "e0" in s["evidence"])


def direct_single(op: str, value: str | None) -> dict:
    """Independently define each allowed primitive delta."""
    state = {"evidence": set(), "admitted_claims": set(), "revoked_claims": set(),
             "authority_epoch": 0, "quota_reservations": set(), "effect_committed": False}
    if op == "ADD_EVIDENCE":
        state["evidence"].add(value)
    elif op == "REVOKE_CLAIM":
        state["revoked_claims"].add(value)
    elif op == "RECORD_IDEMPOTENT_RECEIPT":
        state["evidence"].add(f"receipt:{value}")
    elif op == "REFRESH_EPOCH":
        state["authority_epoch"] = 1
    elif op == "RESERVE_QUOTA":
        state["quota_reservations"].add(str(value))
    elif op == "COMMIT_EFFECT":
        state["effect_committed"] = True
    else:
        raise AssertionError(f"unknown operation {op}")
    return state


def main() -> None:
    source = Path("/out/candidate.json")
    raw = json.loads(source.read_text(encoding="utf-8"))
    expected = list(itertools.product(
        [(op, val) for op, vals in OPS.items() for val in vals],
        [(op, val) for op, vals in OPS.items() for val in vals],
    ))
    errors = []
    expected_labels = {op: ("monotone_safe" if op in SAFE else "coordination_required") for op in OPS}
    if raw.get("operation_labels") != expected_labels:
        errors.append("operation_classification_mismatch")
    if raw.get("pair_count") != len(expected) or len(raw.get("rows", [])) != len(expected):
        errors.append("pair_count_or_rows_mismatch")
    row_by_key = {(r["op_a"], r["value_a"], r["op_b"], r["value_b"]): r for r in raw.get("rows", [])}
    if len(row_by_key) != len(expected):
        errors.append("duplicate_or_missing_pair_keys")
    unsafe_safe_pairs = 0
    coordination_witnesses = {op: 0 for op in OPS if op not in SAFE}
    safe_pairs = 0
    idempotence_checked = 0
    operation_errors = []
    for op, values in OPS.items():
        expected_label = "monotone_safe" if op in SAFE else "coordination_required"
        for value in values:
            if raw.get("operation_labels", {}).get(op) != expected_label:
                operation_errors.append(f"classification_mismatch:{op}")
            key = (op, value, op, value)
            row = row_by_key.get(key)
            one = direct_single(op, value)
            expected_one = {**one, "evidence": sorted(one["evidence"]),
                            "admitted_claims": sorted(one["admitted_claims"]),
                            "revoked_claims": sorted(one["revoked_claims"]),
                            "quota_reservations": sorted(one["quota_reservations"])}
            if row is None or row.get("joined") != expected_one:
                operation_errors.append(f"idempotence_mismatch:{op}:{value}")
            idempotence_checked += 1
    if operation_errors:
        errors.extend(operation_errors)
    for (op_a, val_a), (op_b, val_b) in expected:
        row = row_by_key.get((op_a, val_a, op_b, val_b))
        if row is None:
            errors.append(f"missing:{op_a}:{val_a}:{op_b}:{val_b}")
            continue
        if row.get("label_a") != expected_labels[op_a] or row.get("label_b") != expected_labels[op_b]:
            errors.append(f"pair_classification_mismatch:{op_a}:{op_b}")
        a, b = state_for(op_a, val_a), state_for(op_b, val_b)
        joined = merge_oracle(a, b)
        actual = row.get("joined", {})
        normalized = {**joined, "evidence": sorted(joined["evidence"]),
                      "admitted_claims": sorted(joined["admitted_claims"]),
                      "revoked_claims": sorted(joined["revoked_claims"]),
                      "quota_reservations": sorted(joined["quota_reservations"])}
        if actual != normalized:
            errors.append(f"oracle_join_mismatch:{op_a}:{op_b}")
        verdict = safe_oracle(joined)
        if row.get("invariant") is not verdict:
            errors.append(f"oracle_verdict_mismatch:{op_a}:{op_b}")
        if not row.get("reverse_equal"):
            errors.append(f"commutativity_failure:{op_a}:{op_b}")
        if op_a in SAFE and op_b in SAFE:
            safe_pairs += 1
            if not verdict:
                unsafe_safe_pairs += 1
                errors.append(f"unsafe_monotone_pair:{op_a}:{val_a}:{op_b}:{val_b}")
        else:
            for op in (op_a, op_b):
                if op in coordination_witnesses and not verdict:
                    coordination_witnesses[op] += 1
    no_witness = [op for op, count in coordination_witnesses.items() if not count]
    if no_witness:
        errors.append("coordination_counterexample_missing:" + ",".join(no_witness))
    audit = {
        "allocation": raw.get("allocation"), "kind": "independent_audit",
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "pairs_checked": len(expected), "monotone_pairs_checked": safe_pairs,
        "idempotence_checks": idempotence_checked,
        "unsafe_monotone_pairs": unsafe_safe_pairs,
        "coordination_witness_counts": coordination_witnesses,
        "errors": errors, "decision": "PASS" if not errors else "FAIL",
    }
    out = Path("/out/audit.json")
    out.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
