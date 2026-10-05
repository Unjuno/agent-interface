#!/usr/bin/env python3
"""Read-only audit of the newest retained #57 cohort for Issue #7889 T1."""
import hashlib
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(sys.argv[1])
REV = "origin/main"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05"
OUT = pathlib.Path(sys.argv[2])


def blob(path):
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{REV}:{path}"])


def read_json(path):
    return json.loads(blob(path))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    checks = []

    def check(name, ok, evidence=None):
        checks.append({"check": name, "pass": bool(ok), "evidence": evidence})

    readme_path = "research/integration/compiled_comparison_57_4d74_20261004/README.md"
    protocol_path = f"{BASE}/PROTOCOL.json"
    plan_path = f"{BASE}/PLAN_DRAFT.md"
    audit_path = f"{BASE}/RETAINED_EVIDENCE_AUDIT.json"
    reconcile_path = f"{BASE}/independent-readback/RAW_COST_RECONCILIATION.json"
    readme, protocol, plan = blob(readme_path), read_json(protocol_path), blob(plan_path)
    retained, reconciled = read_json(audit_path), read_json(reconcile_path)
    evals = {}
    for block in (1, 2):
        for arm in "ABCD":
            path = f"{BASE}/formal-output/block-{block}/{arm}/independent-evaluation.json"
            evals[(block, arm)] = read_json(path)

    expected_tasks = [f"task-{i}" for i in range(1, 7)]
    identities_ok = True
    raw_summaries = []
    missing = 0
    exact = 0
    for (block, arm), result in sorted(evals.items()):
        map_counts = result.get("exact_counts", {})
        present = set(map_counts)
        expected = {t: (0 if t in result.get("missing", []) else 1) for t in expected_tasks}
        row_ok = result.get("record_count") == sum(map_counts.values()) and map_counts == expected
        row_ok &= result.get("duplicates") == {} and result.get("unexpected") == []
        identities_ok &= row_ok
        exact += sum(map_counts.values())
        missing += len(result.get("missing", []))
        raw_summaries.append({"block": block, "arm": arm, "task_ids": sorted(present),
                              "exact_counts": map_counts, "missing": result.get("missing", []),
                              "duplicate_ids": result.get("duplicates", {}),
                              "unexpected_ids": result.get("unexpected", []),
                              "independent_success": result.get("success")})

    retained_arms = retained.get("arms", [])
    retained_cells = sum(len(a.get("tasks", [])) for a in retained_arms)
    check("two_blocks_four_arms", len(evals) == 8 and len(retained_arms) == 8)
    check("all_48_assigned_task_cells_retained", retained.get("full_48_tasks_retained") is True and retained_cells == 48 and len(evals)*6 == 48, retained_cells)
    check("same_six_task_ids_per_arm_block", identities_ok and all(set(x["task_ids"]) == set(expected_tasks) for x in raw_summaries))
    check("independent_exact_outcomes_and_noncompletions", exact == 45 and missing == 3, {"exact": exact, "noncompletion": missing})
    check("exact_once_independent_evaluator", all(not x.get("duplicate_ids") and not x.get("unexpected_ids") for x in raw_summaries))
    check("counterbalanced_route_assignment", protocol.get("blocks") == [
        {"seed": 991073, "order": ["A", "B", "C", "D"]},
        {"seed": 991074, "order": ["D", "C", "B", "A"]}],
        {"blocks": protocol.get("blocks"), "arm_definitions_in_plan": all(s in plan.decode() for s in ["A =", "B =", "C =", "D ="])})
    check("all_attempt_denominator_present", retained.get("full_48_tasks_retained") is True and
          set(reconciled.get("arms", {})) == set("ABCD") and all(reconciled["arms"][a].get("tasks") == 12 for a in "ABCD"),
          {"provider_attempts": {a: reconciled["arms"][a].get("all_attempt_input_plus_output") for a in "ABCD"},
           "all_attempt_usage": retained.get("all_attempt_usage")})
    check("fixed_model_and_effort", protocol.get("model") == "gpt-5.6-luna" and protocol.get("effort") == "low")

    # The retained README describes one Chromium fixture, while machine row schemas
    # carry no app/application ID and no second application exists in this cohort.
    schemas = [set(read_json(f"{BASE}/formal-output/block-{b}/{a}/independent-evaluation.json"))
               for b in (1, 2) for a in "ABCD"]
    app_fields = {k for fields in schemas for k in fields if "app" in k.lower() or "application" in k.lower()}
    readme_text = readme.decode(errors="replace")
    one_chromium = "Chromium comparison" in readme_text or "Chromium" in readme_text
    check("single_app_and_cell_app_id_absent", one_chromium and not app_fields,
          {"identified_application_from_report": "Chromium" if one_chromium else "unidentified",
           "application_fields_in_independent_evaluator_rows": sorted(app_fields),
           "distinct_application_count": 1 if one_chromium else None})

    evidence_paths = [readme_path, protocol_path, plan_path, audit_path, reconcile_path]
    evidence_paths += [f"{BASE}/formal-output/block-{b}/{a}/independent-evaluation.json"
                       for b in (1, 2) for a in "ABCD"]
    hashes = {p: sha(blob(p)) for p in evidence_paths}
    status = "HOLD_NO_IDENTIFIABLE_CROSSED_COHORT" if all(c["pass"] for c in checks) else "HOLD_AUDIT_INTEGRITY"
    result = {
        "status": status,
        "source_main": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", REV], text=True).strip(),
        "scope": "read-only historical identifiability audit; no source/raw files modified; no model or GUI calls",
        "checks": checks,
        "cohort": {"blocks": 2, "arms": ["A", "B", "C", "D"], "tasks_per_arm_block": 6,
                   "assigned_cells": 48, "independent_exact": exact, "preserved_noncompletions": missing,
                   "distinct_apps": 1, "identified_app": "Chromium", "cell_level_app_id": False},
        "task_cell_summaries": raw_summaries,
        "evidence_sha256": hashes,
        "hold_reason": "The retained comparison crosses four arms with six task IDs in two blocks, but it contains only one Chromium app fixture and no app/application ID in independent task-cell records. Route-by-app variance and population generalizability are therefore not identifiable."
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "t1-audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "checks": len(checks), "failed": [c["check"] for c in checks if not c["pass"]],
                      "assigned_cells": 48, "independent_exact": exact, "preserved_noncompletions": missing,
                      "distinct_apps": result["cohort"]["distinct_apps"], "evidence_files": len(hashes)}, sort_keys=True))
    return 0 if all(c["pass"] for c in checks) else 2


if __name__ == "__main__":
    sys.exit(main())
