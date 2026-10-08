"""Independent raw-only oracle for the competence-location routing probe."""
from __future__ import annotations

import json
import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENTS = ("browser", "file", "gui")
POLICIES = ("STATIC_SCOPE", "RECENT_SUCCESS_ONLY", "VALIDATED_COMPETENCE_MAP")
TRUSTED = "independent_oracle"
ORACLE_BY_STRATUM = {
    "overlap_browser": "browser", "overlap_file": "file", "overlap_gui": "gui",
    "replacement_task": "file", "stale_task": "gui",
    "unavailable_task": "browser", "novel_mode": None,
}


def expected_truth(case: dict, policy: str) -> tuple[dict | None, str]:
    family = case["task_family"]
    if policy == "STATIC_SCOPE":
        for agent in AGENTS:
            if family in case["declared_scopes"][agent] and case["availability"][agent]:
                return {"adapter": agent, "version": case["current_versions"][agent],
                        "evidence_id": None}, "DECLARED_SCOPE"
        return None, "NO_DECLARED_AVAILABLE_SCOPE"
    evidence = case["evidence"]
    if policy == "RECENT_SUCCESS_ONLY":
        if not evidence:
            return None, "NO_SUCCESS_RECORD"
        selected = sorted(evidence,
                          key=lambda e: (e["score"], e["collected_at"], e["adapter"]),
                          reverse=True)[0]
        return {"adapter": selected["adapter"], "version": selected["adapter_version"],
                "evidence_id": selected["evidence_id"]}, "TOP_SUCCESS_RECORD"
    valid = []
    for item in evidence:
        if item["task_family"] != family or item["source"] != TRUSTED:
            continue
        if item["adapter_version"] != case["current_versions"].get(item["adapter"]):
            continue
        if item["expires_at"] <= case["decision_time"]:
            continue
        if case["decision_time"] - item["collected_at"] > 30 or item["n"] < 2:
            continue
        if family not in case["declared_scopes"].get(item["adapter"], []):
            continue
        if not case["availability"].get(item["adapter"], False):
            continue
        valid.append(item)
    if not valid:
        return None, "NO_VALID_COMPETENCE_EVIDENCE"
    selected = max(valid, key=lambda e: (e["score"], e["n"], e["adapter"]))
    return {"adapter": selected["adapter"], "version": selected["adapter_version"],
            "evidence_id": selected["evidence_id"]}, "VALIDATED_MAP"


def admission(case: dict, proposal: dict | None) -> tuple[bool, str]:
    if proposal is None:
        return False, "YIELD_NO_PROPOSAL"
    agent = proposal["adapter"]
    if case["task_family"] not in case["declared_scopes"].get(agent, []):
        return False, "SCOPE_MISMATCH"
    if not case["availability"].get(agent, False):
        return False, "ADAPTER_UNAVAILABLE"
    if case["current_versions"].get(agent) != proposal["version"]:
        return False, "ADAPTER_VERSION_STALE"
    evidence_ref = proposal["evidence_id"]
    if evidence_ref is not None:
        matched = [e for e in case["evidence"] if e["evidence_id"] == evidence_ref]
        if len(matched) != 1:
            return False, "EVIDENCE_NOT_FOUND"
        evidence = matched[0]
        if evidence["source"] != TRUSTED:
            return False, "EVIDENCE_UNTRUSTED"
        if evidence["expires_at"] <= case["decision_time"]:
            return False, "EVIDENCE_EXPIRED"
        if evidence["adapter_version"] != case["current_versions"].get(agent):
            return False, "EVIDENCE_VERSION_STALE"
    return True, "ADVISORY_ONLY"


def audit(raw: dict) -> dict:
    errors = []
    rows = raw.get("rows")
    cases = raw.get("cases")
    if raw.get("schema") != "competence-location-map-3446-v1":
        errors.append("schema")
    if raw.get("allocation") != "competence-location-map-3446-20261001-01":
        errors.append("allocation")
    if raw.get("case_count") != 56 or raw.get("policy_count") != 3 or raw.get("row_count") != 168:
        errors.append("denominator_header")
    if not isinstance(cases, list) or len(cases) != 56:
        return {"disposition": "STOP_RAW_DENOMINATOR", "errors": errors + ["case_count"]}
    case_by_id = {c.get("case_id"): c for c in cases}
    if len(case_by_id) != 56:
        errors.append("unique_case_inputs")
    if not isinstance(rows, list) or len(rows) != 168:
        return {"disposition": "STOP_RAW_DENOMINATOR", "errors": errors + ["row_count"]}
    by_case: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_case[row.get("case_id")].append(row)
    if len(by_case) != 56:
        errors.append("unique_case_count")
    metric = {p: Counter() for p in POLICIES}
    strata_counts = Counter()
    for case_id, policy_rows in by_case.items():
        if len(policy_rows) != 3 or {r.get("policy") for r in policy_rows} != set(POLICIES):
            errors.append(f"policy_denominator:{case_id}")
            continue
        first = policy_rows[0]
        # Input snapshot must be repeated consistently and is independently reconstructed
        # from the immutable row-level envelope included with every output row.
        case = case_by_id.get(case_id)
        if not isinstance(case, dict):
            errors.append(f"missing_case_input:{case_id}")
            continue
        if case.get("case_id") != case_id:
            errors.append(f"case_identity:{case_id}")
        if case.get("task_family") != case.get("stratum"):
            errors.append(f"family_binding:{case_id}")
        if case.get("oracle_adapter") != ORACLE_BY_STRATUM.get(case.get("stratum"), "__unknown__"):
            errors.append(f"oracle_binding:{case_id}")
        if case.get("layout_variant") not in range(8):
            errors.append(f"variant:{case_id}")
        canonical = json.dumps(case, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        strata_counts[case.get("stratum")] += 1
        support_ids = {x for e in case.get("evidence", []) for x in e.get("support_episode_ids", [])}
        if case.get("heldout_episode_id") in support_ids:
            errors.append(f"episode_leakage:{case_id}")
        for evidence in case.get("evidence", []):
            if (evidence.get("n") != 20
                    or evidence.get("successes") != round(evidence.get("score", -99) * 20)
                    or len(evidence.get("support_episode_ids", [])) != evidence.get("n")):
                errors.append(f"support_summary:{case_id}:{evidence.get('evidence_id')}")
        for row in policy_rows:
            policy = row.get("policy")
            proposal, reason = expected_truth(case, policy)
            accepted, gate = admission(case, proposal)
            selected = proposal["adapter"] if accepted and proposal else None
            expected_work = (sum(1 for _ in AGENTS[:next(
                (i + 1 for i, a in enumerate(AGENTS)
                 if case["task_family"] in case["declared_scopes"].get(a, [])
                 and case["availability"].get(a, False)), len(AGENTS))])
                             if policy == "STATIC_SCOPE" else
                             max(1, len(case["evidence"]))
                             if policy == "RECENT_SUCCESS_ONLY" else
                             len(case["evidence"]) * 7)
            if row.get("case_sha256") != digest:
                errors.append(f"case_binding:{case_id}:{policy}")
            if row.get("work_units") != expected_work:
                errors.append(f"cost_accounting:{case_id}:{policy}")
            truth = case.get("oracle_adapter")
            if row.get("proposal") != proposal or row.get("selection_reason") != reason:
                errors.append(f"proposal:{case_id}:{policy}")
            if row.get("admitted_advisory_route") != accepted or row.get("gate_reason") != gate:
                errors.append(f"admission:{case_id}:{policy}")
            if row.get("selected_adapter") != selected:
                errors.append(f"selection:{case_id}:{policy}")
            exact = selected == truth if truth is not None else False
            if row.get("exact_location") != exact or row.get("required_yield") != (truth is None):
                errors.append(f"outcome:{case_id}:{policy}")
            if row.get("authority_grant") is not False or row.get("input_emit_count") != 0:
                errors.append(f"authority:{case_id}:{policy}")
            metric[policy]["correct_known"] += int(truth is not None and exact)
            metric[policy]["wrong_admitted"] += int(truth is not None and accepted and selected != truth)
            metric[policy]["known_yield"] += int(truth is not None and not accepted)
            metric[policy]["required_yield_recall"] += int(truth is None and not accepted)
            metric[policy]["novel_false_route"] += int(truth is None and accepted)
            metric[policy]["authority_grants"] += int(bool(row.get("authority_grant")))
    if strata_counts != Counter({s: 8 for s in (
        "overlap_browser", "overlap_file", "overlap_gui", "replacement_task",
        "stale_task", "unavailable_task", "novel_mode")}):
        errors.append(f"strata:{dict(strata_counts)}")
    known = {p: metric[p]["correct_known"] for p in POLICIES}
    map_score = known["VALIDATED_COMPETENCE_MAP"]
    if map_score < 39 or any(map_score - known[p] < 10 for p in POLICIES[:2]):
        errors.append("decision_gate_improvement")
    if metric["VALIDATED_COMPETENCE_MAP"]["required_yield_recall"] != 8:
        errors.append("map_required_yield")
    if any(metric[p]["novel_false_route"] or metric[p]["authority_grants"] for p in POLICIES):
        errors.append("safety_gate")
    return {
        "disposition": "PASS_COMPETENCE_LOCATION_MAP_CONSTRUCTION_SCOPED" if not errors
                       else "FAIL_OR_STOP_AUDIT",
        "errors": errors,
        "metrics": {p: dict(metric[p]) for p in POLICIES},
        "decision_gate": {"known_case_count": 48, "map_exact_min": 39,
                          "minimum_margin_over_each_control": 10,
                          "map_required_yields": 8},
        "audited_rows": len(rows),
        "work_units_total": {p: sum(r["work_units"] for r in rows if r["policy"] == p)
                             for p in POLICIES},
    }


def mutation_controls(raw: dict) -> dict:
    mutations = {}
    broken = json.loads(json.dumps(raw))
    target = next(r for r in broken["rows"]
                  if r["policy"] == "VALIDATED_COMPETENCE_MAP"
                  and r["stratum"] == "overlap_file")
    target["selected_adapter"] = "browser"
    mutations["wrong_selected_adapter"] = bool(audit(broken)["errors"])

    broken = json.loads(json.dumps(raw))
    broken["cases"][0]["current_versions"]["browser"] = "tampered"
    mutations["case_identity_without_rehash"] = bool(audit(broken)["errors"])

    broken = json.loads(json.dumps(raw))
    target = next(r for r in broken["rows"] if r["policy"] == "STATIC_SCOPE")
    target["authority_grant"] = True
    mutations["authority_grant"] = bool(audit(broken)["errors"])

    broken = json.loads(json.dumps(raw))
    broken["rows"].pop()
    mutations["missing_row"] = bool(audit(broken)["errors"])
    return mutations


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = audit(raw)
    result["mutation_controls"] = mutation_controls(raw)
    if not all(result["mutation_controls"].values()):
        result["disposition"] = "STOP_AUDITOR_MUTATION_CONTROLS"
        result["errors"].append("auditor_mutation_control_accepted")
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
