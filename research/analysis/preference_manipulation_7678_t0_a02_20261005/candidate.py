from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_certificate():
    path = HERE / "frozen_6274_candidate.py"
    spec = importlib.util.spec_from_file_location("frozen_6274_candidate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen certificate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encode_order(order):
    rank = {item: i for i, tier in enumerate(order) for item in tier}
    names = sorted(rank)
    strict, ties = [], []
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            if rank[left] < rank[right]:
                strict.append([left, right])
            elif rank[right] < rank[left]:
                strict.append([right, left])
            else:
                ties.append([left, right])
    return {"strict": sorted(strict), "ties": sorted(ties)}


def key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def project(order, mask):
    encoded = encode_order(order)
    allowed = {tuple(sorted(pair)) for pair in itertools.combinations(sorted(mask), 2)}
    return {
        "strict": [p for p in encoded["strict"] if tuple(sorted(p)) in allowed],
        "ties": [p for p in encoded["ties"] if tuple(sorted(p)) in allowed],
    }


def signature(result):
    p = result["profile"]
    return {
        "eligible": result["eligible"],
        "excluded_reasons": result["excluded_reasons"],
        "extension_counts_by_principal": p["extension_counts_by_principal"],
        "completion_count": p["completion_count"],
        "possible_frontier": p["possible_frontier"],
        "certain_frontier": p["certain_frontier"],
        "verified_dominated_by": p["verified_dominated_by"],
        "verified_undominated": p["verified_undominated"],
        "unresolved": p["unresolved"],
        "all_completion_frontiers": p["all_completion_frontiers"],
        "decision_status": result["decision_status"],
        "delegated_decision_maker": result["delegated_decision_maker"],
        "delegated_choice": result["delegated_choice"],
    }


def evaluate(cert, fixture, preferences, decision_maker=None, grants=None, protected=None):
    principals = fixture["principals"]
    routes = sorted(fixture["routes"])
    if grants is None:
        grants = {p: list(routes) for p in principals}
    case = {
        "grants": grants,
        "protected_violations": protected or {},
        "decision_maker": decision_maker,
        "preferences": preferences,
    }
    local = {**fixture, "cases": {"probe": case}}
    return signature(cert.evaluate(local, "probe"))


def run(output_path):
    fixture = json.loads((HERE / "fixture.json").read_text())
    cert = load_certificate()
    routes = sorted(fixture["routes"])
    orders = list(cert.ordered_partitions(routes))
    reports_by_key = {}
    for order in orders:
        for mask in fixture["report_masks"]:
            pref = project(order, mask)
            label = "full" if len(mask) == len(routes) else ("empty" if not mask else "mask_" + "".join(mask))
            reports_by_key[key(pref)] = {"preference": pref, "label": label}
    reports = sorted(reports_by_key.values(), key=lambda r: (r["label"], key(r["preference"])))
    for i, row in enumerate(reports):
        row["report_id"] = f"R{i:02d}"
    report_id = {key(r["preference"]): r["report_id"] for r in reports}
    encoded_orders = [encode_order(o) for o in orders]
    cache = {}

    def result(indices, reporter, rid, preference=None):
        cache_key = (indices, reporter, rid)
        if cache_key not in cache:
            prefs = dict(zip(
                fixture["principals"],
                (encoded_orders[i] for i in indices),
                strict=True,
            ))
            prefs[fixture["principals"][reporter]] = (
                preference if preference is not None
                else next(x["preference"] for x in reports if x["report_id"] == rid)
            )
            cache[cache_key] = evaluate(cert, fixture, prefs, fixture["decision_maker"])
        return cache[cache_key]

    worlds, rows = [], []
    for indices in itertools.product(range(len(orders)), repeat=2):
        wid = f"O{indices[0]:02d}-O{indices[1]:02d}"
        signals = {
            str(actor): project(orders[indices[1 - actor]], fixture["partial_information_mask"])
            for actor in range(2)
        }
        worlds.append({"world_id": wid, "order_indices": list(indices), "partial_signals": signals})
        for reporter in range(2):
            sincere = report_id[key(encoded_orders[indices[reporter]])]
            truthful = result(indices, reporter, sincere)
            for report in reports:
                cert_result = result(indices, reporter, report["report_id"])
                rows.append({
                    "world_id": wid,
                    "order_indices": list(indices),
                    "reporter": reporter,
                    "report_id": report["report_id"],
                    "sincere_report_id": sincere,
                    "is_sincere": report["report_id"] == sincere,
                    "certificate": cert_result,
                    "truthful_certificate": truthful,
                    "certificate_changed": cert_result != truthful,
                })

    c_top = next(encode_order(o) for o in orders if o[0] == ("c",))
    peer = encoded_orders[-1]
    same = encode_order((("a",), ("b",), ("c",)))
    controls = {
        "revoked_grant": evaluate(
            cert, fixture, {"principal_0": c_top, "principal_1": peer},
            fixture["decision_maker"],
            {"principal_0": routes, "principal_1": ["a", "b"]},
        ),
        "protected_constraint": evaluate(
            cert, fixture, {"principal_0": c_top, "principal_1": peer},
            fixture["decision_maker"], protected={"c": ["principal_1:protected-record"]},
        ),
        "unknown_comparison": evaluate(
            cert, fixture,
            {"principal_0": {"strict": [["a", "b"]], "ties": []}, "principal_1": peer},
            fixture["decision_maker"],
        ),
        "no_decision_right": evaluate(
            cert, fixture, {"principal_0": same, "principal_1": same}, None
        ),
    }
    payload = {
        "schema": "preference-manipulation-7678-t0-a02-raw-v1",
        "allocation": fixture["allocation"],
        "source_commit": fixture["source_commit"],
        "source_sha256": fixture["source_sha256"],
        "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
        "routes": routes,
        "principals": fixture["principals"],
        "decision_maker": fixture["decision_maker"],
        "presented_set": fixture["presented_set"],
        "set_utility": fixture["set_utility"],
        "orders": [
            {"order_id": f"O{i:02d}", "tiers": [list(t) for t in order], "preference": encoded_orders[i]}
            for i, order in enumerate(orders)
        ],
        "reports": reports,
        "worlds": worlds,
        "deviations": rows,
        "controls": controls,
        "summary": {
            "complete_weak_orders_per_principal": len(orders),
            "admissible_reports_per_principal": len(reports),
            "truthful_worlds": len(worlds),
            "unilateral_report_evaluations": len(rows),
            "frontier_changed_deviations": sum(r["certificate_changed"] for r in rows),
            "frozen_certificate_evaluate_calls": len(cache),
            "canonical_source_main_invoked": False,
            "legacy_result_directory_written": False,
        },
    }
    Path(output_path).write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))


if __name__ == "__main__":
    run(sys.argv[1])
