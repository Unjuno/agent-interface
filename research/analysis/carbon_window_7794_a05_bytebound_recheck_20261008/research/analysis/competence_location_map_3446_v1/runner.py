"""Frozen candidate for the synthetic competence-location routing probe."""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

AGENTS = ("browser", "file", "gui")
PRIORITY = AGENTS
KNOWN = (
    "overlap_browser", "overlap_file", "overlap_gui",
    "replacement_task", "stale_task", "unavailable_task",
)
SCOPES = {agent: set(KNOWN) for agent in AGENTS}
NOW = 100
TTL = 30
MIN_SUPPORT = 2
TRUSTED_SOURCE = "independent_oracle"


def _evidence(stratum: str, family: str, agent: str, version: str,
              score: float, source: str = TRUSTED_SOURCE,
              collected: int = 95, expires: int = 130,
              replicate: int = 0, evidence_index: int = 0) -> dict:
    n = 20
    successes = round(score * n)
    if source == TRUSTED_SOURCE:
        successes = max(0, min(n, successes + (replicate % 3) - 1))
    return {
        "evidence_id": f"{stratum}:r{replicate}:{agent}:{version}:{source}:{evidence_index}",
        "task_family": family,
        "adapter": agent,
        "adapter_version": version,
        "n": n,
        "successes": successes,
        "score": successes / n,
        "source": source,
        "support_episode_ids": [f"support-{stratum}-r{replicate}-{agent}-{i}"
                                for i in range(n)],
        "collected_at": collected,
        "expires_at": expires,
    }


def build_cases() -> list[dict]:
    """Create 7 balanced, authored strata; support and held-out IDs are disjoint."""
    configs = {
        "overlap_browser": ("browser", {}, {
            "browser": [("v1", .95, TRUSTED_SOURCE, 95, 130)],
            "file": [("v1", .55, TRUSTED_SOURCE, 95, 130)],
            "gui": [("v1", .45, TRUSTED_SOURCE, 95, 130)],
        }),
        "overlap_file": ("file", {}, {
            "browser": [("v1", .50, TRUSTED_SOURCE, 95, 130),
                        ("v1", .99, "adapter_self_report", 98, 130)],
            "file": [("v1", .95, TRUSTED_SOURCE, 95, 130)],
            "gui": [("v1", .45, TRUSTED_SOURCE, 95, 130)],
        }),
        "overlap_gui": ("gui", {}, {
            "browser": [("v1", .55, TRUSTED_SOURCE, 95, 130)],
            "file": [("v1", .45, TRUSTED_SOURCE, 95, 130)],
            "gui": [("v1", .95, TRUSTED_SOURCE, 95, 130)],
        }),
        "replacement_task": ("file", {"browser": "v2"}, {
            "browser": [("v1", .99, TRUSTED_SOURCE, 98, 130)],
            "file": [("v1", .90, TRUSTED_SOURCE, 95, 130)],
            "gui": [("v1", .40, TRUSTED_SOURCE, 95, 130)],
        }),
        "stale_task": ("gui", {}, {
            "browser": [("v1", .40, TRUSTED_SOURCE, 95, 130)],
            "file": [("v1", .99, TRUSTED_SOURCE, 60, 90)],
            "gui": [("v1", .90, TRUSTED_SOURCE, 95, 130)],
        }),
        "unavailable_task": ("browser", {}, {
            "browser": [("v1", .90, TRUSTED_SOURCE, 95, 130)],
            "file": [("v1", .40, TRUSTED_SOURCE, 95, 130)],
            "gui": [("v1", .99, TRUSTED_SOURCE, 98, 130)],
        }),
        "novel_mode": (None, {}, {}),
    }
    cases = []
    for stratum, (oracle, version_overrides, evidence_spec) in configs.items():
        family = stratum
        for replicate in range(8):
            versions = {a: version_overrides.get(a, "v1") for a in AGENTS}
            availability = {a: not (stratum == "unavailable_task" and a == "gui")
                            for a in AGENTS}
            records = []
            for agent, specs in evidence_spec.items():
                for evidence_index, (version, score, source, collected, expires) in enumerate(specs):
                    records.append(_evidence(stratum, family, agent, version,
                                             score, source, collected, expires,
                                             replicate, evidence_index))
            cases.append({
                "case_id": f"{stratum}-{replicate:02d}",
                "heldout_episode_id": f"heldout-{stratum}-{replicate:02d}",
                "stratum": stratum,
                "task_family": family,
                "layout_variant": replicate,
                "decision_time": NOW,
                "current_versions": versions,
                "availability": availability,
                "declared_scopes": {a: sorted(SCOPES[a]) for a in AGENTS},
                "evidence": records,
                "oracle_adapter": oracle,
            })
    return cases


def _proposal(policy: str, case: dict) -> tuple[dict | None, str, int]:
    family = case["task_family"]
    evidence = case["evidence"]
    if policy == "STATIC_SCOPE":
        for agent in PRIORITY:
            if family in case["declared_scopes"][agent] and case["availability"][agent]:
                return {"adapter": agent, "version": case["current_versions"][agent],
                        "evidence_id": None}, "DECLARED_SCOPE", 1
        return None, "NO_DECLARED_AVAILABLE_SCOPE", len(AGENTS)
    if policy == "RECENT_SUCCESS_ONLY":
        candidates = sorted(evidence,
                           key=lambda e: (e["score"], e["collected_at"], e["adapter"]),
                           reverse=True)
        if not candidates:
            return None, "NO_SUCCESS_RECORD", 1
        item = candidates[0]
        return {"adapter": item["adapter"], "version": item["adapter_version"],
                "evidence_id": item["evidence_id"]}, "TOP_SUCCESS_RECORD", len(evidence)
    if policy == "VALIDATED_COMPETENCE_MAP":
        scanned = len(evidence)
        candidates = [e for e in evidence
                      if e["task_family"] == family
                      and e["source"] == TRUSTED_SOURCE
                      and e["adapter_version"] == case["current_versions"][e["adapter"]]
                      and e["expires_at"] > case["decision_time"]
                      and case["decision_time"] - e["collected_at"] <= TTL
                      and e["n"] >= MIN_SUPPORT
                      and family in case["declared_scopes"][e["adapter"]]
                      and case["availability"][e["adapter"]]]
        if not candidates:
            return None, "NO_VALID_COMPETENCE_EVIDENCE", scanned + len(evidence) * 6
        item = max(candidates, key=lambda e: (e["score"], e["n"], e["adapter"]))
        return {"adapter": item["adapter"], "version": item["adapter_version"],
                "evidence_id": item["evidence_id"]}, "VALIDATED_MAP", scanned + len(evidence) * 6
    raise ValueError(f"unknown policy: {policy}")


def _admit(case: dict, proposal: dict | None) -> tuple[bool, str]:
    if proposal is None:
        return False, "YIELD_NO_PROPOSAL"
    agent = proposal["adapter"]
    family = case["task_family"]
    if family not in case["declared_scopes"].get(agent, []):
        return False, "SCOPE_MISMATCH"
    if not case["availability"].get(agent, False):
        return False, "ADAPTER_UNAVAILABLE"
    if proposal["version"] != case["current_versions"].get(agent):
        return False, "ADAPTER_VERSION_STALE"
    evidence_id = proposal["evidence_id"]
    if evidence_id is not None:
        item = next((e for e in case["evidence"] if e["evidence_id"] == evidence_id), None)
        if item is None:
            return False, "EVIDENCE_NOT_FOUND"
        if item["source"] != TRUSTED_SOURCE:
            return False, "EVIDENCE_UNTRUSTED"
        if item["expires_at"] <= case["decision_time"]:
            return False, "EVIDENCE_EXPIRED"
        if item["adapter_version"] != case["current_versions"][agent]:
            return False, "EVIDENCE_VERSION_STALE"
    return True, "ADVISORY_ONLY"


def evaluate() -> dict:
    cases = build_cases()
    output = []
    for case in cases:
        support_ids = {x for e in case["evidence"] for x in e["support_episode_ids"]}
        if case["heldout_episode_id"] in support_ids:
            raise AssertionError("support/heldout episode leakage")
        for policy in ("STATIC_SCOPE", "RECENT_SUCCESS_ONLY", "VALIDATED_COMPETENCE_MAP"):
            proposal, selection_reason, work_units = _proposal(policy, case)
            admitted, gate_reason = _admit(case, proposal)
            selected = proposal["adapter"] if admitted and proposal else None
            output.append({
                "case_id": case["case_id"], "stratum": case["stratum"],
                "case_sha256": hashlib.sha256(
                    json.dumps(case, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "policy": policy, "oracle_adapter": case["oracle_adapter"],
                "proposal": proposal, "selection_reason": selection_reason,
                "admitted_advisory_route": admitted, "gate_reason": gate_reason,
                "selected_adapter": selected,
                "exact_location": (selected == case["oracle_adapter"]
                                   if case["oracle_adapter"] is not None else False),
                "required_yield": case["oracle_adapter"] is None,
                "authority_grant": False, "input_emit_count": 0,
                "work_units": work_units,
            })
    return {
        "schema": "competence-location-map-3446-v1",
        "allocation": "competence-location-map-3446-20261001-01",
        "case_count": len(cases), "policy_count": 3,
        "row_count": len(output), "formal_invocations": 1,
        "cases": cases, "rows": output,
    }


if __name__ == "__main__":
    result = evaluate()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if len(sys.argv) == 2:
        Path(sys.argv[1]).write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
