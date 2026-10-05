"""Bounded exhaustive sensitivity analysis using the frozen #6274 certificate."""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import types
from pathlib import Path


HERE = Path(__file__).resolve().parent


def frozen_certificate_source(freeze):
    for relative, expected in freeze["sha256"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"HOLD_FROZEN_FILE_HASH_MISMATCH:{relative}")
    raw = subprocess.run(
        ["git", "show", f"{freeze['source_commit']}:{freeze['source_path']}"],
        cwd=HERE, capture_output=True, check=True,
    ).stdout
    digest = hashlib.sha256(raw).hexdigest()
    if digest != freeze["source_sha256"]:
        raise RuntimeError("HOLD_CERTIFICATE_SOURCE_HASH_MISMATCH")
    module = types.ModuleType("frozen_6274_certificate")
    module.__file__ = str(HERE.parents[2] / freeze["source_path"])
    exec(compile(raw, freeze["source_path"], "exec"), module.__dict__)
    return module


def encode_order(order):
    strict, ties = [], []
    ranks = {route: tier for tier, group in enumerate(order) for route in group}
    routes = sorted(ranks)
    for i, left in enumerate(routes):
        for right in routes[i + 1:]:
            if ranks[left] < ranks[right]:
                strict.append([left, right])
            elif ranks[right] < ranks[left]:
                strict.append([right, left])
            else:
                ties.append([left, right])
    return {"strict": sorted(strict), "ties": sorted(ties)}


def preference_key(pref):
    return json.dumps(pref, sort_keys=True, separators=(",", ":"))


def project_order(order, mask):
    full = encode_order(order)
    allowed = {tuple(sorted(pair)) for pair in itertools.combinations(sorted(mask), 2)}
    return {
        "strict": [pair for pair in full["strict"] if tuple(sorted(pair)) in allowed],
        "ties": [pair for pair in full["ties"] if tuple(sorted(pair)) in allowed],
    }


def report_domain(certificate, fixture):
    routes = sorted(fixture["routes"])
    orders = sorted(tuple(tuple(tier) for tier in order)
                    for order in certificate.ordered_partitions(routes))
    by_key = {}
    for order in orders:
        for mask in fixture["report_masks"]:
            pref = project_order(order, mask)
            key = preference_key(pref)
            label = "full" if len(mask) == len(routes) else ("empty" if not mask else "mask_" + "".join(mask))
            by_key[key] = {"preference": pref, "label": label}
    reports = sorted(by_key.values(), key=lambda row: (row["label"], preference_key(row["preference"])))
    for index, row in enumerate(reports):
        row["report_id"] = f"R{index:02d}"
    return orders, reports


def signature(result):
    profile = result["profile"]
    return {
        "eligible": result["eligible"],
        "excluded_reasons": result["excluded_reasons"],
        "extension_counts_by_principal": profile["extension_counts_by_principal"],
        "completion_count": profile["completion_count"],
        "possible_frontier": profile["possible_frontier"],
        "certain_frontier": profile["certain_frontier"],
        "verified_dominated_by": profile["verified_dominated_by"],
        "verified_undominated": profile["verified_undominated"],
        "unresolved": profile["unresolved"],
        "all_completion_frontiers": profile["all_completion_frontiers"],
        "decision_status": result["decision_status"],
        "delegated_decision_maker": result["delegated_decision_maker"],
        "delegated_choice": result["delegated_choice"],
    }


def case_for(fixture, preferences, decision_maker=None, grants=None, protected=None):
    principals = fixture["principals"]
    all_routes = sorted(fixture["routes"])
    if grants is None:
        grants = {principal: list(all_routes) for principal in principals}
    return {
        "grants": grants,
        "protected_violations": protected or {},
        "decision_maker": decision_maker,
        "preferences": preferences,
    }


def evaluate(certificate, fixture, preferences, decision_maker=None, grants=None, protected=None):
    case = case_for(fixture, preferences, decision_maker, grants, protected)
    local = {**fixture, "cases": {"probe": case}}
    return signature(certificate.evaluate(local, "probe"))


def run():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    certificate = frozen_certificate_source(freeze)
    orders, reports = report_domain(certificate, fixture)
    order_prefs = [encode_order(order) for order in orders]
    full_report_ids = {preference_key(row["preference"]): row["report_id"]
                       for row in reports if row["label"] == "full"}
    principal_count = len(fixture["principals"])
    if principal_count != 2:
        raise RuntimeError("HOLD_UNSUPPORTED_PRINCIPAL_COUNT")
    world_rows, deviations = [], []
    result_cache = {}

    def run_profile(order_indices, reporter, report_id):
        peer = 1 - reporter
        pref_by_principal = [order_prefs[index] for index in order_indices]
        report = next(row for row in reports if row["report_id"] == report_id)
        pref_by_principal[reporter] = report["preference"]
        prefs = dict(zip(fixture["principals"], pref_by_principal, strict=True))
        key = (tuple(order_indices), reporter, report_id)
        if key not in result_cache:
            result_cache[key] = evaluate(certificate, fixture, prefs, fixture["decision_maker"])
        return result_cache[key]

    for order_indices in itertools.product(range(len(orders)), repeat=principal_count):
        world_id = f"O{order_indices[0]:02d}-O{order_indices[1]:02d}"
        signals = {}
        for reporter in range(principal_count):
            peer = 1 - reporter
            peer_order = orders[order_indices[peer]]
            signals[str(reporter)] = project_order(peer_order, fixture["partial_information_mask"])
        world_rows.append({"world_id": world_id, "order_indices": list(order_indices),
                           "partial_signals": signals})
        for reporter in range(principal_count):
            sincere_id = full_report_ids[preference_key(order_prefs[order_indices[reporter]])]
            for report in reports:
                result = run_profile(order_indices, reporter, report["report_id"])
                truthful = run_profile(order_indices, reporter, sincere_id)
                deviations.append({
                    "world_id": world_id,
                    "order_indices": list(order_indices),
                    "reporter": reporter,
                    "report_id": report["report_id"],
                    "sincere_report_id": sincere_id,
                    "is_sincere": report["report_id"] == sincere_id,
                    "certificate": result,
                    "truthful_certificate": truthful,
                    "certificate_changed": result != truthful,
                })

    # Explicit controls exercise authority, unknown comparisons, constraints and decision rights.
    partial_report = {"strict": [["a", "b"]], "ties": []}
    c_top = next(encode_order(order) for order in orders if order[0] == ("c",))
    peer_pref = order_prefs[-1]
    same_order = encode_order((("a",), ("b",), ("c",)))
    controls = {
        "revoked_grant": evaluate(
            certificate, fixture,
            {fixture["principals"][0]: c_top, fixture["principals"][1]: peer_pref},
            fixture["decision_maker"],
            grants={fixture["principals"][0]: ["a", "b", "c"],
                    fixture["principals"][1]: ["a", "b"]},
        ),
        "protected_constraint": evaluate(
            certificate, fixture,
            {fixture["principals"][0]: c_top, fixture["principals"][1]: peer_pref},
            fixture["decision_maker"],
            protected={"c": ["principal_1:protected-record"]},
        ),
        "unknown_comparison": evaluate(
            certificate, fixture,
            {fixture["principals"][0]: partial_report, fixture["principals"][1]: order_prefs[-1]},
            fixture["decision_maker"],
        ),
        "no_decision_right": evaluate(
            certificate, fixture,
            {fixture["principals"][0]: same_order, fixture["principals"][1]: same_order},
            decision_maker=None,
        ),
    }

    result = {
        "schema": "preference-manipulation-7678-t0-candidate-v1",
        "allocation": fixture["allocation"],
        "source_commit": fixture["source_commit"],
        "source_sha256": fixture["source_sha256"],
        "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
        "routes": sorted(fixture["routes"]),
        "principals": fixture["principals"],
        "decision_maker": fixture["decision_maker"],
        "presented_set": fixture["presented_set"],
        "set_utility": fixture["set_utility"],
        "orders": [{"order_id": f"O{i:02d}", "tiers": [list(t) for t in order],
                    "preference": order_prefs[i]} for i, order in enumerate(orders)],
        "reports": reports,
        "worlds": world_rows,
        "deviations": deviations,
        "controls": controls,
        "summary": {
            "complete_weak_orders_per_principal": len(orders),
            "admissible_reports_per_principal": len(reports),
            "truthful_worlds": len(world_rows),
            "unilateral_report_evaluations": len(deviations),
            "frontier_changed_deviations": sum(row["certificate_changed"] for row in deviations),
        "canonical_source_main_invoked": False,
            "canonical_source_evaluate_calls": len(result_cache),
            "legacy_result_directory_written": False,
        },
    }
    out = HERE / "results" / "formal-01" / "candidate-output.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    run()
