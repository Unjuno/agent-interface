"""Single-run synthetic T0 runner for Issue #5332."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import candidate


ALLOCATION = "dynamic-assurance-case-5332-t0-20260930-01"
SOURCE_MAIN = "bdd093f24c626c7ffadaa7ba2a6c8e408814675c"


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evidence_digest(row: dict[str, Any]) -> str:
    payload = "|".join(str(row[key]) for key in (
        "evidence_id", "claim", "polarity", "source_revision",
        "independence_domain", "defeats",
    )).encode()
    return hashlib.sha256(payload).hexdigest()


def evidence_row(
    evidence_id: str,
    claim: str,
    domain: str,
    revision: int = 1,
    polarity: str = "SUPPORT",
    defeats: str | None = None,
) -> dict[str, Any]:
    row = {
        "evidence_id": evidence_id,
        "claim": claim,
        "polarity": polarity,
        "source_revision": revision,
        "independence_domain": domain,
        "defeats": defeats,
        "artifact_sha256": "",
    }
    row["artifact_sha256"] = evidence_digest(row)
    return row


def baseline() -> list[dict[str, Any]]:
    return [
        evidence_row("ev-scope", "scope", "scope-contract"),
        evidence_row("ev-protocol", "protocol", "protocol-monitor"),
        evidence_row("ev-freshness", "freshness", "observation-ledger"),
        evidence_row("ev-causality", "causal_attribution", "effect-oracle"),
        evidence_row("ev-release", "release", "release-receipt"),
        evidence_row("ev-effect-a", "effect", "effect-oracle-a"),
        evidence_row("ev-effect-b", "effect", "effect-oracle-b"),
    ]


def scenarios() -> dict[str, dict[str, Any]]:
    clean = baseline()
    stale = copy.deepcopy(clean)
    stale[0]["source_revision"] = 0
    stale[0]["artifact_sha256"] = evidence_digest(stale[0])

    missing = [row for row in copy.deepcopy(clean) if row["claim"] != "causal_attribution"]
    missing.append(evidence_row("ev-unrelated", "UNRELATED", "memo"))

    correlated = copy.deepcopy(clean)
    correlated[5]["independence_domain"] = "shared-model-stack"
    correlated[6]["independence_domain"] = "shared-model-stack"
    correlated[5]["artifact_sha256"] = evidence_digest(correlated[5])
    correlated[6]["artifact_sha256"] = evidence_digest(correlated[6])

    defeater = copy.deepcopy(clean)
    defeater.append(evidence_row("ev-refute", "top", "negative-verifier", polarity="REFUTE", defeats="SAFE_TO_RELEASE"))

    prior_graph = {"revision": 1, "claim": "SAFE_TO_RELEASE", "evidence": copy.deepcopy(clean)}
    prior_digest = canonical_digest(prior_graph)
    successor = copy.deepcopy(clean)
    successor.append(evidence_row("ev-negative-successor", "top", "successor-experiment", revision=2, polarity="REFUTE", defeats="SAFE_TO_RELEASE"))

    return {
        "BASELINE": {"current_revision": 1, "evidence": clean, "history": []},
        "DEPENDENCY_CHANGED": {"current_revision": 2, "evidence": stale, "history": []},
        "MISSING_CAUSALITY": {"current_revision": 1, "evidence": missing, "history": []},
        "CORRELATED_DUPLICATE": {"current_revision": 1, "evidence": correlated, "history": []},
        "DIRECT_DEFEATER": {"current_revision": 1, "evidence": defeater, "history": []},
        "NEGATIVE_SUCCESSOR": {
            "current_revision": 2,
            "evidence": successor,
            "history": [{
                "graph": prior_graph,
                "before_digest": prior_digest,
                "after_digest": canonical_digest(prior_graph),
            }],
        },
    }


def build_raw() -> dict[str, Any]:
    inputs = scenarios()
    rows = []
    for case_id, case in inputs.items():
        for policy in candidate.POLICIES:
            status, reasons = candidate.evaluate(policy, case["evidence"], case["current_revision"])
            rows.append({
                "case_id": case_id,
                "policy": policy,
                "status": status,
                "reasons": reasons,
                "authority_created": False,
                "external_effect_calls": 0,
            })
    return {
        "metadata": {
            "allocation": ALLOCATION,
            "issue": 5332,
            "source_main": SOURCE_MAIN,
            "mode": "host-only-synthetic-t0",
            "container_invocations": 0,
            "network_requests": 0,
            "model_calls": 0,
            "gui_or_input_actions": 0,
            "python": platform.python_version(),
            "system": os.uname().sysname,
            "release": os.uname().release,
            "machine": os.uname().machine,
            "external_effect_calls": 0,
        },
        "top_claim": candidate.TOP_CLAIM,
        "required_subclaims": list(candidate.REQUIRED),
        "effect_independence_minimum": 2,
        "scenario_inputs": inputs,
        "policies": list(candidate.POLICIES),
        "rows": rows,
    }


def main(output_path: str) -> None:
    raw = build_raw()
    Path(output_path).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "allocation": ALLOCATION,
        "status": "RAW_WRITTEN",
        "rows": len(raw["rows"]),
        "scenarios": len(raw["scenario_inputs"]),
        "policies": len(raw["policies"]),
        "raw_path": output_path,
    }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -B runner.py OUTPUT.json")
    main(sys.argv[1])
