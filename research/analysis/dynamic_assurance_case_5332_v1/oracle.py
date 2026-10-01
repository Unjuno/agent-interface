"""Independent expected-state oracle; does not import candidate policy code."""

from __future__ import annotations

from typing import Any


def expected(policy: str, case: dict[str, Any]) -> tuple[str, list[str]]:
    evidence = case["evidence"]
    current = case["current_revision"]
    support = [row for row in evidence if row["polarity"] == "SUPPORT"]
    claims = {row["claim"] for row in support if row["claim"] != "UNRELATED"}
    needed = {"scope", "protocol", "freshness", "causal_attribution", "release", "effect"}
    absent = sorted(needed - claims)
    current_defeater = any(
        row["polarity"] == "REFUTE"
        and row["defeats"] == "SAFE_TO_RELEASE"
        and row["source_revision"] == current
        for row in evidence
    )
    current_domains = {
        row["independence_domain"]
        for row in support
        if row["claim"] == "effect" and row["source_revision"] == current
    }
    stale_ids = sorted(
        row["evidence_id"]
        for row in support
        if row["claim"] != "UNRELATED" and row["source_revision"] != current
    )

    if policy == "FLAT_RECEIPTS":
        return ("SUPPORTED", ["POSITIVE_RECEIPT_COUNT>=7"]) if len(support) >= 7 else ("PARTIAL", ["POSITIVE_RECEIPT_COUNT<7"])
    if absent:
        return "PARTIAL", [f"MISSING:{item}" for item in absent]
    if policy == "STATIC_CASE":
        return "SUPPORTED", []
    if stale_ids:
        return "STALE", [f"STALE:{item}" for item in stale_ids]
    if policy == "DYNAMIC_CASE":
        return "SUPPORTED", []
    if policy in {"DEFEATER_AWARE", "COMPOSITE_DYNAMIC_CASE"} and current_defeater:
        return "CONFLICTED", ["CURRENT_DEFEATER"]
    if policy in {"INDEPENDENCE_AWARE", "COMPOSITE_DYNAMIC_CASE"} and len(current_domains) < 2:
        return "PARTIAL", ["EFFECT_INDEPENDENCE_LT_2"]
    return "SUPPORTED", []


def top_claim_truth(case: dict[str, Any]) -> tuple[str, list[str]]:
    """Synthetic reference contract for whether this case supports the top claim."""
    evidence = case["evidence"]
    current = case["current_revision"]
    support = [row for row in evidence if row["polarity"] == "SUPPORT"]
    claims = {row["claim"] for row in support if row["claim"] != "UNRELATED"}
    needed = {"scope", "protocol", "freshness", "causal_attribution", "release", "effect"}
    absent = sorted(needed - claims)
    if absent:
        return "PARTIAL", [f"MISSING:{item}" for item in absent]
    stale = sorted(
        row["evidence_id"]
        for row in support
        if row["claim"] != "UNRELATED" and row["source_revision"] != current
    )
    if stale:
        return "STALE", [f"STALE:{item}" for item in stale]
    refuted = any(
        row["polarity"] == "REFUTE"
        and row["defeats"] == "SAFE_TO_RELEASE"
        and row["source_revision"] == current
        for row in evidence
    )
    if refuted:
        return "CONFLICTED", ["CURRENT_DEFEATER"]
    domains = {
        row["independence_domain"]
        for row in support
        if row["claim"] == "effect" and row["source_revision"] == current
    }
    if len(domains) < 2:
        return "PARTIAL", ["EFFECT_INDEPENDENCE_LT_2"]
    return "SUPPORTED", []
