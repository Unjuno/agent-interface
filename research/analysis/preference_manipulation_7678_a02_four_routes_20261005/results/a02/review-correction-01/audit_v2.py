"""Independent rank-vector audit for the four-route #7678 A02 allocation."""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import types
from pathlib import Path

HERE = Path(__file__).resolve().parents[3]


def load_oracle(fixture):
    raw = subprocess.run(
        ["git", "show", f"{fixture['source_commit']}:{fixture['auditor_path']}"],
        cwd=HERE, capture_output=True, check=True,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != fixture["auditor_sha256"]:
        raise RuntimeError("HOLD_FROZEN_ORACLE_HASH_MISMATCH")
    module = types.ModuleType("frozen_independent_6274_oracle")
    module.__file__ = str(HERE / fixture["auditor_path"])
    exec(compile(raw, fixture["auditor_path"], "exec"), module.__dict__)
    return module


def all_rank_maps(options):
    """Enumerate distinct weak orders by rank-vector normalization."""
    options = tuple(sorted(options))
    maps = {}
    for vector in itertools.product(range(len(options)), repeat=len(options)):
        levels = {value: index for index, value in enumerate(sorted(set(vector)))}
        rank = {route: levels[vector[index]] for index, route in enumerate(options)}
        maps[tuple(rank[route] for route in options)] = rank
    return [maps[key] for key in sorted(maps)]


def relation(rank, mask):
    strict, ties = [], []
    for a, b in itertools.combinations(sorted(mask), 2):
        if rank[a] < rank[b]:
            strict.append([a, b])
        elif rank[b] < rank[a]:
            strict.append([b, a])
        else:
            ties.append([a, b])
    return {"strict": strict, "ties": ties}


def key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def independent_report_domain(fixture):
    options = sorted(fixture["routes"])
    unique = {}
    # Construct reports from independent normalized rank vectors, then erase
    # comparisons outside each declared mask.
    for mask in fixture["report_masks"]:
        label = "full" if len(mask) == len(options) else ("empty" if not mask else "mask_" + "".join(mask))
        for ranking in all_rank_maps(options):
            projected = relation(ranking, mask)
            unique[key(projected)] = {"preference": projected, "label": label}
    result = sorted(unique.values(), key=lambda row: (row["label"], key(row["preference"])))
    for index, row in enumerate(result):
        row["report_id"] = f"R{index:03d}"
    return result


def order_rank(order):
    return {route: tier for tier, group in enumerate(order) for route in group}


def make_case(fixture, order_indices, reporter=None, report=None,
              decision_maker="principal_1", grants=None, protected=None):
    preferences = {
        principal: relation(order_rank(fixture["truth_orders"][index]), sorted(fixture["routes"]))
        for principal, index in zip(fixture["principals"], order_indices, strict=True)
    }
    if reporter is not None:
        preferences[fixture["principals"][reporter]] = report
    if grants is None:
        grants = {principal: sorted(fixture["routes"]) for principal in fixture["principals"]}
    return {"grants": grants, "protected_violations": protected or {},
            "decision_maker": decision_maker, "preferences": preferences}


def signature(result):
    p = result["profile"]
    return {
        "eligible": result["eligible"],
        "excluded_reasons": result["excluded_reasons"],
        "completion_count": p["completion_count"],
        "extension_counts_by_principal": p["extension_counts_by_principal"],
        "possible_frontier": p["possible_frontier"],
        "certain_frontier": p["certain_frontier"],
        "verified_dominated_by": p["verified_dominated_by"],
        "verified_undominated": p["verified_undominated"],
        "unresolved": p["unresolved"],
        "decision_status": result["decision_status"],
        "delegated_decision_maker": result["delegated_decision_maker"],
        "delegated_choice": result["delegated_choice"],
    }


def set_utility(certificate, order):
    ranks = order_rank(order)
    frontier = certificate["possible_frontier"]
    return min((ranks[route] for route in frontier), default=None)


def signal(order, mask):
    return key(relation(order_rank(order), mask))


def safe_benefits(fixture, reports, matrix, info_mask):
    """Check one report per information cell under the frozen ordinal set utility."""
    report_ids = [row["report_id"] for row in reports]
    report_for_pref = {key(row["preference"]): row["report_id"] for row in reports}
    counts = {"information_cells": 0, "safe_beneficial_report_cells": 0}
    examples = []
    for reporter in range(2):
        peer = 1 - reporter
        for own_index, own_order in enumerate(fixture["truth_orders"]):
            groups = {}
            for peer_index, peer_order in enumerate(fixture["truth_orders"]):
                sig = "full:" + str(peer_index) if info_mask is None else "partial:" + signal(peer_order, info_mask)
                groups.setdefault(sig, []).append(peer_index)
            for sig, peers in sorted(groups.items()):
                counts["information_cells"] += 1
                truthful_pref = relation(order_rank(own_order), sorted(fixture["routes"]))
                sincere_id = report_for_pref[key(truthful_pref)]
                base = [set_utility(matrix[(tuple((own_index, peer_index) if reporter == 0
                                                   else (peer_index, own_index)), reporter, sincere_id)], own_order)
                        for peer_index in peers]
                for report_id in report_ids:
                    if report_id == sincere_id:
                        continue
                    deviating = [set_utility(matrix[(tuple((own_index, peer_index) if reporter == 0
                                                           else (peer_index, own_index)), reporter, report_id)], own_order)
                                 for peer_index in peers]
                    if any(value is None for value in base + deviating):
                        continue
                    if all(new <= old for new, old in zip(deviating, base, strict=True)) and any(
                            new < old for new, old in zip(deviating, base, strict=True)):
                        counts["safe_beneficial_report_cells"] += 1
                        if len(examples) < 8:
                            examples.append({"reporter": reporter, "own_order_index": own_index,
                                             "information_cell": sig, "peer_indices": peers,
                                             "sincere_report_id": sincere_id,
                                             "deviation_report_id": report_id,
                                             "truthful_utilities": base,
                                             "deviation_utilities": deviating})
    return {**counts, "examples": examples}


def audit():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sha256"].items():
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("HOLD_FROZEN_FILE_HASH_MISMATCH:" + name)
    candidate = json.loads((HERE / "results" / "a02" / "candidate-output.json").read_text(encoding="utf-8"))
    oracle = load_oracle(fixture)
    reports = independent_report_domain(fixture)
    errors = []
    if candidate.get("schema") != "preference-manipulation-7678-a02-candidate-v1":
        errors.append("candidate schema mismatch")
    if candidate.get("report_domain") != reports:
        errors.append("candidate report domain differs from rank-vector reconstruction")
    expected_rows = len(fixture["truth_orders"]) ** 2 * 2 * len(reports)
    expected_keys = set()
    actual_keys = set()
    row_map = {}
    for oi, oj in itertools.product(range(len(fixture["truth_orders"])), repeat=2):
        for reporter in range(2):
            own_index = (oi, oj)[reporter]
            sincere = relation(order_rank(fixture["truth_orders"][own_index]), sorted(fixture["routes"]))
            sincere_id = next(row["report_id"] for row in reports if row["preference"] == sincere)
            for report in reports:
                world_id = f"O{oi:02d}-O{oj:02d}"
                row_key = (world_id, reporter, report["report_id"])
                expected_keys.add(row_key)
                case = make_case(fixture, (oi, oj), reporter, report["preference"])
                expected_signature = signature(oracle.evaluate(
                    {**fixture, "cases": {"x": case}}, "x"))
                actual_keys.add(row_key)
                candidate_row = next((item for item in candidate.get("rows", [])
                                      if (item.get("world_id"), item.get("reporter"),
                                          item.get("report_id")) == row_key), None)
                if candidate_row is None:
                    errors.append("missing candidate row:" + repr(row_key))
                    continue
                row_map[row_key] = expected_signature
                if candidate_row.get("sincere_report_id") != sincere_id:
                    errors.append("sincere report mismatch:" + repr(row_key))
                if candidate_row.get("is_sincere") != (report["report_id"] == sincere_id):
                    errors.append("sincerity flag mismatch:" + repr(row_key))
                if candidate_row.get("certificate") != expected_signature:
                    errors.append("certificate mismatch:" + repr(row_key))
    if len(candidate.get("rows", [])) != expected_rows:
        errors.append("candidate row count mismatch")
    candidate_keys = [(r.get("world_id"), r.get("reporter"), r.get("report_id"))
                      for r in candidate.get("rows", [])]
    if len(candidate_keys) != len(set(candidate_keys)):
        errors.append("duplicate candidate row key")
    if actual_keys != expected_keys:
        errors.append("row coverage mismatch")

    def oracle_case(case):
        return signature(oracle.evaluate({**fixture, "cases": {"x": case}}, "x"))

    control_results = {"revoked_grant": [], "protected_constraint": [], "unknown_comparison": []}
    for report in reports:
        revoked = make_case(fixture, (0, 1), 0, report["preference"],
                            grants={"principal_0": sorted(fixture["routes"]),
                                    "principal_1": ["a", "b", "c"]})
        protected = make_case(fixture, (0, 1), 1, report["preference"],
                              protected={"c": ["principal_0:protected-record"]})
        control_results["revoked_grant"].append({"report_id": report["report_id"],
                                                  "certificate": oracle_case(revoked)})
        control_results["protected_constraint"].append({"report_id": report["report_id"],
                                                       "certificate": oracle_case(protected)})
        if report["label"] != "full":
            partial = oracle_case(make_case(fixture, (0, 1), 0, report["preference"]))
            control_results["unknown_comparison"].append({"report_id": report["report_id"],
                                                          "certificate": partial})
    no_right = oracle_case(make_case(fixture, (0, 1), decision_maker=None))
    if candidate.get("controls", {}).get("revoked_grant") != control_results["revoked_grant"]:
        errors.append("revoked-grant control mismatch")
    if candidate.get("controls", {}).get("protected_constraint") != control_results["protected_constraint"]:
        errors.append("protected-constraint control mismatch")
    if candidate.get("controls", {}).get("unknown_comparison") != control_results["unknown_comparison"]:
        errors.append("unknown-comparison control mismatch")
    if candidate.get("controls", {}).get("no_decision_right") != no_right:
        errors.append("no-decision-right control mismatch")
    if any("d" in row["certificate"]["eligible"] for row in control_results["revoked_grant"]):
        errors.append("revoked route became eligible")
    if any("c" in row["certificate"]["eligible"] for row in control_results["protected_constraint"]):
        errors.append("protected route became eligible")
    if any(row["certificate"]["extension_counts_by_principal"].get("principal_0", 0) <= 1
           for row in control_results["unknown_comparison"]):
        errors.append("an incomplete report collapsed to one completion")
    if no_right["delegated_choice"] is not None or no_right["decision_status"] == "DELEGATED_CHOICE":
        errors.append("missing decision right created a choice")

    certificate_changes = 0
    safe_utility_by_full = safe_benefits(fixture, reports, row_map, None)
    safe_utility_by_partial = safe_benefits(fixture, reports, row_map,
                                            fixture["partial_information_mask"])
    sincere_by_world_reporter = {}
    for row in candidate["rows"]:
        if row["is_sincere"]:
            sincere_by_world_reporter[(row["world_id"], row["reporter"])] = row["certificate"]
    for row in candidate["rows"]:
        if not row["is_sincere"] and row["certificate"] != sincere_by_world_reporter[
                (row["world_id"], row["reporter"])]:
            certificate_changes += 1
    if certificate_changes == 0:
        errors.append("report-sensitivity guard not exercised")
    if candidate.get("summary", {}).get("rows") != expected_rows:
        errors.append("candidate summary row count mismatch")
    summary = {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "truth_types": len(fixture["truth_orders"]),
        "report_types": len(reports),
        "truth_worlds": len(fixture["truth_orders"]) ** 2,
        "unilateral_deviation_rows": expected_rows,
        "candidate_rows_exactly_reconstructed": len(errors) == 0,
        "certificate_changed_deviations": certificate_changes,
        "safe_benefits_full_information": safe_utility_by_full,
        "safe_benefits_partial_information": safe_utility_by_partial,
        "control_counts": {name: len(rows) for name, rows in control_results.items()},
        "revoked_route_excluded_all_reports": all(
            "d" not in row["certificate"]["eligible"] for row in control_results["revoked_grant"]),
        "protected_route_excluded_all_reports": all(
            "c" not in row["certificate"]["eligible"] for row in control_results["protected_constraint"]),
        "incomplete_reports_preserve_multiple_completions": all(
            row["certificate"]["extension_counts_by_principal"].get("principal_0", 0) > 1
            for row in control_results["unknown_comparison"]),
        "no_decision_right_selects_nothing": no_right["delegated_choice"] is None,
        "formal_allocation_a01_modified": False,
    }
    (HERE / "results" / "a02" / "review-correction-01" / "AUDIT.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "errors": errors,
                      "rows": expected_rows,
                      "certificate_changed_deviations": certificate_changes,
                      "safe_benefits_full": safe_utility_by_full["safe_beneficial_report_cells"],
                      "safe_benefits_partial": safe_utility_by_partial["safe_beneficial_report_cells"]},
                     sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    audit()
