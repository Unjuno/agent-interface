"""Independent integer-ID/raw-only auditor for Issue #7808 T0."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

EPS = 1e-9
ROUTE_IDS = {"conservative": 0, "fast": 1, "balanced": 2}


def _canonical_fixture_hash(fixture):
    blob = json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _profile(fixture, case, row, context, route):
    value = fixture["contexts"][context][route]
    override = case.get("overrides", {}).get(str(row), {}).get(route, {})
    vector = override.get("actual", value["actual"])
    useful = override.get("verified_useful", value["verified_useful"])
    return tuple(float(v) for v in vector), bool(useful)


def _pick(arm, available, profiles, debt, target):
    # The auditor uses numeric route IDs and recomputes all scores from raw inputs.
    ids = sorted(ROUTE_IDS[name] for name in available)
    by_id = {ROUTE_IDS[name]: profiles[name] for name in available}
    def n(id_):
        return next(name for name, number in ROUTE_IDS.items() if number == id_)
    if arm == "blackwell":
        def key(i):
            p = by_id[i]
            score = sum(debt[d] * p["forecast"][d] for d in range(len(target)))
            return (score, -int(bool(p["useful_forecast"])), i)
    elif arm == "scalar":
        def key(i):
            p = by_id[i]
            return (sum(p["forecast"]), -int(bool(p["useful_forecast"])), i)
    else:
        axes = [d for d in range(len(debt)) if debt[d] > EPS]
        safe_ids = [i for i in ids if all(by_id[i]["forecast"][d] <= target[d] + EPS
                                           for d in axes)]
        pool = safe_ids if safe_ids else ids
        def key(i):
            p = by_id[i]
            return (sum(p["forecast"]), -int(bool(p["useful_forecast"])), i)
    chosen = min(pool if arm == "independent_freeze" else ids, key=key)
    return n(chosen)


def _replay(fixture, case, arm):
    seen = []
    scheduled = []
    decisions = []
    length = len(case["contexts"])
    not_returned = set(case["missing_rows"])
    for t, context in enumerate(case["contexts"]):
        due_now = [item for item in scheduled if item[0] <= t]
        scheduled = [item for item in scheduled if item[0] > t]
        for due, row, route_id, vector, useful in due_now:
            seen.append({"row": row, "route": next(k for k,v in ROUTE_IDS.items() if v == route_id),
                         "vector": list(vector), "useful_verified": useful, "received_tick": t})
        if seen:
            debt = [max(0.0, sum(item["vector"][d] for item in seen) -
                        len(seen) * case["target"][d]) for d in range(len(case["target"]))]
        else:
            debt = [0.0] * len(case["target"])
        gate = case["gates"][context]
        available = [route for route, allowed in gate.items() if allowed is True and route in ROUTE_IDS]
        selected = _pick(arm, available, fixture["contexts"][context], debt, case["target"])
        decisions.append({"row": t, "context": context, "route": selected,
                          "feedback_before": [item["row"] for item in seen],
                          "forecast": list(fixture["contexts"][context][selected]["forecast"]),
                          "hard_gate_pass": bool(gate[selected])})
        vector, useful = _profile(fixture, case, t, context, selected)
        if t not in not_returned:
            due = t + int(case.get("delay_by_row", {}).get(str(t), 0)) + 1
            scheduled.append((due, t, ROUTE_IDS[selected], vector, useful))
    for tick in range(length, 2 * length + 1):
        due_now = [item for item in scheduled if item[0] <= tick]
        scheduled = [item for item in scheduled if item[0] > tick]
        for due, row, route_id, vector, useful in due_now:
            seen.append({"row": row, "route": next(k for k,v in ROUTE_IDS.items() if v == route_id),
                         "vector": list(vector), "useful_verified": useful, "received_tick": tick})
    seen.sort(key=lambda item: item["row"])
    ids = {item["row"] for item in seen}
    unknown = [i for i in range(length) if i not in ids]
    complete = not unknown
    if complete:
        means = [sum(item["vector"][d] for item in seen) / length
                 for d in range(len(case["target"]))]
        claim = "WITHIN_TARGET" if all(means[d] <= case["target"][d] + EPS
                                       for d in range(len(means))) else "OUTSIDE_TARGET"
    else:
        means, claim = None, "UNKNOWN_INCOMPLETE_FEEDBACK"
    highs = [max((item["vector"][d] for item in seen), default=None)
             for d in range(len(case["target"]))]
    return {"steps": decisions, "feedback": seen, "unknown_feedback_rows": unknown,
            "complete_feedback": complete, "observed_mean": means,
            "max_observed_single_episode": highs,
            "verified_useful_count": sum(int(item["useful_verified"]) for item in seen),
            "target_claim": claim}


def _oracle_uncached(fixture, case):
    route_lists = []
    for context in case["contexts"]:
        gate = case["gates"][context]
        route_lists.append([r for r in fixture["route_order"]
                            if gate.get(r) is True and r in ROUTE_IDS])
    best_feasible = None
    best_any = None
    feasible_count = 0
    for sequence in itertools.product(*route_lists):
        totals = [0.0] * len(case["target"])
        useful = 0
        for row, (context, route) in enumerate(zip(case["contexts"], sequence)):
            vector, effect = _profile(fixture, case, row, context, route)
            useful += int(effect)
            for d, value in enumerate(vector):
                totals[d] += value
        means = [v / len(sequence) for v in totals]
        feasible = all(means[d] <= case["target"][d] + EPS
                       for d in range(len(means)))
        record = {"routes": list(sequence), "means": means, "useful": useful}
        rank = (useful, tuple(-v for v in means), tuple(sequence))
        if best_any is None or rank > best_any[0]:
            best_any = (rank, record)
        if feasible:
            feasible_count += 1
            if best_feasible is None or rank > best_feasible[0]:
                best_feasible = (rank, record)
    return {"status": "FEASIBLE" if best_feasible else "INFEASIBLE",
            "feasible_sequences": feasible_count,
            "best_feasible": best_feasible[1] if best_feasible else None,
            "best_any": best_any[1] if best_any else None}


_ORACLE_CACHE = {}


def _oracle(fixture, case):
    key = (_canonical_fixture_hash(fixture), case["id"])
    if key not in _ORACLE_CACHE:
        _ORACLE_CACHE[key] = _oracle_uncached(fixture, case)
    return _ORACLE_CACHE[key]

def audit(fixture, raw):
    errors = []
    if fixture.get("schema") != "vca7808-fixture-v1":
        errors.append("fixture_schema")
    if raw.get("schema") != "vca7808-candidate-v1":
        errors.append("candidate_schema")
    if raw.get("fixture_sha256") != _canonical_fixture_hash(fixture):
        errors.append("fixture_hash_mismatch")
    result = {}
    for case in fixture["cases"]:
        cid = case["id"]
        if cid not in raw.get("policies", {}):
            errors.append("missing_case:" + cid)
            continue
        result[cid] = {}
        for arm in ("blackwell", "scalar", "independent_freeze"):
            actual = raw["policies"][cid].get(arm)
            if actual is None:
                errors.append(f"missing_arm:{cid}:{arm}")
                continue
            expected = _replay(fixture, case, arm)
            if actual != expected:
                errors.append(f"trace_or_summary_mismatch:{cid}:{arm}")
            for step in actual.get("steps", []):
                context = step.get("context")
                route = step.get("route")
                if route not in ROUTE_IDS or case["gates"].get(context, {}).get(route) is not True:
                    errors.append(f"hard_gate_violation:{cid}:{arm}:{step.get('row')}")
            oracle = _oracle(fixture, case)
            result[cid][arm] = {
                "verified_useful": expected["verified_useful_count"],
                "observed_mean": expected["observed_mean"],
                "max_episode": expected["max_observed_single_episode"],
                "target_claim": expected["target_claim"],
                "unknown_feedback_rows": expected["unknown_feedback_rows"],
                "oracle": oracle,
                "hard_gate_violations": sum(not s["hard_gate_pass"] for s in expected["steps"]),
            }
    feasible = result.get("feasible_tradeoff", {})
    bw = feasible.get("blackwell", {})
    fr = feasible.get("independent_freeze", {})
    sc = feasible.get("scalar", {})
    target = next(c["target"] for c in fixture["cases"] if c["id"] == "feasible_tradeoff")
    feasible_ok = (bw.get("target_claim") == "WITHIN_TARGET" and
                   bw.get("observed_mean") is not None and
                   all(bw["observed_mean"][i] <= target[i] + EPS for i in range(len(target))) and
                   bw.get("oracle", {}).get("status") == "FEASIBLE" and
                   bw.get("verified_useful", 0) > fr.get("verified_useful", 0) and
                   bw.get("verified_useful", 0) > sc.get("verified_useful", 0))
    if not feasible_ok:
        errors.append("feasible_case_hypothesis_not_met")
    infeasible = result.get("infeasible_target", {}).get("blackwell", {})
    if (infeasible.get("oracle", {}).get("status") != "INFEASIBLE" or
            infeasible.get("target_claim") == "WITHIN_TARGET"):
        errors.append("infeasible_target_claim")
    gap = result.get("delayed_missing_feedback", {}).get("blackwell", {})
    if (gap.get("target_claim") != "UNKNOWN_INCOMPLETE_FEEDBACK" or
            not gap.get("unknown_feedback_rows")):
        errors.append("missing_feedback_not_unknown")
    extreme = result.get("single_extreme_episode", {}).get("blackwell", {})
    if not extreme.get("max_episode") or max(extreme["max_episode"]) < 10.0:
        errors.append("extreme_episode_hidden")
    for cid, arms in result.items():
        for arm, summary in arms.items():
            if summary["hard_gate_violations"]:
                errors.append(f"hard_gate_summary:{cid}:{arm}")
    status = "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD"
    return {"schema": "vca7808-independent-audit-v1", "disposition": status,
            "errors": errors, "cases": result}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    raw = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "errors": result["errors"],
                      "cases": len(result["cases"])}))


if __name__ == "__main__":
    main()
