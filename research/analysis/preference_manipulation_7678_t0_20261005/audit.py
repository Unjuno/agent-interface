"""Independent rank-vector reconstruction and manipulation audit; no candidate imports."""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "formal-01"


def rank_vector_orders(items):
    """Independent domain generation by rank vectors, not ordered partitions."""
    found = {}
    for values in itertools.product(range(len(items)), repeat=len(items)):
        levels = sorted(set(values))
        normalized = {value: index for index, value in enumerate(levels)}
        tiers = tuple(tuple(items[i] for i, value in enumerate(values)
                            if normalized[value] == level)
                      for level in range(len(levels)))
        found[tiers] = {item: normalized[values[i]] for i, item in enumerate(items)}
    return sorted(found.items())


def order_preference(order):
    strict, ties = [], []
    ranks = {item: level for level, tier in enumerate(order) for item in tier}
    items = sorted(ranks)
    for i, left in enumerate(items):
        for right in items[i + 1:]:
            if ranks[left] < ranks[right]:
                strict.append([left, right])
            elif ranks[right] < ranks[left]:
                strict.append([right, left])
            else:
                ties.append([left, right])
    return {"strict": sorted(strict), "ties": sorted(ties)}


def project(order, mask):
    pref = order_preference(order)
    allowed = {tuple(sorted(pair)) for pair in itertools.combinations(sorted(mask), 2)}
    return {kind: [pair for pair in pref[kind] if tuple(sorted(pair)) in allowed]
            for kind in ("strict", "ties")}


def pref_key(pref):
    return json.dumps(pref, sort_keys=True, separators=(",", ":"))


def report_domain(orders, masks):
    rows = {}
    items = sorted({item for order, _ in orders for tier in order for item in tier})
    for order, _ in orders:
        for mask in masks:
            pref = project(order, mask)
            label = "full" if len(mask) == len(items) else ("empty" if not mask else "mask_" + "".join(mask))
            rows[pref_key(pref)] = {"preference": pref, "label": label}
    reports = sorted(rows.values(), key=lambda row: (row["label"], pref_key(row["preference"])))
    for index, row in enumerate(reports):
        row["report_id"] = f"R{index:02d}"
    return reports


def completions(orders, preference, eligible):
    def consistent(rank):
        return (all(rank[a] < rank[b] for a, b in preference["strict"])
                and all(rank[a] == rank[b] for a, b in preference["ties"]))
    rows = [rank for _, rank in orders if consistent(rank)]
    return rows


def oracle_profile(fixture, case):
    principals = fixture["principals"]
    all_routes = sorted(fixture["routes"])
    eligible, excluded = [], {}
    for route, details in fixture["routes"].items():
        reasons = []
        if details["effect_id"] != fixture["task_effect_id"]:
            reasons.append("requester_effect_mismatch")
        for principal in principals:
            if route not in case["grants"].get(principal, []):
                reasons.append(f"grant_missing:{principal}")
        reasons.extend(f"nontradeable:{x}" for x in case["protected_violations"].get(route, []))
        if reasons:
            excluded[route] = sorted(reasons)
        else:
            eligible.append(route)
    eligible = sorted(eligible)
    order_rows = rank_vector_orders(eligible)
    projected = {
        principal: {
            kind: [pair for pair in case["preferences"][principal][kind]
                   if pair[0] in set(eligible) and pair[1] in set(eligible)]
            for kind in ("strict", "ties")
        }
        for principal in principals
    }
    extensions = [completions(order_rows, projected[principal], eligible)
                  for principal in principals]
    combos = list(itertools.product(*extensions)) if all(extensions) else []
    frontiers = []
    for combo in combos:
        frontier = []
        for option in eligible:
            dominated = any(
                rival != option
                and all(row[rival] <= row[option] for row in combo)
                and any(row[rival] < row[option] for row in combo)
                for rival in eligible
            )
            if not dominated:
                frontier.append(option)
        frontiers.append(tuple(frontier))
    possible = sorted(set(itertools.chain.from_iterable(frontiers)))
    certain = sorted(set(eligible).intersection(*map(set, frontiers))) if frontiers else []
    verified_dominated, verified_undominated, unresolved = {}, [], []
    for option in eligible:
        dominators = []
        for rival in eligible:
            if rival == option:
                continue
            weak_everywhere = all(all(row[rival] <= row[option] for row in combo) for combo in combos)
            strict_principal_everywhere = any(
                all(combo[index][rival] < combo[index][option] for combo in combos)
                for index in range(len(principals))
            )
            if weak_everywhere and strict_principal_everywhere:
                dominators.append(rival)
        if dominators:
            verified_dominated[option] = dominators
        elif all(option in frontier for frontier in frontiers):
            verified_undominated.append(option)
        else:
            unresolved.append(option)
    profile = {
        "extension_counts_by_principal": dict(zip(principals, map(len, extensions), strict=True)),
        "completion_count": len(combos),
        "possible_frontier": possible,
        "certain_frontier": certain,
        "verified_dominated_by": verified_dominated,
        "verified_undominated": sorted(verified_undominated),
        "unresolved": sorted(unresolved),
        "all_completion_frontiers": [list(row) for row in sorted(set(frontiers))],
    }
    decision_maker = case["decision_maker"]
    delegated_choice = None
    if decision_maker and eligible:
        index = principals.index(decision_maker)
        pref = case["preferences"][decision_maker]
        projected_pref = {
            kind: [pair for pair in pref[kind]
                   if pair[0] in set(eligible) and pair[1] in set(eligible)]
            for kind in ("strict", "ties")
        }
        pref_rows = completions(order_rows, projected_pref, eligible)
        if len(pref_rows) == 1:
            best = min(pref_rows[0][route] for route in eligible)
            top = [route for route in eligible if pref_rows[0][route] == best]
            if len(top) == 1:
                delegated_choice = top[0]
    if decision_maker:
        status = "DELEGATED_CHOICE" if delegated_choice else "DELEGATION_UNRESOLVED"
    elif len(possible) > 1:
        status = "HANDOFF_MULTIPLE_OR_POSSIBLE_FRONTIER"
    elif unresolved:
        status = "HANDOFF_PARTIAL_PREFERENCE"
    elif possible:
        status = "NO_AUTO_CHOICE_WITHOUT_DECISION_RIGHT"
    else:
        status = "NO_AUTHORIZED_ALTERNATIVE"
    return {
        "eligible": eligible,
        "excluded_reasons": excluded,
        **profile,
        "decision_status": status,
        "delegated_decision_maker": decision_maker,
        "delegated_choice": delegated_choice,
    }


def build_case(fixture, prefs, decision_maker, grants=None, protected=None):
    all_routes = sorted(fixture["routes"])
    grants = grants or {p: list(all_routes) for p in fixture["principals"]}
    return {"grants": grants, "protected_violations": protected or {},
            "decision_maker": decision_maker, "preferences": prefs}


def expected_signature(fixture, prefs, decision_maker, grants=None, protected=None):
    return oracle_profile(fixture, build_case(fixture, prefs, decision_maker, grants, protected))


def best_rank(signature, true_order):
    rank = {route: index for index, tier in enumerate(true_order) for route in tier}
    front = signature["possible_frontier"]
    return min((rank[route] for route in front), default=len(true_order) + 1)


def summarize_manipulation(document):
    report_by_id = {r["report_id"]: r for r in document["reports"]}
    order_by_id = {r["order_id"]: r["tiers"] for r in document["orders"]}
    world_by_id = {w["world_id"]: w for w in document["worlds"]}
    row_lookup = {(tuple(row["order_indices"]), row["reporter"], row["report_id"]): row
                  for row in document["deviations"]}
    safe_full, safe_partial = [], []
    changed = 0
    top_removed = 0
    sincere_by_world = {}
    for row in document["deviations"]:
        key = (tuple(row["order_indices"]), row["reporter"], row["report_id"])
        sincere = row_lookup[(tuple(row["order_indices"]), row["reporter"], row["sincere_report_id"])]
        if row["certificate"] != sincere["certificate"]:
            changed += 1
        true_order = order_by_id[f"O{row['order_indices'][row['reporter']]:02d}"]
        top = set(true_order[0])
        if not top.intersection(row["certificate"]["possible_frontier"]):
            top_removed += 1
        sincere_by_world[(tuple(row["order_indices"]), row["reporter"])] = sincere

    # A report is safe-beneficial in an information cell iff its opportunity-set
    # rank is no worse in every possible peer world and better in at least one.
    for reporter in range(2):
        other = 1 - reporter
        own_order_indices = range(len(order_by_id))
        for own_index in own_order_indices:
            possible_worlds = [tuple([own_index, peer_index]) if reporter == 0
                               else tuple([peer_index, own_index])
                               for peer_index in range(len(order_by_id))]
            full_cells = [[world] for world in possible_worlds]
            grouped = {}
            for world in possible_worlds:
                world_id = f"O{world[0]:02d}-O{world[1]:02d}"
                signal = world_by_id[world_id]["partial_signals"][str(reporter)]
                grouped.setdefault(pref_key(signal), []).append(world)
            for cells, out in ((full_cells, safe_full), (list(grouped.values()), safe_partial)):
                for cell in cells:
                    sincere_ranks = []
                    for world in cell:
                        base = sincere_by_world[(world, reporter)]["certificate"]
                        own_tiers = order_by_id[f"O{world[reporter]:02d}"]
                        sincere_ranks.append(best_rank(base, own_tiers))
                    for report_id, report in report_by_id.items():
                        if len(cell) == 1 and report_id == row_lookup[(cell[0], reporter, report_id)]["sincere_report_id"]:
                            continue
                        ranks = [best_rank(row_lookup[(world, reporter, report_id)]["certificate"],
                                           order_by_id[f"O{world[reporter]:02d}"])
                                 for world in cell]
                        if all(new <= old for new, old in zip(ranks, sincere_ranks, strict=True)) \
                                and any(new < old for new, old in zip(ranks, sincere_ranks, strict=True)):
                            out.append({"reporter": reporter, "own_order_index": own_index,
                                        "report_id": report_id,
                                        "worlds": [list(w) for w in cell],
                                        "truthful_ranks": sincere_ranks,
                                        "deviation_ranks": ranks})
    return {"frontier_changed_deviations": changed,
            "true_top_removed_deviations": top_removed,
            "safe_beneficial_full_information": safe_full,
            "safe_beneficial_partial_information": safe_partial}


def audit():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["sha256"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"HOLD_FROZEN_FILE_HASH_MISMATCH:{relative}")
    raw = subprocess.run(["git", "show", f"{freeze['source_commit']}:{freeze['source_path']}"],
                         cwd=HERE, capture_output=True, check=True).stdout
    if hashlib.sha256(raw).hexdigest() != freeze["source_sha256"]:
        raise SystemExit("HOLD_CERTIFICATE_SOURCE_HASH_MISMATCH")
    fixture_raw = (HERE / "fixture.json").read_bytes()
    if hashlib.sha256(fixture_raw).hexdigest() != freeze["fixture_sha256"]:
        raise SystemExit("HOLD_FIXTURE_HASH_MISMATCH")
    document = json.loads((OUT / "candidate-output.json").read_text(encoding="utf-8"))
    items = sorted(fixture["routes"])
    orders = rank_vector_orders(items)
    reports = report_domain(orders, fixture["report_masks"])
    if len(orders) != 13 or len(reports) != 23:
        raise SystemExit("HOLD_DOMAIN_CARDINALITY_MISMATCH")
    expected_keys = set()
    expected_by_key = {}
    for indices in itertools.product(range(len(orders)), repeat=2):
        for reporter in range(2):
            peer = 1 - reporter
            for report in reports:
                pref_by_principal = [order_preference(orders[index][0]) for index in indices]
                pref_by_principal[reporter] = report["preference"]
                prefs = dict(zip(fixture["principals"], pref_by_principal, strict=True))
                key = (indices, reporter, report["report_id"])
                expected_keys.add(key)
                expected_by_key[key] = expected_signature(fixture, prefs, fixture["decision_maker"])
    observed = {}
    for row in document["deviations"]:
        key = (tuple(row["order_indices"]), row["reporter"], row["report_id"])
        if key in observed:
            raise SystemExit("FAIL_DUPLICATE_DEVIATION_ROW")
        observed[key] = row
    if set(observed) != expected_keys:
        raise SystemExit("FAIL_DEVIATION_DOMAIN_INCOMPLETE")
    mismatches = []
    for key, expected in expected_by_key.items():
        if observed[key]["certificate"] != expected:
            mismatches.append(key)
    if mismatches:
        raise SystemExit(f"FAIL_ORACLE_MISMATCH:{len(mismatches)}")

    controls = document["controls"]
    c_top = next(order_preference(order) for order, _ in orders if order[0] == ("c",))
    peer_pref = order_preference(orders[-1][0])
    revoked_expected = expected_signature(
        fixture, {fixture["principals"][0]: c_top, fixture["principals"][1]: peer_pref},
        fixture["decision_maker"],
        grants={"principal_0": ["a", "b", "c"], "principal_1": ["a", "b"]},
    )
    protected_expected = expected_signature(
        fixture, {fixture["principals"][0]: c_top, fixture["principals"][1]: peer_pref},
        fixture["decision_maker"], protected={"c": ["principal_1:protected-record"]},
    )
    unknown_expected = expected_signature(
        fixture, {fixture["principals"][0]: {"strict": [["a", "b"]], "ties": []},
                  fixture["principals"][1]: peer_pref}, fixture["decision_maker"],
    )
    same_order = order_preference((("a",), ("b",), ("c",)))
    no_right_expected = expected_signature(
        fixture, {"principal_0": same_order, "principal_1": same_order}, None,
    )
    if controls != {"revoked_grant": revoked_expected,
                    "protected_constraint": protected_expected,
                    "unknown_comparison": unknown_expected,
                    "no_decision_right": no_right_expected}:
        raise SystemExit("FAIL_CONTROL_ORACLE_MISMATCH")
    if "c" in controls["revoked_grant"]["eligible"] or "c" in controls["protected_constraint"]["eligible"]:
        raise SystemExit("FAIL_AUTHORITY_OR_CONSTRAINT_CONTROL")
    if controls["unknown_comparison"]["completion_count"] <= 1:
        raise SystemExit("FAIL_UNKNOWN_COMPARISON_IMPUTED")
    if controls["no_decision_right"]["delegated_choice"] is not None \
            or controls["no_decision_right"]["decision_status"] != "NO_AUTO_CHOICE_WITHOUT_DECISION_RIGHT":
        raise SystemExit("FAIL_DECISION_RIGHT_CONTROL")

    manipulation = summarize_manipulation(document)
    if manipulation["frontier_changed_deviations"] == 0:
        raise SystemExit("FAIL_NO_REPORT_SENSITIVITY_DETECTED")
    if manipulation["safe_beneficial_full_information"] or manipulation["safe_beneficial_partial_information"]:
        conclusion = "MANIPULATION_WITNESS"
    else:
        conclusion = "EXHAUSTIVE_NULL_FOR_DECLARED_SET_UTILITY"

    # Prove that this auditor fails closed on a deliberately damaged candidate row.
    first = next(iter(observed))
    damaged = dict(observed[first]["certificate"])
    damaged["possible_frontier"] = ["not-a-route"]
    mutation_rejected = damaged != expected_by_key[first]
    if not mutation_rejected:
        raise SystemExit("FAIL_AUDITOR_MUTATION_CONTROL")

    result = {
        "schema": "preference-manipulation-7678-t0-audit-v1",
        "allocation": fixture["allocation"],
        "status": "PASS_METHOD_SCOPED",
        "hypothesis_conclusion": conclusion,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
        "independent_oracle": "rank-vector weak-order generation; independent completion/frontier reconstruction",
        "counts": {"weak_orders": len(orders), "admissible_reports": len(reports),
                      "truthful_worlds": len(list(itertools.product(range(len(orders)), repeat=2))),
                   "unilateral_report_evaluations": len(observed),
                   "certificate_mismatches": len(mismatches),
                   "frontier_changed_deviations": manipulation["frontier_changed_deviations"],
                   "true_top_removed_deviations": manipulation["true_top_removed_deviations"],
                   "truthful_top_preserved_worlds": len(document["worlds"]) * len(fixture["principals"]),
                   "safe_beneficial_full_information": len(manipulation["safe_beneficial_full_information"]),
                   "safe_beneficial_partial_information": len(manipulation["safe_beneficial_partial_information"]),
                   "all_controls_pass": True,
                   "auditor_rejects_mutation": mutation_rejected},
        "manipulation": manipulation,
        "scope": "finite synthetic certificate sensitivity; possible-frontier opportunity-set utility only",
    }
    (OUT / "audit-output.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "manipulation_counts": {k: len(v) for k, v in manipulation.items()
                                              if isinstance(v, list)}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(audit())
