#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #7409 T0."""
import copy
import json
import sys


def merge(document, values):
    merged = copy.deepcopy(document)
    for key in values:
        merged[key] = copy.deepcopy(values[key])
    return merged


def next_revision(revision):
    return f"r{int(revision[1:]) + 1}"


def expected(case):
    original = copy.deepcopy(case["base"])
    human_values = case["human"]["writes"]
    agent_values = case["agent"]["writes"]
    human_revision = case["human"].get("revision_after_commit", "r1")
    after_human = merge(original, human_values)
    direct_final = merge(after_human, agent_values)
    direct = {
        "final": direct_final,
        "revision": next_revision(human_revision),
        "agent_writes_reached_live_before_completion": bool(agent_values),
        "external_effects": copy.deepcopy(case["agent"]["external_effects"]),
        "status": "DIRECT_COMMITTED",
    }
    app = case["app"]
    eligible = app["versioned_draft"] and app["draft_backend_isolated"] and app["no_external_effects"] and not case["agent"]["external_effects"]
    if not eligible:
        reason = "SHARED_BACKEND" if not app["draft_backend_isolated"] else "EXTERNAL_EFFECT"
        staged = {
            "status": "REFUSED_ELIGIBILITY", "reason": reason, "draft_created": False, "draft": None,
            "live_after_draft_write": after_human, "live_revision_after_draft_write": human_revision,
            "live_after_human_commit": after_human, "final": after_human, "final_revision": human_revision,
            "revision_checked": False, "conflicts": [], "promoted": False, "external_effects": [],
            "events": ["HUMAN_COMMIT", "REFUSED_BEFORE_DRAFT"],
        }
        return {"case_id": case["id"], "direct": direct, "staged": staged}

    draft = merge(original, agent_values)
    reads = case["agent"]["reads"]
    changed_by_human = set(human_values)
    affected_by_agent = set(agent_values) | set(reads)
    collision = sorted(changed_by_human & affected_by_agent)
    if collision:
        staged = {
            "status": "CONFLICT_HOLD", "reason": "OVERLAPPING_READ_OR_WRITE", "draft_created": True, "draft": draft,
            "live_after_draft_write": original, "live_revision_after_draft_write": "r0",
            "live_after_human_commit": after_human, "final": after_human, "final_revision": human_revision,
            "revision_checked": True, "conflicts": collision, "promoted": False, "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "CONFLICT_SURFACED"],
        }
    elif not app["explicit_promotion"]:
        staged = {
            "status": "HOLD_PROMOTION_NOT_AUTHORIZED", "reason": "NO_EXPLICIT_PROMOTION", "draft_created": True, "draft": draft,
            "live_after_draft_write": original, "live_revision_after_draft_write": "r0",
            "live_after_human_commit": after_human, "final": after_human, "final_revision": "r1",
            "revision_checked": True, "conflicts": [], "promoted": False, "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "PROMOTION_HELD"],
        }
    else:
        promoted = merge(after_human, agent_values)
        staged = {
            "status": "PROMOTED", "reason": "DISJOINT_REVISION_MERGED", "draft_created": True, "draft": draft,
            "live_after_draft_write": original, "live_revision_after_draft_write": "r0",
            "live_after_human_commit": after_human, "final": promoted, "final_revision": next_revision(human_revision),
            "revision_checked": True, "conflicts": [], "promoted": True, "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "EXPLICIT_PROMOTION"],
        }
    return {"case_id": case["id"], "direct": direct, "staged": staged}


def audit(cases, candidate):
    errors = []
    if candidate.get("schema") != "issue-7409-t0-candidate-v1":
        errors.append("schema mismatch")
    actual_rows = candidate.get("rows", [])
    if len(actual_rows) != len(cases):
        errors.append("row count mismatch")
    expected_rows = [expected(case) for case in cases]
    for index, want in enumerate(expected_rows):
        if index >= len(actual_rows):
            break
        if actual_rows[index] != want:
            errors.append(f"row {index} differs from independent reconstruction")
    if [case["id"] for case in cases] != [row.get("case_id") for row in actual_rows]:
        errors.append("case order/identity mismatch")
    return errors


def mutation_checks(cases, candidate):
    rejected = {}
    def probe(name, mutate):
        changed = copy.deepcopy(candidate)
        mutate(changed)
        rejected[name] = bool(audit(cases, changed))

    def row_for(data, case_id):
        return next(row for row in data["rows"] if row["case_id"] == case_id)

    probe("premature_live_write", lambda data: row_for(data, "C1-disjoint")["staged"]["live_after_draft_write"].update({"summary": "agent summary"}))
    probe("silent_same_field_overwrite", lambda data: row_for(data, "C2-same-field")["staged"].update({"status": "PROMOTED", "promoted": True}))
    probe("ignored_hidden_dependency", lambda data: row_for(data, "C3-hidden-dependency")["staged"].update({"status": "PROMOTED", "promoted": True, "conflicts": []}))
    probe("unchecked_revision_change", lambda data: row_for(data, "C4-revision-changed-disjoint")["staged"].update({"revision_checked": False}))
    probe("shared_backend_accepted", lambda data: row_for(data, "C5-shared-backend-autosave")["staged"].update({"status": "PROMOTED", "promoted": True, "draft_created": True}))
    probe("external_effect_in_draft", lambda data: row_for(data, "C6-external-side-effect")["staged"].update({"external_effects": ["send-notification"], "status": "PROMOTED", "promoted": True}))
    return rejected


def main():
    input_path, raw_path, output_path = sys.argv[1:4]
    with open(input_path, encoding="utf-8") as stream:
        cases = json.load(stream)
    with open(raw_path, encoding="utf-8") as stream:
        candidate = json.load(stream)
    errors = audit(cases, candidate)
    mutations = mutation_checks(cases, candidate)
    if not all(mutations.values()):
        errors.append("one or more frozen mutations were accepted")
    result = {
        "schema": "issue-7409-t0-audit-v1",
        "disposition": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
        "reconstructed_rows": len(cases),
        "errors": errors,
        "mutation_controls_rejected": sum(mutations.values()),
        "mutation_controls_total": len(mutations),
        "mutations": mutations,
        "scope": "authored deterministic fixture only; no real application, human, model, GUI, product effect, or safety result",
    }
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"disposition": result["disposition"], "errors": errors, "mutation_controls_rejected": result["mutation_controls_rejected"], "mutation_controls_total": result["mutation_controls_total"]}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
