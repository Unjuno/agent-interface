#!/usr/bin/env python3
"""Independent reconstruction and mutation challenge; does not import candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CASES = {
    "VALID": ({"recipient": "team@example.test", "format": "pdf"}, True, "FIXED_BY_EXPLICIT_CONSTRAINT"),
    "WRONG_RECIPIENT": ({"recipient": "archive@example.test", "format": "pdf"}, False, "FIXED_BY_EXPLICIT_CONSTRAINT"),
    "WRONG_FORMAT": ({"recipient": "team@example.test", "format": "docx"}, False, "FIXED_BY_EXPLICIT_CONSTRAINT"),
    "UNSPECIFIED_PREFERENCE_REVISION": ({"recipient": "team@example.test", "format": "pdf"}, None, "UNSCORABLE_PREFERENCE"),
}
POLICIES = {
    "PREVIEW_FIRST": ["candidate_preview", "source_constraint", "neutral_facts"],
    "CONSTRAINT_FIRST": ["source_constraint_recall", "candidate_preview", "neutral_facts"],
    "NEUTRAL_FACTS_FIRST": ["neutral_facts", "candidate_preview", "source_constraint"],
}
SOURCE_TASK = "Send the quarterly report to team@example.test as PDF."
CONSTRAINT = {"recipient": "team@example.test", "format": "pdf"}
FACTS = ["The report contains the approved quarterly summary.",
         "The source task specifies delivery to team@example.test as PDF."]


def digest(effect: dict) -> str:
    return hashlib.sha256(json.dumps(effect, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_rows() -> dict[tuple[str, str], dict]:
    expected = {}
    for case_id, (effect, allowed, preference) in CASES.items():
        for policy, events in POLICIES.items():
            expected[(case_id, policy)] = {
                "case_id": case_id, "policy": policy, "source_task": SOURCE_TASK,
                "source_constraint": CONSTRAINT, "candidate_effect": effect,
                "candidate_digest": digest(effect), "allowed_by_explicit_constraint": allowed,
                "preference_status": preference, "agent_origin": True,
                "authority": "HYPOTHETICAL_NO_EXECUTION", "neutral_facts": FACTS,
                "unsupported_endorsement": False, "oracle_label_exposed": False,
                "presentation_events": events,
            }
    return expected


def row_errors(row: dict, expected: dict) -> list[str]:
    problems = []
    for key, value in expected.items():
        if row.get(key) != value:
            problems.append(key)
    if row.get("candidate_digest") != digest(row.get("candidate_effect", {})):
        problems.append("digest_binding")
    return problems


def run_mutation_challenges() -> dict[str, bool]:
    import copy
    baseline = next(iter(expected_rows().values()))
    mutations = {
        "recipient_swap": lambda x: x["candidate_effect"].__setitem__("recipient", "other@example.test"),
        "format_swap": lambda x: x["candidate_effect"].__setitem__("format", "txt"),
        "remove_agent_provenance": lambda x: x.__setitem__("agent_origin", False),
        "inject_quality_endorsement": lambda x: x.__setitem__("unsupported_endorsement", True),
        "leak_oracle_label": lambda x: x.__setitem__("oracle_label_exposed", True),
        "alter_candidate_digest": lambda x: x.__setitem__("candidate_digest", "0" * 64),
    }
    rejected = {}
    for name, mutate in mutations.items():
        mutant = copy.deepcopy(baseline)
        mutate(mutant)
        rejected[name] = bool(row_errors(mutant, baseline))
    return rejected


def audit(data: dict) -> dict:
    errors = []
    if data.get("schema") != "preview-constraint-parity-6565-candidate-v1":
        errors.append("schema_mismatch")
    expected = expected_rows()
    received = {}
    for i, row in enumerate(data.get("rows", [])):
        key = (row.get("case_id"), row.get("policy"))
        if key in received:
            errors.append(f"duplicate:{key}")
        received[key] = row
    if set(received) != set(expected):
        errors.append("coverage_mismatch")
    for key, wanted in expected.items():
        if key in received:
            fields = row_errors(received[key], wanted)
            if fields:
                errors.append(f"row_mismatch:{key[0]}:{key[1]}:{','.join(fields)}")
    mutants = run_mutation_challenges()
    if not all(mutants.values()):
        errors.append("mutation_not_rejected")
    return {"schema": "preview-constraint-parity-6565-audit-v1",
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "rows_expected": len(expected), "rows_received": len(data.get("rows", [])),
            "unique_rows": len(received), "mutations_rejected": mutants,
            "errors": errors,
            "scope": "authored-card factual parity and auditor sensitivity only; no human or causal claim"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = Path(args.candidate).read_bytes()
    result = audit(json.loads(raw))
    result["candidate_sha256"] = hashlib.sha256(raw).hexdigest()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "rows": result["rows_received"],
                      "errors": len(result["errors"])}))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
