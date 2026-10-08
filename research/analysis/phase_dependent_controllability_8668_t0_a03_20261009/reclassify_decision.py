#!/usr/bin/env python3
"""Post-run decision-label mapping; does not execute candidate or auditor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    design_path = ROOT / "design.json"
    audit_path = ROOT / "run-01" / "audit.json"
    design = json.loads(design_path.read_text())
    audit = json.loads(audit_path.read_text())
    if audit.get("method_gate") != "PASS_METHOD_SCOPED" or audit.get("errors") != []:
        raise SystemExit("HOLD: original audit is not a clean scoped method pass")
    if audit.get("mutation_controls") != {"rejected": 9, "total": 9}:
        raise SystemExit("HOLD: frozen mutation gate does not pass")
    strict_zero_fields = (
        "strict_false_completions",
        "strict_false_cancellations",
        "strict_unsafe_retries",
        "neutral_release_aborts",
        "contradictory_ack_gate_failures",
    )
    if any(audit.get(field) != 0 for field in strict_zero_fields):
        raise SystemExit("HOLD: strict policy invariant counter is nonzero")
    if audit.get("schedules_with_policy_difference", 0) <= 0:
        raise SystemExit("NO_INCREMENTAL_VALUE: no decision difference was found")
    if audit.get("latest_false_completions", 0) + audit.get("latest_unsafe_retries", 0) <= 0:
        raise SystemExit("HOLD: identity-blind comparator has no frozen failure witness")

    precise = "SUPPORT_FOR_ID_ATTEMPT_BINDING_SCOPED"
    if precise not in design.get("HTDCU", {}).get("D", {}):
        raise SystemExit("HOLD: precise A03 decision is absent from frozen design")
    original = audit.get("decision")
    result = {
        "schema": "8668-a03-decision-label-reclassification-v1",
        "allocation": audit["allocation"],
        "reclassification_only": True,
        "candidate_or_original_auditor_rerun": False,
        "source_sha256": {
            "design.json": digest(design_path),
            "run-01/audit.json": digest(audit_path),
            "run-01/candidate.json": digest(ROOT / "run-01" / "candidate.json"),
        },
        "original_audit_method_gate": audit["method_gate"],
        "original_audit_decision_label": original,
        "frozen_A03_decision_label": precise,
        "normalized_A03_disposition": precise,
        "reason": "The frozen A03 HTDCU gate names the operation-ID/attempt sub-hypothesis; the one-shot audit serialized the broader parent-Issue phase-refinement label. Raw rows, first audit, freeze, and execution are unchanged.",
        "scope": "A03 authored finite model only; this does not reinstate or replace A02's stale-ACK transition HOLD and does not satisfy a live backend/GUI gate.",
    }
    out = ROOT / "DECISION_LABEL_RECLASSIFICATION.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": out.name, "normalized_A03_disposition": precise, "original_audit_decision": original}, sort_keys=True))


if __name__ == "__main__":
    main()
