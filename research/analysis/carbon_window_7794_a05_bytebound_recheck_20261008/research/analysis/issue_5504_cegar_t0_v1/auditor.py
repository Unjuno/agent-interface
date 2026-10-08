"""Independent raw-only auditor; does not import candidate implementation."""

import hashlib
import json
from pathlib import Path


def load_frozen_cases(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _oracle(case):
    if case.get("well_formed") is not True or case.get("oracle_confidence") != "replayed":
        return "UNKNOWN"
    requirements = ("authority_current", "target_current", "evidence_current", "effect_safe")
    if any(case.get(key) is not True for key in requirements):
        return "REJECT"
    graph = {}
    for before, after in case.get("dependencies", []):
        graph.setdefault(before, []).append(after)
    active, finished = set(), set()

    def cycle(node):
        if node in active:
            return True
        if node in finished:
            return False
        active.add(node)
        found = any(cycle(child) for child in graph.get(node, []))
        active.remove(node)
        finished.add(node)
        return found

    return "REJECT" if any(cycle(node) for node in graph) else "ADMIT"


def _abstract(case, checks):
    if case.get("well_formed") is not True or case.get("oracle_confidence") != "replayed":
        return "UNKNOWN"
    for check in checks:
        if check == "acyclic_dependencies":
            graph = {}
            for before, after in case.get("dependencies", []):
                graph.setdefault(before, []).append(after)
            active, done = set(), set()

            def visit(node):
                if node in active:
                    return False
                if node in done:
                    return True
                active.add(node)
                if not all(visit(child) for child in graph.get(node, [])):
                    return False
                active.remove(node)
                done.add(node)
                return True

            if not all(visit(node) for node in graph):
                return "REJECT"
        elif case.get(check) is not True:
            return "REJECT"
    return "ADMIT"


def audit_result(result, cases):
    errors = []
    if result.get("schema") != "issue5504-cegar-t0-v1":
        errors.append("schema_mismatch")
    expected_cases = {case["case_id"]: (split, case) for split in ("training", "heldout") for case in cases[split]}
    expected_digest = hashlib.sha256(_canonical(cases).encode("utf-8")).hexdigest()
    if result.get("corpus_sha256") != expected_digest:
        errors.append("corpus_digest_mismatch")
    rows = {row.get("case_id"): row for row in result.get("rows", [])}
    if set(rows) != set(expected_cases):
        errors.append("case_inventory_mismatch")
    checks = set(result.get("learned_checks", []))
    over_specific = {"target_current", "authority_current", "evidence_current", "effect_safe", "acyclic_dependencies", "redundant_receipt_attestation", "independent_review_receipt", "clock_sync_attestation"}
    initial = set(result.get("initial_checks", []))
    if initial != {"target_current"}:
        errors.append("initial_abstraction_mismatch")

    # Independently replay the refinement sequence from raw training cases.
    replay_checks = {"target_current"}
    replay_lineage = []
    for case in cases["training"]:
        candidate = _abstract(case, replay_checks)
        expected = _oracle(case)
        if candidate != "ADMIT" or expected != "REJECT":
            continue
        if case.get("well_formed") is not True or case.get("oracle_confidence") != "replayed":
            continue
        omitted_false = [name for name in ("authority_current", "target_current", "evidence_current", "effect_safe", "acyclic_dependencies") if name not in replay_checks and ((name == "acyclic_dependencies" and not _abstract(case, {name}) == "ADMIT") or (name != "acyclic_dependencies" and case.get(name) is False))]
        if len(omitted_false) == 1:
            replay_checks.add(omitted_false[0])
            replay_lineage.append({"case_id": case["case_id"], "added_check": omitted_false[0]})
    if result.get("lineage") != replay_lineage:
        errors.append("refinement_sequence_mismatch")
    if checks != replay_checks:
        errors.append("learned_check_replay_mismatch")
    parent_ids = set()
    lineage_checks = set(initial)
    for event in result.get("lineage", []):
        case_id, check = event.get("case_id"), event.get("added_check")
        parent_ids.add(case_id)
        if case_id not in expected_cases or expected_cases[case_id][0] != "training":
            errors.append("refinement_parent_missing")
            continue
        _, parent = expected_cases[case_id]
        if _oracle(parent) != "REJECT" or parent.get("oracle_confidence") != "replayed":
            errors.append("refinement_parent_not_replayed_rejection")
        if check in lineage_checks:
            errors.append("duplicate_refinement")
        if check == "acyclic_dependencies":
            if not _abstract(parent, {"target_current", "authority_current", "evidence_current", "effect_safe", "acyclic_dependencies"}) == "REJECT":
                errors.append("cycle_refinement_not_reproduced")
        elif parent.get(check) is not False:
            errors.append("refinement_predicate_not_false_in_parent")
        lineage_checks.add(check)
    if checks != lineage_checks:
        errors.append("refinement_lineage_check_mismatch")
    for case_id, (split, case) in expected_cases.items():
        row = rows.get(case_id)
        if row is None:
            continue
        expected_oracle = _oracle(case)
        if row.get("split") != split or row.get("oracle") != expected_oracle:
            errors.append(f"oracle_or_split_mismatch:{case_id}")
        if row.get("coarse") != _abstract(case, {"target_current"}):
            errors.append(f"coarse_mismatch:{case_id}")
        if row.get("cegar") != _abstract(case, checks):
            errors.append(f"cegar_mismatch:{case_id}")
        if row.get("full_oracle") != expected_oracle:
            errors.append(f"full_oracle_mismatch:{case_id}")
        if row.get("over_specific") != _abstract(case, over_specific):
            errors.append(f"over_specific_mismatch:{case_id}")
        if row.get("authority_granted") is not False:
            errors.append(f"authority_claim:{case_id}")

    def metrics(arm, split):
        selected = [rows[case_id] for case_id, (row_split, _) in expected_cases.items() if row_split == split and case_id in rows]
        determinate = [row for row in selected if row.get("oracle") in ("ADMIT", "REJECT")]
        unknown = [row for row in selected if row.get("oracle") == "UNKNOWN"]
        return {
            "false_admissions": sum(row.get(arm) == "ADMIT" and row.get("oracle") == "REJECT" for row in determinate),
            "false_rejections": sum(row.get(arm) == "REJECT" and row.get("oracle") == "ADMIT" for row in determinate),
            "unknown_preserved": sum(row.get(arm) == "UNKNOWN" for row in unknown),
            "unknown_total": len(unknown),
            "authority_grants": sum(bool(row.get("authority_granted")) for row in selected),
        }

    for arm in ("coarse", "cegar", "full_oracle", "over_specific"):
        for split in ("training", "heldout"):
            observed = result.get("comparison", {}).get(arm, {}).get(split)
            if observed != metrics(arm, split):
                errors.append(f"comparison_metric_mismatch:{arm}:{split}")
    expected_counts = {"initial_coarse": 1, "cegar_learned": len(replay_checks), "full_required_ontology": 5, "over_specific_static": 8}
    if result.get("check_counts") != expected_counts:
        errors.append("check_count_mismatch")
    comparison = result.get("comparison", {})
    coarse_heldout = comparison.get("coarse", {}).get("heldout", {})
    cegar_heldout = comparison.get("cegar", {}).get("heldout", {})
    if cegar_heldout.get("false_admissions") != 0 or cegar_heldout.get("false_admissions", 0) >= coarse_heldout.get("false_admissions", 0):
        errors.append("gate_cegar_false_admission_reduction")
    if cegar_heldout.get("false_rejections") != 0:
        errors.append("gate_cegar_false_rejections")
    if cegar_heldout.get("unknown_preserved") != cegar_heldout.get("unknown_total"):
        errors.append("gate_unknown_not_preserved")
    if any(comparison.get(arm, {}).get(split, {}).get("authority_grants") != 0 for arm in ("coarse", "cegar", "full_oracle", "over_specific") for split in ("training", "heldout")):
        errors.append("gate_authority_granted")
    counts = result.get("check_counts", {})
    if counts.get("cegar_learned", 0) >= counts.get("over_specific_static", 0):
        errors.append("gate_no_check_count_reduction")
    return {"decision": "PASS" if not errors else "FAIL", "errors": errors}
