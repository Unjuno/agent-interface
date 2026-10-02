#!/usr/bin/env python3
"""Emit frozen truthful presentation cards for Issue #6565 T0 method checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


POLICIES = ("PREVIEW_FIRST", "CONSTRAINT_FIRST", "NEUTRAL_FACTS_FIRST")
CASES = {
    "VALID": {"source_constraint": {"recipient": "team@example.test", "format": "pdf"},
              "candidate_effect": {"recipient": "team@example.test", "format": "pdf"},
              "allowed": True, "preference": "FIXED_BY_EXPLICIT_CONSTRAINT"},
    "WRONG_RECIPIENT": {"source_constraint": {"recipient": "team@example.test", "format": "pdf"},
                         "candidate_effect": {"recipient": "archive@example.test", "format": "pdf"},
                         "allowed": False, "preference": "FIXED_BY_EXPLICIT_CONSTRAINT"},
    "WRONG_FORMAT": {"source_constraint": {"recipient": "team@example.test", "format": "pdf"},
                     "candidate_effect": {"recipient": "team@example.test", "format": "docx"},
                     "allowed": False, "preference": "FIXED_BY_EXPLICIT_CONSTRAINT"},
    "UNSPECIFIED_PREFERENCE_REVISION": {
        "source_constraint": {"recipient": "team@example.test", "format": "pdf"},
        "candidate_effect": {"recipient": "team@example.test", "format": "pdf"},
        "allowed": None, "preference": "UNSCORABLE_PREFERENCE"},
}
FACTS = ["The report contains the approved quarterly summary.",
         "The source task specifies delivery to team@example.test as PDF."]


def canonical_digest(effect: dict) -> str:
    blob = json.dumps(effect, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def emit() -> dict:
    rows = []
    for case_id, case in CASES.items():
        for policy in POLICIES:
            events = {
                "PREVIEW_FIRST": ["candidate_preview", "source_constraint", "neutral_facts"],
                "CONSTRAINT_FIRST": ["source_constraint_recall", "candidate_preview", "neutral_facts"],
                "NEUTRAL_FACTS_FIRST": ["neutral_facts", "candidate_preview", "source_constraint"],
            }[policy]
            rows.append({
                "case_id": case_id, "policy": policy,
                "source_task": "Send the quarterly report to team@example.test as PDF.",
                "source_constraint": case["source_constraint"],
                "candidate_effect": case["candidate_effect"],
                "candidate_digest": canonical_digest(case["candidate_effect"]),
                "allowed_by_explicit_constraint": case["allowed"],
                "preference_status": case["preference"],
                "agent_origin": True,
                "authority": "HYPOTHETICAL_NO_EXECUTION",
                "neutral_facts": list(FACTS),
                "unsupported_endorsement": False,
                "oracle_label_exposed": False,
                "presentation_events": events,
            })
    return {"schema": "preview-constraint-parity-6565-candidate-v1", "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(emit(), sort_keys=True, indent=2) + "\n"
    with target.open("x", encoding="utf-8", newline="\n") as f:
        f.write(payload)
    print(json.dumps({"schema": "preview-constraint-parity-6565-candidate-v1", "rows": 12}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
