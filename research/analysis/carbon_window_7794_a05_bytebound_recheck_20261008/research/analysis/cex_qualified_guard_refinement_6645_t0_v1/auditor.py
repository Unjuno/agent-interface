#!/usr/bin/env python3
"""Independent raw-only reconstruction and finite method gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _bits(state: dict[str, Any], names: list[str]) -> tuple[bool, ...]:
    return tuple(state["features"][name] for name in names)


def reconstruct(fixture: dict[str, Any]) -> dict[str, Any]:
    states = {item["id"]: item for item in fixture["state_inventory"]}
    domain = fixture["predicate_vocabulary"]
    controls = [states[name] for name in fixture["independently_verified_control_ids"]]
    baseline = fixture["original_guard"]
    ambiguous: set[tuple[bool, ...]] = set()
    unresolved: set[tuple[bool, ...]] = set()
    evidence_rows = []
    options = []
    for item in fixture["counterexamples"]:
        subject = states[item["state_id"]]
        sig = _bits(subject, domain)
        consumed = "NO_REFINEMENT_NONREAL"
        terms = []
        if item["classification"] == "REAL_GUARD_MISS" and item["independent_replay"] is True:
            matching = [c for c in controls if _bits(c, domain) == sig]
            if matching:
                ambiguous.add(sig)
                unresolved.add(sig)
                consumed = "UNKNOWN_OBSERVATIONAL_ALIAS"
            else:
                terms = [p for p in domain if all(c["features"][p] is True for c in controls) and subject["features"][p] is False]
                if terms:
                    options.extend({"counterexample_id": item["id"], "terms": [p]} for p in sorted(terms))
                    consumed = "REFINEMENT_ALTERNATIVES_RETAINED"
                else:
                    unresolved.add(sig)
                    consumed = "UNKNOWN_NO_VALID_CONTROL_PRESERVING_TERM"
        evidence_rows.append({
            "counterexample_id": item["id"],
            "state_id": subject["id"],
            "classification_consumed": item["classification"],
            "result": consumed,
            "candidate_terms": sorted(terms),
        })

    delta = sorted({p for option in options for p in option["terms"]})
    invalidated = sorted(
        c["id"] for c in fixture["cache_instances"]
        if c["active"] is True and any(p in c["depends_on"] for p in delta)
    )
    retained = sorted(c["id"] for c in fixture["cache_instances"] if c["active"] is True and c["id"] not in invalidated)
    unavailable = _bits({"features": fixture["fallback"]["unavailable_signature"]}, domain)
    dispositions = {}
    for name, state in sorted(states.items()):
        sig = _bits(state, domain)
        if name in fixture["out_of_scope_state_ids"]:
            disposition = "OUT_OF_SCOPE"
        elif sig in ambiguous or sig in unresolved:
            disposition = "UNKNOWN"
        elif not all(state["features"][p] is True for p in baseline):
            disposition = "HOLD_NO_SAFE_FALLBACK" if sig == unavailable else "DEOPT_GENERIC"
        else:
            outcomes = [all(state["features"][p] is True for p in option["terms"]) for option in options if option["terms"]]
            if not outcomes:
                disposition = "UNKNOWN"
            elif all(outcomes):
                disposition = "ADMIT"
            elif not any(outcomes):
                disposition = "REFUSE_AND_DEOPT"
            else:
                disposition = "UNKNOWN_ALTERNATIVE_DISAGREEMENT"
        dispositions[name] = disposition

    # Validate the oracle labels only in the independent audit, never in the candidate.
    truth_errors = []
    for item in fixture["counterexamples"]:
        state = states[item["state_id"]]
        if item["classification"] == "REAL_GUARD_MISS":
            if state["oracle"] != "HARMFUL" or not item["independent_replay"] or not all(state["features"][p] is True for p in baseline):
                truth_errors.append(f"invalid-real-counterexample:{item['id']}")
        elif item["classification"] == "SPURIOUS_ORACLE_OR_TRACE":
            if state["oracle"] != "SAFE_VALID" or item["independent_replay"]:
                truth_errors.append(f"invalid-spurious-classification:{item['id']}")
        elif item["classification"] == "OUT_OF_SCOPE":
            if state["oracle"] != "OUT_OF_SCOPE" or item["state_id"] not in fixture["out_of_scope_state_ids"]:
                truth_errors.append(f"invalid-out-of-scope-classification:{item['id']}")
        elif item["classification"] == "UNRESOLVED":
            if item["independent_replay"]:
                truth_errors.append(f"unresolved-with-replay:{item['id']}")

    oracle_diagnostic = {
        name: ("ADMIT" if s["oracle"] == "SAFE_VALID" else "REFUSE_AND_DEOPT" if s["oracle"] == "HARMFUL" else "OUT_OF_SCOPE")
        for name, s in sorted(states.items())
    }
    return {
        "schema": "cex-guard-refinement-raw-v1",
        "allocation_id": fixture["allocation_id"],
        "counterexample_events": evidence_rows,
        "refinement_alternatives": options,
        "changed_predicates": delta,
        "cache_invalidation": {"invalidated": invalidated, "retained": retained},
        "decisions": dispositions,
        "fallback": {
            "route": fixture["fallback"]["route"],
            "authority_before": fixture["fallback"]["authority_before"],
            "authority_after": fixture["fallback"]["authority_after"],
            "task_input_replays": 0,
        },
        "arms": fixture["arms"],
        "oracle_diagnostic": oracle_diagnostic,
        "truth_errors": truth_errors,
    }


def audit(fixture: dict[str, Any], candidate_raw: dict[str, Any]) -> dict[str, Any]:
    expected = reconstruct(fixture)
    errors = list(expected["truth_errors"])
    for field in ("schema", "allocation_id", "counterexample_events", "refinement_alternatives", "changed_predicates", "cache_invalidation", "decisions", "fallback", "arms"):
        if candidate_raw.get(field) != expected[field]:
            errors.append(f"candidate-field-mismatch:{field}")
    # A candidate payload must not carry independent truth labels/diagnostics.
    if "oracle_diagnostic" in candidate_raw or "truth_errors" in candidate_raw:
        errors.append("candidate-leaked-auditor-only-truth")
    if expected["fallback"]["authority_before"] != expected["fallback"]["authority_after"] or expected["fallback"]["task_input_replays"] != 0:
        errors.append("fallback-authority-or-replay-boundary-violated")
    d = candidate_raw.get("decisions", {})
    if any(d.get(name) == "ADMIT" for name, state in ((s["id"],s) for s in fixture["state_inventory"]) if state["oracle"] == "HARMFUL"):
        errors.append("harmful-state-admitted")
    for state in fixture["state_inventory"]:
        sig = _bits(state, fixture["predicate_vocabulary"])
        aliases = [other for other in fixture["state_inventory"] if _bits(other, fixture["predicate_vocabulary"]) == sig]
        truths = {other["oracle"] for other in aliases}
        if "SAFE_VALID" in truths and "HARMFUL" in truths:
            unavailable = _bits({"features": fixture["fallback"]["unavailable_signature"]}, fixture["predicate_vocabulary"])
            required = "HOLD_NO_SAFE_FALLBACK" if sig == unavailable else "UNKNOWN"
            if d.get(state["id"]) != required:
                errors.append(f"observational-alias-not-conservatively-held:{state['id']}")
    expected_alternatives = [
        ["context_current"], ["focus_current"]
    ]
    observed_alternatives = sorted([item["terms"] for item in candidate_raw.get("refinement_alternatives", [])])
    if observed_alternatives != expected_alternatives:
        errors.append("minimal-alternative-set-mismatch")
    real_cex_ids = {
        item["state_id"] for item in fixture["counterexamples"]
        if item["classification"] == "REAL_GUARD_MISS" and item["independent_replay"] is True
    }
    comparison = {}
    for arm in fixture["arms"]:
        counts = {"valid_admitted": 0, "valid_unknown": 0, "valid_deopt": 0,
                  "harmful_admitted": 0, "harmful_unknown": 0, "harmful_deopt": 0}
        for state in fixture["state_inventory"]:
            sid = state["id"]
            truth = state["oracle"]
            if truth == "OUT_OF_SCOPE":
                continue
            original_admits = all(state["features"][p] is True for p in fixture["original_guard"])
            if arm == "UNCHANGED_GUARD":
                disposition = "ADMIT" if original_admits else "DEOPT_GENERIC"
            elif arm == "INVALIDATE_ALL_FALLBACK":
                sig = _bits(state, fixture["predicate_vocabulary"])
                missing_fallback = _bits({"features": fixture["fallback"]["unavailable_signature"]}, fixture["predicate_vocabulary"])
                disposition = "HOLD_NO_SAFE_FALLBACK" if sig == missing_fallback else "DEOPT_GENERIC"
            elif arm == "EXACT_STATE_BLACKLIST":
                disposition = "REFUSE_AND_DEOPT" if sid in real_cex_ids else "ADMIT" if original_admits else "DEOPT_GENERIC"
            elif arm == "CANDIDATE_REFINEMENT":
                disposition = candidate_raw.get("decisions", {}).get(sid, "MISSING")
            else:
                disposition = "ADMIT" if truth == "SAFE_VALID" else "REFUSE_AND_DEOPT"
            group = "valid" if truth == "SAFE_VALID" else "harmful"
            if disposition == "ADMIT":
                counts[f"{group}_admitted"] += 1
            elif disposition in {"UNKNOWN", "UNKNOWN_ALTERNATIVE_DISAGREEMENT", "HOLD_NO_SAFE_FALLBACK"}:
                counts[f"{group}_unknown"] += 1
            else:
                counts[f"{group}_deopt"] += 1
        comparison[arm] = counts
    if comparison.get("CANDIDATE_REFINEMENT", {}).get("harmful_admitted", 0) != 0:
        errors.append("candidate-arm-harmful-admission")
    status = "PASS_METHOD_SCOPED" if not errors else "HOLD_AUDIT_INTEGRITY"
    return {
        "schema": "cex-guard-refinement-audit-v1",
        "allocation_id": fixture["allocation_id"],
        "audit_status": status,
        "errors": errors,
        "state_count": len(fixture["state_inventory"]),
        "counterexample_count": len(fixture["counterexamples"]),
        "raw_counterexample_events": len(candidate_raw.get("counterexample_events", [])),
        "refinement_alternative_count": len(observed_alternatives),
        "ambiguous_state_count": sum(v == "UNKNOWN" for v in candidate_raw.get("decisions", {}).values()),
        "invalidated_sibling_caches": candidate_raw.get("cache_invalidation", {}).get("invalidated", []),
        "arm_comparison": comparison,
        "scope": "deterministic finite fixture only; no live GUI, runtime safety, task-effect or production claim"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture")
    parser.add_argument("raw")
    parser.add_argument("output")
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["audit_status"] == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
