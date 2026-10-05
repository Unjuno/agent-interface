"""One-shot four-route manipulation sensitivity candidate for Issue #7678."""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_frozen(path: str, expected: str, source_commit: str):
    raw = subprocess.run(
        ["git", "show", f"{source_commit}:{path}"], cwd=HERE,
        capture_output=True, check=True,
    ).stdout
    if hashlib.sha256(raw).hexdigest() != expected:
        raise RuntimeError("HOLD_CANONICAL_SOURCE_HASH_MISMATCH:" + path)
    module = types.ModuleType("frozen_" + Path(path).stem)
    module.__file__ = str(HERE / ("frozen_" + Path(path).name))
    exec(compile(raw, path, "exec"), module.__dict__)
    return module


def encode(order):
    rank = {route: tier for tier, group in enumerate(order) for route in group}
    strict, ties = [], []
    routes = sorted(rank)
    for left, right in itertools.combinations(routes, 2):
        if rank[left] < rank[right]:
            strict.append([left, right])
        elif rank[right] < rank[left]:
            strict.append([right, left])
        else:
            ties.append([left, right])
    return {"strict": strict, "ties": ties}


def pref_key(pref):
    return json.dumps(pref, sort_keys=True, separators=(",", ":"))


def report_domain(certificate, fixture):
    routes = sorted(fixture["routes"])
    orders = list(certificate.ordered_partitions(routes))
    unique = {}
    for mask in fixture["report_masks"]:
        allowed = {tuple(pair) for pair in itertools.combinations(sorted(mask), 2)}
        label = "full" if len(mask) == len(routes) else ("empty" if not mask else "mask_" + "".join(mask))
        for order in orders:
            full = encode(order)
            pref = {kind: [pair for pair in full[kind]
                           if tuple(sorted(pair)) in allowed]
                    for kind in ("strict", "ties")}
            unique[pref_key(pref)] = {"preference": pref, "label": label}
    reports = sorted(unique.values(), key=lambda row: (
        row["label"], pref_key(row["preference"])))
    for index, row in enumerate(reports):
        row["report_id"] = f"R{index:03d}"
    return orders, reports


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


def make_case(fixture, order_indices, reporter=None, report=None,
              decision_maker="principal_1", grants=None, protected=None):
    prefs = {principal: encode(fixture["truth_orders"][index])
             for principal, index in zip(fixture["principals"], order_indices, strict=True)}
    if reporter is not None:
        prefs[fixture["principals"][reporter]] = report
    if grants is None:
        grants = {principal: sorted(fixture["routes"]) for principal in fixture["principals"]}
    return {"grants": grants, "protected_violations": protected or {},
            "decision_maker": decision_maker, "preferences": prefs}


def run():
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sha256"].items():
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("HOLD_FROZEN_FILE_HASH_MISMATCH:" + name)
    certificate = load_frozen(fixture["candidate_path"], fixture["candidate_sha256"], fixture["source_commit"])
    orders, reports = report_domain(certificate, fixture)
    true_orders = fixture["truth_orders"]
    order_index = {json.dumps(order, separators=(",", ":")): i for i, order in enumerate(true_orders)}
    report_id_by_pref = {pref_key(row["preference"]): row["report_id"] for row in reports}
    cache = {}

    def evaluate(case):
        key = pref_key(case["preferences"])
        if key not in cache:
            local = {**fixture, "cases": {"x": case}}
            cache[key] = signature(certificate.evaluate(local, "x"))
        return cache[key]

    rows = []
    worlds = list(itertools.product(range(len(true_orders)), repeat=2))
    for oi, oj in worlds:
        world_id = f"O{oi:02d}-O{oj:02d}"
        for reporter in range(2):
            own_order_index = (oi, oj)[reporter]
            sincere_pref = encode(true_orders[own_order_index])
            sincere_id = report_id_by_pref[pref_key(sincere_pref)]
            for report_row in reports:
                case_result = evaluate(make_case(fixture, (oi, oj), reporter,
                                                  report_row["preference"]))
                rows.append({
                    "world_id": world_id, "order_indices": [oi, oj],
                    "reporter": reporter, "report_id": report_row["report_id"],
                    "sincere_report_id": sincere_id,
                    "is_sincere": report_row["report_id"] == sincere_id,
                    "certificate": case_result,
                })

    controls = {}
    controls["revoked_grant"] = []
    controls["protected_constraint"] = []
    controls["unknown_comparison"] = []
    for report_row in reports:
        grant_case = make_case(
            fixture, (0, 1), reporter=0, report=report_row["preference"],
            grants={"principal_0": sorted(fixture["routes"]),
                    "principal_1": ["a", "b", "c"]})
        protected_case = make_case(
            fixture, (0, 1), reporter=1, report=report_row["preference"],
            protected={"c": ["principal_0:protected-record"]})
        controls["revoked_grant"].append({"report_id": report_row["report_id"],
                                          "certificate": evaluate(grant_case)})
        controls["protected_constraint"].append({"report_id": report_row["report_id"],
                                                   "certificate": evaluate(protected_case)})
        if report_row["label"] != "full":
            partial = evaluate(make_case(fixture, (0, 1), reporter=0,
                                         report=report_row["preference"]))
            controls["unknown_comparison"].append({"report_id": report_row["report_id"],
                                                     "certificate": partial})
    controls["no_decision_right"] = signature(certificate.evaluate(
        {**fixture, "cases": {"x": make_case(fixture, (0, 1), decision_maker=None)}}, "x"))

    result = {
        "schema": "preference-manipulation-7678-a02-candidate-v1",
        "allocation": fixture["allocation"], "source_commit": fixture["source_commit"],
        "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
        "route_ids": sorted(fixture["routes"]), "truth_order_count": len(true_orders),
        "report_domain": reports, "truth_world_count": len(worlds),
        "expected_deviation_rows": len(worlds) * 2 * len(reports),
        "rows": rows, "controls": controls,
        "summary": {"rows": len(rows), "certificate_changes": sum(
            row["certificate"] != next(r["certificate"] for r in rows
                if r["world_id"] == row["world_id"] and r["reporter"] == row["reporter"]
                and r["is_sincere"]) for row in rows if not row["is_sincere"]),
            "distinct_certificate_evaluations": len(cache),
            "canonical_candidate_invoked": True,
            "legacy_allocation_invoked": False},
    }
    out = HERE / "results" / "a02" / "candidate-output.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    run()
