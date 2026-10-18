from __future__ import annotations

import hashlib
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import oracle

HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def project(preference, mask):
    allowed = {tuple(sorted(pair)) for pair in itertools.combinations(sorted(mask), 2)}
    return {
        "strict": [p for p in preference["strict"] if tuple(sorted(p)) in allowed],
        "ties": [p for p in preference["ties"] if tuple(sorted(p)) in allowed],
    }


def prefs_for(order_rows, indices):
    return {
        f"principal_{i}": order_rows[index]["preference"]
        for i, index in enumerate(indices)
    }


def safe_utility(order_row, certificate):
    rank = {
        route: tier
        for tier, routes in enumerate(order_row["tiers"])
        for route in routes
    }
    frontier = certificate["possible_frontier"]
    if not frontier:
        return None
    return min(rank[route] for route in frontier)


def audit(raw_path, output_path, freeze_path=None):
    fixture = json.loads((HERE / "fixture.json").read_text())
    freeze = json.loads(Path(freeze_path).read_text()) if freeze_path else None
    raw = json.loads(Path(raw_path).read_text())
    errors = []
    add = errors.append
    expected_fixture_hash = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
    expected_source_hash = hashlib.sha256((HERE / "frozen_6274_candidate.py").read_bytes()).hexdigest()
    if raw.get("allocation") != fixture["allocation"]:
        add("allocation mismatch")
    if raw.get("fixture_sha256") != expected_fixture_hash:
        add("fixture digest mismatch")
    if raw.get("source_commit") != fixture["source_commit"] or raw.get("source_sha256") != expected_source_hash:
        add("frozen certificate source identity mismatch")
    if freeze is not None and expected_fixture_hash != freeze["sha256"]["fixture.json"]:
        add("freeze fixture digest mismatch")
    if freeze is not None and expected_source_hash != freeze["sha256"]["frozen_6274_candidate.py"]:
        add("freeze certificate source digest mismatch")

    generated = oracle.weak_orders(fixture["routes"])
    order_rows = raw.get("orders", [])
    indexed_orders = []
    if len(order_rows) != 13 or len({canonical(r.get("tiers")) for r in order_rows}) != 13:
        add("expected exactly 13 unique complete weak orders")
    for i, row in enumerate(order_rows):
        if row.get("order_id") != f"O{i:02d}":
            add(f"order id mismatch at {i}")
        tiers = tuple(tuple(t) for t in row.get("tiers", []))
        if tiers not in generated:
            add(f"non-domain order at index {i}")
        expected_preference = oracle.encoded(tiers)
        if row.get("preference") != expected_preference:
            add(f"order/preference encoding mismatch at {i}")
        indexed_orders.append(tiers)
    if set(indexed_orders) != set(generated):
        add("true-order domain is incomplete")

    report_rows = raw.get("reports", [])
    expected_report_map = {}
    for order in indexed_orders:
        encoded = oracle.encoded(order)
        for mask in fixture["report_masks"]:
            pref = project(encoded, mask)
            label = "full" if len(mask) == len(fixture["routes"]) else ("empty" if not mask else "mask_" + "".join(mask))
            expected_report_map[canonical(pref)] = {"preference": pref, "label": label}
    expected_reports = sorted(
        expected_report_map.values(),
        key=lambda r: (r["label"], canonical(r["preference"])),
    )
    for i, row in enumerate(expected_reports):
        row["report_id"] = f"R{i:02d}"
    if report_rows != expected_reports:
        add("report-domain or report-id mismatch")
    report_by_id = {r["report_id"]: r for r in report_rows}
    full_report_id = {
        canonical(r["preference"]): r["report_id"]
        for r in report_rows if r["label"] == "full"
    }
    if len(report_by_id) != 23 or len(full_report_id) != 13:
        add("report-domain cardinality mismatch")

    worlds = raw.get("worlds", [])
    expected_world_keys = set(itertools.product(range(13), repeat=2))
    world_map = {}
    for world in worlds:
        ids = tuple(world.get("order_indices", []))
        if len(ids) != 2 or ids not in expected_world_keys or ids in world_map:
            add("invalid or duplicate truthful world")
            continue
        expected_id = f"O{ids[0]:02d}-O{ids[1]:02d}"
        expected_signals = {
            str(actor): project(
                oracle.encoded(indexed_orders[ids[1 - actor]]),
                fixture["partial_information_mask"],
            )
            for actor in range(2)
        }
        if world.get("world_id") != expected_id or world.get("partial_signals") != expected_signals:
            add(f"truth-world signal mismatch: {expected_id}")
        world_map[ids] = world
    if set(world_map) != expected_world_keys:
        add("truth-world coverage mismatch")

    deviations = raw.get("deviations", [])
    expected_keys = {
        (profile, reporter, report["report_id"])
        for profile in expected_world_keys
        for reporter in range(2)
        for report in expected_reports
    }
    row_map = {}
    for row in deviations:
        indices = tuple(row.get("order_indices", []))
        key = (indices, row.get("reporter"), row.get("report_id"))
        if key not in expected_keys or key in row_map:
            add("invalid or duplicate deviation row")
            continue
        row_map[key] = row
        reporter = row["reporter"]
        sincere_id = full_report_id[canonical(
            oracle.encoded(indexed_orders[indices[reporter]])
        )]
        if row.get("sincere_report_id") != sincere_id:
            add(f"sincere report mismatch: {key}")
        if row.get("is_sincere") != (row.get("report_id") == sincere_id):
            add(f"sincere flag mismatch: {key}")
        if row.get("world_id") != f"O{indices[0]:02d}-O{indices[1]:02d}":
            add(f"world reference mismatch: {key}")
        preferences = prefs_for(order_rows, indices)
        preferences[f"principal_{reporter}"] = report_by_id[row["report_id"]]["preference"]
        truthful_preferences = prefs_for(order_rows, indices)
        expected_certificate = oracle.signature(
            oracle.certificate(fixture, preferences, fixture["decision_maker"])
        )
        expected_truthful = oracle.signature(
            oracle.certificate(fixture, truthful_preferences, fixture["decision_maker"])
        )
        if row.get("certificate") != expected_certificate:
            add(f"candidate/oracle mismatch: {key}")
        if row.get("truthful_certificate") != expected_truthful:
            add(f"truthful baseline/oracle mismatch: {key}")
        if row.get("certificate_changed") != (expected_certificate != expected_truthful):
            add(f"certificate-change flag mismatch: {key}")
    if set(row_map) != expected_keys:
        add("deviation matrix coverage mismatch")

    c_top = next(oracle.encoded(o) for o in indexed_orders if o[0] == ("c",))
    peer = oracle.encoded(indexed_orders[-1])
    same = oracle.encoded((("a",), ("b",), ("c",)))
    controls_expected = {
        "revoked_grant": oracle.signature(oracle.certificate(
            fixture,
            {"principal_0": c_top, "principal_1": peer},
            fixture["decision_maker"],
            {"principal_0": sorted(fixture["routes"]), "principal_1": ["a", "b"]},
        )),
        "protected_constraint": oracle.signature(oracle.certificate(
            fixture,
            {"principal_0": c_top, "principal_1": peer},
            fixture["decision_maker"],
            protected={"c": ["principal_1:protected-record"]},
        )),
        "unknown_comparison": oracle.signature(oracle.certificate(
            fixture,
            {"principal_0": {"strict": [["a", "b"]], "ties": []}, "principal_1": peer},
            fixture["decision_maker"],
        )),
        "no_decision_right": oracle.signature(oracle.certificate(
            fixture,
            {"principal_0": same, "principal_1": same},
            None,
        )),
    }
    if raw.get("controls") != controls_expected:
        add("control certificates do not match independent oracle")
    control_checks = {
        "revoked_grant": (
            controls_expected["revoked_grant"]["eligible"] == ["a", "b"]
            and any("grant_missing:principal_1" in r for r in controls_expected["revoked_grant"]["excluded_reasons"]["c"])
        ),
        "protected_constraint": (
            controls_expected["protected_constraint"]["eligible"] == ["a", "b"]
            and any("nontradeable" in r for r in controls_expected["protected_constraint"]["excluded_reasons"]["c"])
        ),
        "unknown_comparison": (
            controls_expected["unknown_comparison"]["extension_counts_by_principal"].get("principal_0", 0) > 1
            and bool(controls_expected["unknown_comparison"]["unresolved"])
        ),
        "no_decision_right": (
            controls_expected["no_decision_right"]["delegated_decision_maker"] is None
            and controls_expected["no_decision_right"]["delegated_choice"] is None
            and controls_expected["no_decision_right"]["decision_status"] != "DELEGATED_CHOICE"
        ),
    }
    if not all(control_checks.values()):
        add("one or more negative controls failed")

    full_safe, partial_safe = set(), set()
    partial_contexts = defaultdict(set)
    for indices in expected_world_keys:
        for reporter in range(2):
            peer_order = indexed_orders[indices[1 - reporter]]
            signal = canonical(project(oracle.encoded(peer_order), fixture["partial_information_mask"]))
            partial_contexts[(reporter, indices[reporter], signal)].add(indices[1 - reporter])
            sincere = full_report_id[canonical(oracle.encoded(indexed_orders[indices[reporter]]))]
            baseline_row = row_map.get((indices, reporter, sincere))
            if baseline_row is None:
                continue
            base_u = safe_utility(order_rows[indices[reporter]], baseline_row["truthful_certificate"])
            for report_id in report_by_id:
                if report_id == sincere:
                    continue
                row = row_map.get((indices, reporter, report_id))
                if row is None:
                    continue
                dev_u = safe_utility(order_rows[indices[reporter]], row["certificate"])
                if base_u is not None and dev_u is not None and dev_u <= base_u and dev_u < base_u:
                    full_safe.add((indices, reporter, report_id))

    for (reporter, own_index, signal), peer_indices in partial_contexts.items():
        own_order = order_rows[own_index]
        sincere = full_report_id[canonical(oracle.encoded(indexed_orders[own_index]))]
        for report_id in report_by_id:
            if report_id == sincere:
                continue
            outcomes = []
            for peer_index in sorted(peer_indices):
                indices = (own_index, peer_index) if reporter == 0 else (peer_index, own_index)
                row = row_map.get((indices, reporter, report_id))
                if row is None:
                    continue
                base = row["truthful_certificate"]
                outcomes.append((
                    safe_utility(own_order, row["certificate"]),
                    safe_utility(own_order, base),
                ))
            if outcomes and all(d is not None and t is not None and d <= t for d, t in outcomes) and any(d < t for d, t in outcomes):
                partial_safe.add((reporter, own_index, signal, report_id))

    changed = sum(bool(r.get("certificate_changed")) for r in deviations)
    if changed == 0:
        add("no report-dependent certificate change observed")
    expected_summary = {
        "complete_weak_orders_per_principal": 13,
        "admissible_reports_per_principal": 23,
        "truthful_worlds": 169,
        "unilateral_report_evaluations": 7774,
        "frontier_changed_deviations": changed,
        "frozen_certificate_evaluate_calls": 13 * 13 * 2 * 23,
        "canonical_source_main_invoked": False,
        "legacy_result_directory_written": False,
    }
    if raw.get("summary") != expected_summary:
        add("candidate summary mismatch")
    method_pass = not errors and all(control_checks.values()) and changed > 0
    hypothesis = "SUPPORTED_WITHIN_DECLARED_SYNTHETIC_MODEL" if full_safe or partial_safe else "EXHAUSTIVE_NULL_FOR_DECLARED_SET_UTILITY"
    result = {
        "schema": "preference-manipulation-7678-t0-a02-audit-v1",
        "allocation": fixture["allocation"],
        "disposition": "PASS_METHOD_SCOPED" if method_pass else "FAIL_METHOD",
        "hypothesis_result": hypothesis,
        "candidate_oracle_rows": len(row_map),
        "expected_rows": len(expected_keys),
        "frontier_changed_deviations": changed,
        "full_information_safe_beneficial_count": len(full_safe),
        "partial_information_safe_beneficial_count": len(partial_safe),
        "control_checks": control_checks,
        "errors": errors,
        "scope": "Finite authored preference types and information partitions only; no human behavior, fairness, consent, privacy, legal, or GUI-safety inference.",
    }
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if method_pass else 1


if __name__ == "__main__":
    sys.exit(audit(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
