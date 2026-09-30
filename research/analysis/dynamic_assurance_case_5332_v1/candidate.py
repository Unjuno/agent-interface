"""Candidate assurance-case policies for the bounded Issue #5332 T0."""

from __future__ import annotations

from typing import Any

TOP_CLAIM = "SAFE_TO_RELEASE"
REQUIRED = ("scope", "protocol", "freshness", "causal_attribution", "release")
POLICIES = (
    "FLAT_RECEIPTS",
    "STATIC_CASE",
    "DYNAMIC_CASE",
    "DEFEATER_AWARE",
    "INDEPENDENCE_AWARE",
    "COMPOSITE_DYNAMIC_CASE",
)


def positive(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in evidence if row["polarity"] == "SUPPORT"]


def covered_claims(evidence: list[dict[str, Any]]) -> set[str]:
    return {row["claim"] for row in positive(evidence) if row["claim"] != "UNRELATED"}


def static_result(evidence: list[dict[str, Any]]) -> tuple[str, list[str]]:
    covered = covered_claims(evidence)
    missing = sorted((set(REQUIRED) | {"effect"}) - covered)
    return ("PARTIAL", [f"MISSING:{claim}" for claim in missing]) if missing else ("SUPPORTED", [])


def dynamic_result(
    evidence: list[dict[str, Any]], current_revision: int
) -> tuple[str, list[str]]:
    status, reasons = static_result(evidence)
    if status != "SUPPORTED":
        return status, reasons
    stale = sorted(
        row["evidence_id"]
        for row in positive(evidence)
        if row["claim"] != "UNRELATED" and row["source_revision"] != current_revision
    )
    return ("STALE", [f"STALE:{item}" for item in stale]) if stale else ("SUPPORTED", [])


def effect_domains(evidence: list[dict[str, Any]], current_revision: int) -> set[str]:
    return {
        row["independence_domain"]
        for row in positive(evidence)
        if row["claim"] == "effect" and row["source_revision"] == current_revision
    }


def has_current_defeater(evidence: list[dict[str, Any]], current_revision: int) -> bool:
    return any(
        row["polarity"] == "REFUTE"
        and row["defeats"] == TOP_CLAIM
        and row["source_revision"] == current_revision
        for row in evidence
    )


def evaluate(
    policy: str, evidence: list[dict[str, Any]], current_revision: int
) -> tuple[str, list[str]]:
    if policy == "FLAT_RECEIPTS":
        if len(positive(evidence)) >= 7:
            return "SUPPORTED", ["POSITIVE_RECEIPT_COUNT>=7"]
        return "PARTIAL", ["POSITIVE_RECEIPT_COUNT<7"]
    if policy == "STATIC_CASE":
        return static_result(evidence)
    dynamic_status, dynamic_reasons = dynamic_result(evidence, current_revision)
    if policy == "DYNAMIC_CASE":
        return dynamic_status, dynamic_reasons
    if policy == "DEFEATER_AWARE":
        if dynamic_status != "SUPPORTED":
            return dynamic_status, dynamic_reasons
        if has_current_defeater(evidence, current_revision):
            return "CONFLICTED", ["CURRENT_DEFEATER"]
        return "SUPPORTED", []
    if policy == "INDEPENDENCE_AWARE":
        if dynamic_status != "SUPPORTED":
            return dynamic_status, dynamic_reasons
        domains = effect_domains(evidence, current_revision)
        if len(domains) < 2:
            return "PARTIAL", ["EFFECT_INDEPENDENCE_LT_2"]
        return "SUPPORTED", []
    if policy == "COMPOSITE_DYNAMIC_CASE":
        if dynamic_status != "SUPPORTED":
            return dynamic_status, dynamic_reasons
        if has_current_defeater(evidence, current_revision):
            return "CONFLICTED", ["CURRENT_DEFEATER"]
        if len(effect_domains(evidence, current_revision)) < 2:
            return "PARTIAL", ["EFFECT_INDEPENDENCE_LT_2"]
        return "SUPPORTED", []
    raise ValueError(f"unknown policy: {policy}")
