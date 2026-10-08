"""Exact finite decision-compression enumeration for Issue #5329."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROFILES = {
    "OUTCOME_REDUCER": ("outcome",),
    "FRESHNESS_AUDITOR": ("fresh",),
    "EFFECT_ATTRIBUTION": ("fresh", "effect_link", "lineage"),
    "AUTHORITY_ADMISSION": ("fresh", "lineage", "authority", "protocol"),
    "CAUSAL_ATTRIBUTION": ("fresh", "effect_link", "lineage", "causal"),
    "RELEASE_GATE": ("outcome", "fresh", "lineage", "authority", "protocol"),
}
POLICIES = ("LABEL_ONLY", "RAW_TRACE", "FIXED_SUMMARY", "DECISION_SUFFICIENT", "ADVERSARIAL_COMPRESSION")
FIXED_FIELDS = ("outcome", "fresh", "effect_link")


def decide(consumer: str, evidence: dict) -> str:
    required = PROFILES[consumer]
    if any(k not in evidence for k in required):
        return "UNKNOWN"
    if any(evidence[k] is None or evidence[k] == "UNKNOWN" for k in required):
        return "UNKNOWN"
    if consumer == "OUTCOME_REDUCER":
        return evidence["outcome"]
    if consumer == "FRESHNESS_AUDITOR":
        return "FRESH" if evidence["fresh"] else "STALE"
    if consumer == "EFFECT_ATTRIBUTION":
        return "VERIFIED" if all(evidence[k] for k in required) else "NOT_VERIFIED"
    if consumer == "AUTHORITY_ADMISSION":
        return "ADMIT" if evidence["fresh"] and evidence["lineage"] and evidence["authority"] and evidence["protocol"] == "OK" else "DENY"
    if consumer == "CAUSAL_ATTRIBUTION":
        return "SUPPORTED" if (evidence["fresh"] and evidence["effect_link"] and evidence["lineage"] and evidence["causal"] == "SUPPORTED") else "NOT_SUPPORTED"
    if consumer == "RELEASE_GATE":
        if evidence["outcome"] == "FAIL":
            return "FAIL"
        return "PASS" if (evidence["outcome"] == "PASS" and evidence["fresh"] and evidence["lineage"] and evidence["authority"] and evidence["protocol"] == "OK") else "HOLD"
    raise ValueError(consumer)


def representation(policy: str, trace: dict, consumer: str) -> dict:
    req = PROFILES[consumer]
    if policy == "LABEL_ONLY":
        return {"outcome": trace["outcome"], "raw_digest": trace["raw_digest"]}
    if policy == "RAW_TRACE":
        return dict(trace)
    fields = list(FIXED_FIELDS) if policy == "FIXED_SUMMARY" else list(req)
    if policy == "ADVERSARIAL_COMPRESSION":
        fields = list(FIXED_FIELDS)
        removable = sorted(set(req).intersection(fields))
        if removable:
            fields.remove(removable[0])
    summary = {k: trace[k] for k in fields if k in trace}
    summary["raw_digest"] = trace["raw_digest"]
    return summary


def policy_decision(policy: str, consumer: str, trace: dict, summary: dict) -> str:
    if policy == "LABEL_ONLY":
        # Adversarially weak legacy consumer treats a PASS label as sufficient for release.
        if consumer == "RELEASE_GATE":
            return summary["outcome"]
    return decide(consumer, summary)


def run() -> dict:
    traces = json.loads((ROOT / "traces.json").read_text(encoding="utf-8"))["traces"]
    rows = []
    for trace in traces:
        for consumer in PROFILES:
            reference = decide(consumer, trace)
            for policy in POLICIES:
                encoded = representation(policy, trace, consumer)
                observed = policy_decision(policy, consumer, trace, encoded)
                rows.append({
                    "trace": trace["id"], "consumer": consumer, "policy": policy,
                    "reference": reference, "decision": observed,
                    "equivalent": observed == reference,
                    "unsafe_pass": consumer == "RELEASE_GATE" and observed == "PASS" and reference != "PASS",
                    "unknown": observed == "UNKNOWN",
                    "bytes": len(json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode("utf-8")),
                    "fields": sorted(k for k in encoded if k != "raw_digest"),
                })
    summary = {}
    for policy in POLICIES:
        rs = [r for r in rows if r["policy"] == policy]
        summary[policy] = {
            "rows": len(rs), "decision_mismatches": sum(not r["equivalent"] for r in rs),
            "unsafe_passes": sum(r["unsafe_pass"] for r in rs),
            "unknowns": sum(r["unknown"] for r in rs), "bytes": sum(r["bytes"] for r in rs),
        }
    return {"schema": "issue-5329-finite-enumeration-v1", "rows": rows, "summary": summary}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
