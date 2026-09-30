"""Independent raw-only auditor for the Issue #5332 T0."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import oracle


EXPECTED_POLICIES = {
    "FLAT_RECEIPTS", "STATIC_CASE", "DYNAMIC_CASE", "DEFEATER_AWARE",
    "INDEPENDENCE_AWARE", "COMPOSITE_DYNAMIC_CASE",
}
EXPECTED_CASES = {
    "BASELINE", "DEPENDENCY_CHANGED", "MISSING_CAUSALITY",
    "CORRELATED_DUPLICATE", "DIRECT_DEFEATER", "NEGATIVE_SUCCESSOR",
}


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evidence_digest(row: dict[str, Any]) -> str:
    payload = "|".join(str(row[key]) for key in (
        "evidence_id", "claim", "polarity", "source_revision",
        "independence_domain", "defeats",
    )).encode()
    return hashlib.sha256(payload).hexdigest()


def audit(raw: dict[str, Any]) -> list[str]:
    errors = []
    metadata = raw.get("metadata", {})
    if metadata.get("allocation") != "dynamic-assurance-case-5332-t0-20260930-01":
        errors.append("allocation mismatch")
    if metadata.get("source_main") != "bdd093f24c626c7ffadaa7ba2a6c8e408814675c":
        errors.append("source main mismatch")
    if metadata.get("mode") != "host-only-synthetic-t0":
        errors.append("execution mode mismatch")
    if metadata.get("container_invocations") != 0:
        errors.append("declared execution scope mismatch")
    if metadata.get("network_requests") != 0 or metadata.get("model_calls") != 0:
        errors.append("unexpected network/model call")
    if metadata.get("gui_or_input_actions") != 0 or metadata.get("external_effect_calls") != 0:
        errors.append("unexpected GUI/effect")
    cases = raw.get("scenario_inputs", {})
    policies = set(raw.get("policies", []))
    if set(cases) != EXPECTED_CASES:
        errors.append("scenario set mismatch")
    if policies != EXPECTED_POLICIES:
        errors.append("policy set mismatch")
    rows = raw.get("rows", [])
    if len(rows) != 36:
        errors.append("row count mismatch")
    seen = set()
    for row in rows:
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append("duplicate policy/case row")
        seen.add(key)
        case = cases.get(row.get("case_id"))
        if case is None or row.get("policy") not in EXPECTED_POLICIES:
            errors.append("row key not declared")
            continue
        wanted_status, wanted_reasons = oracle.expected(row["policy"], case)
        if row.get("status") != wanted_status or row.get("reasons") != wanted_reasons:
            errors.append(f"independent decision mismatch:{key}")
        if row.get("authority_created") is not False:
            errors.append("authority flag not false")
        if row.get("external_effect_calls") != 0:
            errors.append("external effect count not zero")
    if len(seen) != 36:
        errors.append("incomplete policy/case matrix")
    for scenario in cases.values():
        evidence_ids = [item.get("evidence_id") for item in scenario.get("evidence", [])]
        if len(evidence_ids) != len(set(evidence_ids)):
            errors.append("duplicate evidence ID")
        for item in scenario.get("evidence", []):
            if item.get("artifact_sha256") != evidence_digest(item):
                errors.append("evidence artifact digest mismatch")
    successor = cases.get("NEGATIVE_SUCCESSOR", {}).get("history", [])
    if len(successor) != 1:
        errors.append("negative successor history missing")
    else:
        item = successor[0]
        computed = digest(item.get("graph"))
        if item.get("before_digest") != computed or item.get("after_digest") != computed:
            errors.append("historical graph revision changed")
        expected_prior = {
            "revision": 1,
            "claim": "SAFE_TO_RELEASE",
            "evidence": cases.get("BASELINE", {}).get("evidence"),
        }
        if item.get("graph") != expected_prior:
            errors.append("historical graph differs from prior supported revision")
        successor_evidence = cases.get("NEGATIVE_SUCCESSOR", {}).get("evidence", [])
        prior_evidence = item.get("graph", {}).get("evidence", [])
        if successor_evidence[:len(prior_evidence)] != prior_evidence:
            errors.append("negative successor rewrote predecessor evidence")
    return errors


def corruption_controls(raw: dict[str, Any]) -> list[dict[str, Any]]:
    mutations = {
        "REMOVE_POLICY_ROW": lambda value: value["rows"].pop(),
        "ALTER_DECISION": lambda value: value["rows"][0].__setitem__("status", "CONFLICTED"),
        "CHANGE_SOURCE_REVISION": lambda value: value["scenario_inputs"]["DEPENDENCY_CHANGED"]["evidence"][0].__setitem__("source_revision", 2),
        "MINT_AUTHORITY": lambda value: value["rows"][0].__setitem__("authority_created", True),
        "EMIT_EXTERNAL_EFFECT": lambda value: value["rows"][0].__setitem__("external_effect_calls", 1),
        "REWRITE_HISTORY_DIGEST": lambda value: value["scenario_inputs"]["NEGATIVE_SUCCESSOR"]["history"][0].__setitem__("after_digest", "0" * 64),
    }
    results = []
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        results.append({"control": name, "rejected": bool(audit(changed))})
    return results


def main(source: str, destination: str) -> None:
    raw = json.loads(Path(source).read_text(encoding="utf-8"))
    errors = audit(raw)
    controls = corruption_controls(raw)
    failed_controls = [item["control"] for item in controls if not item["rejected"]]
    unsound = []
    indexed = {(row["case_id"], row["policy"]): row for row in raw.get("rows", [])}
    for case_id, case in raw.get("scenario_inputs", {}).items():
        for policy in raw.get("policies", []):
            expected_status, _ = oracle.top_claim_truth(case)
            row = indexed.get((case_id, policy), {})
            if row.get("status") == "SUPPORTED" and expected_status != "SUPPORTED":
                unsound.append({"case_id": case_id, "policy": policy})
    receipt = {
        "status": "PASS_READONLY" if not errors and not failed_controls else "FAIL_AUDIT",
        "errors": errors,
        "corruption_controls": controls,
        "failed_corruption_controls": failed_controls,
        "rows": len(raw.get("rows", [])),
        "unsound_supported_cases": unsound,
        "historical_revision_preserved": not any("historical graph revision changed" in error for error in errors),
    }
    Path(destination).write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    if errors or failed_controls:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 -B audit.py RAW.json AUDIT.json")
    main(sys.argv[1], sys.argv[2])
