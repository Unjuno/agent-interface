#!/usr/bin/env python3
"""Independent audit-only check of Issue 8589 A01's preregistered left-only gate."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name):
    return json.loads((SOURCE / name).read_text())

def integer_versions(value):
    return isinstance(value, dict) and all(type(v) is int for v in value.values())

def audit():
    freeze = load("A01_FREEZE.json")
    inputs = load("A01_input.json")
    raw = load("A01_candidate_raw.json")
    # Bind the copied inputs back to the immutable A01 freeze.
    checks = {
        "a01_input_hash_matches_freeze": sha(SOURCE / "A01_input.json").lower() == freeze["frozen_sha256"]["input.json"].lower(),
        "a01_base_matches_audit_base": freeze["base_commit"] == "28b6f0fc0dd3cf6d798d97ee608a409ce773e409",
        "issue_matches": freeze["issue"] == 8589,
        "a01_retry_budget_zero": freeze["retry_budget"] == 0,
    }
    nodes = inputs["base_nodes"]
    node_by_id = {n["id"]: n for n in nodes}
    expected_ids = [n["id"] for n in nodes if n["kind"] not in ("effect", "verify")]
    rows = raw.get("results", [])
    selected = [r for r in rows if r.get("case_id") == "revision_left"]
    aliases = [r for r in rows if r.get("case_id") == "boolean_version_alias"]
    checks["left_case_unique"] = len(selected) == 1
    checks["boolean_alias_case_unique"] = len(aliases) == 1
    if len(selected) == 1:
        case = next(c for c in inputs["cases"] if c["case_id"] == "revision_left")
        plan = selected[0]["plan"]
        versions = case["current_versions"]
        # This is a clean complete left-only change: exact integer versions, only left_cfg differs.
        checks["left_case_complete_provenance"] = case["provenance_complete"] is True
        checks["left_case_versions_are_exact_integers"] = integer_versions(versions)
        changed = [key for key, old in {k: 1 for k in versions}.items() if versions[key] != old]
        checks["left_case_is_only_left_cfg_change"] = changed == ["left_cfg"] and versions["left_cfg"] == 2
        stale_nodes = {n["id"] for n in nodes if any(versions.get(k) != v for k, v in n.get("reads", {}).items())}
        # Close invalidation over data dependencies, then exclude effects/verifications from recomputation.
        invalid = set(stale_nodes)
        grew = True
        while grew:
            grew = False
            for n in nodes:
                if n["id"] not in invalid and any(d in invalid for d in n.get("deps", [])):
                    invalid.add(n["id"]); grew = True
        selective = [n["id"] for n in nodes if n["id"] in invalid and n["kind"] not in ("effect", "verify")]
        earliest = min((i for i, n in enumerate(nodes) if n["id"] in stale_nodes), default=len(nodes))
        suffix = [n["id"] for n in nodes[earliest:] if n["kind"] not in ("effect", "verify")]
        checks["selective_reconstruction_matches_raw"] = plan["recompute"]["SELECTIVE_VALIDITY_RECOVERY"] == selective
        checks["suffix_reconstruction_matches_raw"] = plan["recompute"]["EARLIEST_CONFLICT_SUFFIX"] == suffix
        checks["strict_left_only_advantage"] = len(selective) < len(suffix)
        checks["left_case_no_dispatch"] = plan["dispatch_effects"] == []
        checks["left_case_plan_disposition"] = plan["disposition"] == "PASS_PLAN"
        left_metrics = {"selective_recompute": selective, "suffix_recompute": suffix,
                        "selective_count": len(selective), "suffix_count": len(suffix)}
    else:
        left_metrics = {}
    if len(aliases) == 1:
        alias_case = next(c for c in inputs["cases"] if c["case_id"] == "boolean_version_alias")
        alias_versions = alias_case["current_versions"]
        checks["boolean_alias_rejected_as_integer_generation"] = not integer_versions(alias_versions)
        alias_plan = aliases[0]["plan"]
        checks["alias_not_used_as_discriminator"] = alias_case["case_id"] != "revision_left" and alias_plan["dispatch_effects"] == []
    ok = all(checks.values())
    return {
        "status": "PASS_AUDIT_ONLY_LEFT_GATE" if ok else "FAIL_AUDIT_ONLY_LEFT_GATE",
        "scope": "Independent audit-only confirmation of the frozen A01 left-only complete-schedule strict-advantage gate. Does not rerun A01 candidate or auditor and does not alter A01 records or overall method claim.",
        "checks": checks,
        "left_case": left_metrics,
        "invocation": {"candidate": 0, "a01_auditor": 0, "new_auditor": 1, "retries": 0},
        "source_sha256": {name: sha(SOURCE / name) for name in ("A01_FREEZE.json", "A01_input.json", "A01_candidate_raw.json")},
        "auditor_sha256": sha(ROOT / "auditor.py"),
    }

def main():
    result = audit()
    out = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if len(sys.argv) == 2:
        Path(sys.argv[1]).write_text(out)
    else:
        print(out, end="")
    return 0 if result["status"] == "PASS_AUDIT_ONLY_LEFT_GATE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
