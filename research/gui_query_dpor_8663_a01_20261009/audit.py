"""Independent raw-only replay and exhaustive oracle; imports no candidate module."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_ID = "GUI-QUERY-DPOR-8663-A01-20261009"
BASE = "743ae74ec5be2472ff27fa06fe13d5ecf8534de5"


def load(path):
    return json.loads(path.read_text())


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def scan(s):
    answer = []
    for obj in s["nodes"]:
        if (obj["scope"] == s["active_scope"] and obj["name"] == "Save"
                and obj["enabled"] is True and obj["visible"] is True):
            answer.append(obj["id"])
    return sorted(answer)


def starting(fixture):
    src = fixture["initial"]
    return {"active_scope": src["active_scope"], "complete": src["complete"],
            "predicate_epoch": 0, "scope_epoch": 0,
            "nodes": copy.deepcopy(src["nodes"]), "query": None,
            "validated": False, "admission": None,
            "_events": copy.deepcopy(fixture["events"])}


def find_node(s, ident):
    for obj in s["nodes"]:
        if obj["id"] == ident:
            return obj
    return None


def queried(s):
    ids = scan(s)
    versions = {}
    for obj in s["nodes"]:
        if obj["id"] in ids:
            versions[obj["id"]] = obj["version"]
    return {"members": ids, "versions": versions, "scope": s["active_scope"],
            "complete": s["complete"], "predicate_epoch": s["predicate_epoch"],
            "scope_epoch": s["scope_epoch"]}


def fresh_valid(s):
    now = scan(s)
    return s["complete"] is True and len(now) == 1


def old_selection_valid(s):
    q = s["query"]
    if q is None or q["complete"] is not True or s["complete"] is not True:
        return False
    if q["scope"] != s["active_scope"] or q["scope_epoch"] != s["scope_epoch"]:
        return False
    if q["predicate_epoch"] != s["predicate_epoch"] or q["members"] != scan(s):
        return False
    if len(q["members"]) != 1:
        return False
    obj = find_node(s, q["members"][0])
    return obj is not None and obj["version"] == q["versions"][obj["id"]]


def denial(s, family):
    q = s["query"]
    if q is None:
        return "no_query"
    if family == "node":
        if q["complete"] is not True:
            return "query_incomplete"
        if len(q["members"]) == 0:
            return "query_empty"
        if len(q["members"]) > 1:
            return "query_ambiguous"
        obj = find_node(s, q["members"][0])
        return "target_missing_or_changed" if obj is None or obj["version"] != q["versions"][obj["id"]] else "refused"
    if family == "certificate":
        if q["complete"] is not True or s["complete"] is not True:
            return "incomplete"
        if q["scope"] != s["active_scope"] or q["scope_epoch"] != s["scope_epoch"]:
            return "scope_changed"
        if q["members"] != scan(s):
            return "membership_changed"
        if q["predicate_epoch"] != s["predicate_epoch"]:
            return "predicate_epoch_changed"
        if len(q["members"]) != 1:
            return "query_empty" if not q["members"] else "query_ambiguous"
        obj = find_node(s, q["members"][0])
        return "target_missing_or_changed" if obj is None or obj["version"] != q["versions"][obj["id"]] else "refused"
    if s["complete"] is not True:
        return "incomplete"
    current = scan(s)
    if not current:
        return "empty"
    return "ambiguous"


def decide(s):
    q = s["query"]
    current = scan(s)
    node_target = q["members"][0] if q and len(q["members"]) == 1 else None
    node = find_node(s, node_target) if node_target else None
    node_ok = bool(q and q["complete"] is True and node is not None
                   and node["version"] == q["versions"][node_target])
    cert_ok = node_ok and old_selection_valid(s)
    fresh_ok = fresh_valid(s)
    return {
        "node_only": {"accepted": node_ok, "target": node_target if node_ok else None,
                      "unsafe": bool(node_ok and not old_selection_valid(s)),
                      "reason": "accepted" if node_ok else denial(s, "node")},
        "predicate_cert": {"accepted": cert_ok, "target": node_target if cert_ok else None,
                           "unsafe": bool(cert_ok and not old_selection_valid(s)),
                           "reason": "accepted" if cert_ok else denial(s, "certificate")},
        "always_requery": {"accepted": fresh_ok,
                           "target": current[0] if fresh_ok else None,
                           "unsafe": False,
                           "reason": "accepted" if fresh_ok else denial(s, "fresh")}}


def step(s, event):
    t = copy.deepcopy(s)
    kind = event["kind"]
    if kind == "query":
        t["query"] = queried(t)
    elif kind == "validate":
        t["validated"] = True
    elif kind == "admit":
        t["admission"] = decide(t)
    elif kind == "insert":
        before = set(scan(t))
        t["nodes"].append(copy.deepcopy(event["node"]))
        if before != set(scan(t)):
            t["predicate_epoch"] += 1
    elif kind == "remove":
        old = set(scan(t))
        t["nodes"] = [obj for obj in t["nodes"] if obj["id"] != event["target"]]
        if old != set(scan(t)):
            t["predicate_epoch"] += 1
    elif kind == "rename":
        old = set(scan(t))
        obj = find_node(t, event["target"])
        if obj is not None:
            obj["name"] = event["name"]
            obj["version"] = obj["version"] + 1
        if old != set(scan(t)):
            t["predicate_epoch"] += 1
    elif kind == "enable":
        old = set(scan(t))
        obj = find_node(t, event["target"])
        if obj is not None:
            obj["enabled"] = event["value"]
            obj["version"] = obj["version"] + 1
        if old != set(scan(t)):
            t["predicate_epoch"] += 1
    elif kind == "scope":
        if t["active_scope"] != event["value"]:
            t["active_scope"] = event["value"]
            t["scope_epoch"] = t["scope_epoch"] + 1
            t["predicate_epoch"] = t["predicate_epoch"] + 1
    elif kind == "incomplete":
        if t["complete"] is not False:
            t["complete"] = False
            t["predicate_epoch"] = t["predicate_epoch"] + 1
    elif kind == "unknown":
        t["complete"] = None
        t["scope_epoch"] = t["scope_epoch"] + 1
        t["predicate_epoch"] = t["predicate_epoch"] + 1
    elif kind == "aba":
        obj = find_node(t, event["target"])
        if obj is not None:
            for _ in range(2):
                obj["enabled"] = not obj["enabled"]
                obj["version"] += 1
                t["predicate_epoch"] += 1
    elif kind == "decorate":
        obj = find_node(t, event["target"])
        if obj is not None:
            obj[event["field"]] = event["value"]
    else:
        raise ValueError(kind)
    return t


def final_record(s):
    stable_nodes = [dict(obj) for obj in sorted(s["nodes"], key=lambda n: n["id"])]
    return {"final": {"active_scope": s["active_scope"], "complete": s["complete"],
                       "predicate_epoch": s["predicate_epoch"], "scope_epoch": s["scope_epoch"],
                       "nodes": stable_nodes},
            "query": copy.deepcopy(s["query"]), "admission": copy.deepcopy(s["admission"])}


def runnable(events, done):
    answer = []
    for event in events:
        if event["id"] in done:
            continue
        if all(required in done for required in event.get("requires", [])):
            answer.append(event["id"])
    return sorted(answer)


def all_orders(case):
    catalog = {e["id"]: e for e in case["events"]}
    out = []

    def walk(s, done, path):
        if len(done) == len(catalog):
            out.append({"schedule": list(path), "outcome": final_record(s)})
            return
        for ident in runnable(case["events"], done):
            walk(step(s, catalog[ident]), done | {ident}, path + (ident,))

    walk(starting(case), set(), ())
    return out


def affects_selector(ev, s):
    kind = ev["kind"]
    if kind in {"scope", "incomplete", "unknown", "aba"}:
        return True
    if kind == "insert":
        n = ev["node"]
        if n["name"] == "Save" and n["enabled"] is True and n["visible"] is True:
            return True
        return any(x.get("target") == n["id"] and x["kind"] in {"rename", "enable", "remove"}
                   for x in s.get("_events", []))
    if kind == "remove":
        return True
    if kind in {"rename", "enable"}:
        return True
    return False


def control(ev):
    return ev["kind"] in ("query", "validate", "admit")


def writes(ev):
    k = ev["kind"]
    if k == "insert":
        return {(ev["node"]["id"], "*")}
    if k in {"remove", "rename", "enable"}:
        fld = {"remove": "*", "rename": "name", "enable": "enabled"}[k]
        return {(ev["target"], fld)}
    if k == "decorate":
        return {(ev["target"], ev["field"])}
    return {("?", "?")}


def independent(s, case, left, right, method):
    table = {e["id"]: e for e in case["events"]}
    a, b = table[left], table[right]
    if "unknown" in (a["kind"], b["kind"]):
        return method == "mutant_unknown_independent"
    if control(a) and control(b):
        return False
    if control(a) != control(b):
        ui = b if control(a) else a
        if method in {"predicate", "mutant_cross_scope", "mutant_unknown_independent"}:
            if affects_selector(ui, s):
                return method == "mutant_cross_scope" and ui["kind"] == "scope"
            return True
        observed = set(scan(s))
        changed = set()
        if ui["kind"] in {"remove", "rename", "enable", "decorate"}:
            changed.add(ui["target"])
        elif ui["kind"] == "insert":
            changed.add(ui["node"]["id"])
        if ui["kind"] in {"scope", "incomplete", "unknown", "aba"}:
            return True
        return observed.isdisjoint(changed)
    if a["kind"] in {"scope", "incomplete", "aba"} or b["kind"] in {"scope", "incomplete", "aba"}:
        return False
    if method in {"predicate", "mutant_cross_scope", "mutant_unknown_independent"}:
        if selector_event(a) or selector_event(b):
            return False
    wa, wb = writes(a), writes(b)
    for obj_a, field_a in wa:
        for obj_b, field_b in wb:
            if obj_a == obj_b and ("*" in (field_a, field_b) or field_a == field_b):
                return False
    return True


def selector_event(ev):
    return ev["kind"] in {"insert", "remove", "rename", "enable", "scope",
                          "incomplete", "unknown", "aba"}


def reduced_orders(case, method):
    table = {e["id"]: e for e in case["events"]}
    output = []
    claims = []

    def descend(s, done, sleeping, path):
        available = runnable(case["events"], done)
        if len(done) == len(table):
            output.append({"schedule": list(path), "outcome": final_record(s)})
            return
        sleep_here = set(sleeping).intersection(available)
        for ident in available:
            if ident in sleep_here:
                continue
            after = step(s, table[ident])
            done_after = done | {ident}
            enabled_after = set(runnable(case["events"], done_after))
            keep_sleeping = set()
            for old in sleep_here:
                independent_pair = independent(s, case, old, ident, method)
                claims.append({"prefix": list(path), "left": old, "right": ident,
                               "declared_independent": independent_pair})
                if old in enabled_after and independent_pair:
                    keep_sleeping.add(old)
            descend(after, done_after, keep_sleeping, path + (ident,))
            sleep_here.add(ident)

    descend(starting(case), set(), set(), ())
    return output, claims


def check():
    freeze = load(ROOT / "FREEZE.json")
    for rel, expected in freeze["sha256"].items():
        found = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if found != expected:
            raise RuntimeError("frozen input changed: " + rel)
    model_path = ROOT / "MODEL.json"
    model = load(model_path)
    raw = load(ROOT / "candidate_raw.json")
    if raw.get("allocation_id") != RUN_ID or raw.get("base_commit") != BASE:
        raise RuntimeError("candidate identity mismatch")
    if raw.get("model_sha256") != freeze["model_sha256"]:
        raise RuntimeError("candidate model identity mismatch")
    checks = []
    error_list = []

    def assert_check(name, condition, detail=None):
        checks.append({"check": name, "pass": bool(condition), "detail": detail})
        if not condition:
            error_list.append(name)

    plans = {"exhaustive": None, "node_only_dpor": "node_only",
             "predicate_dpor": "predicate", "mutant_missing_predicate": "node_only",
             "mutant_cross_scope": "mutant_cross_scope",
             "mutant_unknown_independent": "mutant_unknown_independent"}
    replayed = {key: {} for key in plans}
    coverage = {}
    full_witnesses = set()
    for case in model["cases"]:
        name = case["id"]
        baseline = all_orders(case)
        expected_sched = {tuple(row["schedule"]) for row in baseline}
        stored_full = raw["runs"]["exhaustive"].get(name, [])
        stored_sched = {tuple(row["schedule"]) for row in stored_full}
        assert_check(f"{name}: exhaustive schedule equality", stored_sched == expected_sched,
                     {"expected": len(expected_sched), "stored": len(stored_sched)})
        baseline_outcomes = set()
        unsafe_classes = set()
        for schedule in sorted(expected_sched):
            replay = replay_schedule(case, schedule)
            sig = packed(final_record(replay))
            baseline_outcomes.add(sig)
            for policy, result in replay["admission"].items():
                if result["unsafe"]:
                    q_at = schedule.index("query")
                    a_at = schedule.index("admit")
                    between = [table_event(case, e)["kind"] for e in schedule[q_at + 1:a_at]]
                    unsafe_classes.add((name, policy, tuple(sorted(between))))
        coverage[name] = {"exhaustive_schedules": len(expected_sched),
                          "exhaustive_outcomes": len(baseline_outcomes),
                          "unsafe_classes": [list(x) for x in sorted(unsafe_classes)]}
        full_witnesses.update(unsafe_classes)

        for key, mode in plans.items():
            if key == "exhaustive":
                rows = stored_full
            else:
                expected_rows, own_claims = reduced_orders(case, mode)
                rows = raw["runs"][key].get(name, [])
                expected_dpor = {tuple(r["schedule"]) for r in expected_rows}
                actual_dpor = {tuple(r["schedule"]) for r in rows}
                assert_check(f"{name}: {key} DPOR trace equality", actual_dpor == expected_dpor,
                             {"expected": len(expected_dpor), "stored": len(actual_dpor)})
                if key != "node_only_dpor":
                    stored_claims = raw["runs"].get("claims", {}).get(key, {}).get(name, [])
                    assert_check(f"{name}: {key} dependency claims", stored_claims == own_claims,
                                 {"expected": len(own_claims), "stored": len(stored_claims)})
                    for claim in stored_claims:
                        if claim["declared_independent"]:
                            at_state = replay_schedule(case, claim["prefix"])
                            commutes = pair_commutes(case, at_state, claim["prefix"],
                                                     claim["left"], claim["right"])
                            assert_check(f"{name}: independent pair commutes",
                                         commutes, {"prefix": claim["prefix"],
                                                    "left": claim["left"], "right": claim["right"]})
            computed = []
            for row in rows:
                schedule = tuple(row["schedule"])
                replay = replay_schedule(case, schedule)
                expected_result = final_record(replay)
                assert_check(f"{name}: {key} raw replay",
                             packed(row["outcome"]) == packed(expected_result),
                             {"schedule": list(schedule)})
                computed.append({"schedule": list(schedule), "outcome": expected_result})
            replayed[key][name] = computed

        pred_outcomes = {packed(r["outcome"]) for r in replayed["predicate_dpor"][name]}
        assert_check(f"{name}: predicate-DPOR outcome coverage",
                     pred_outcomes == baseline_outcomes,
                     {"exhaustive": len(baseline_outcomes), "predicate_dpor": len(pred_outcomes)})

        pred_unsafe = unsafe_classes_from(replayed["predicate_dpor"][name], name)
        assert_check(f"{name}: predicate-DPOR unsafe witness classes",
                     unsafe_classes <= pred_unsafe,
                     {"expected": len(unsafe_classes), "retained": len(pred_unsafe)})

    unknown_case = next(c for c in model["cases"] if c["id"] == "unknown_transition")
    unknown_pairs = []
    for left in unknown_case["events"]:
        for right in unknown_case["events"]:
            if "unknown" in {left["kind"], right["kind"]} and left["id"] != right["id"]:
                if independent(starting(unknown_case), unknown_case, left["id"], right["id"], "predicate"):
                    unknown_pairs.append([left["id"], right["id"]])
    assert_check("unknown dependencies are never independent", not unknown_pairs,
                 {"bad_pairs": unknown_pairs})

    all_lookup = {c["id"]: c for c in model["cases"]}
    for cid, strategy in (("matching_insert", "mutant_missing_predicate"),
                          ("modal_scope_change", "mutant_cross_scope"),
                          ("unknown_transition", "mutant_unknown_independent")):
        full = {packed(r["outcome"]) for r in replayed["exhaustive"][cid]}
        reduced = {packed(r["outcome"]) for r in replayed[strategy][cid]}
        missing = sorted(full - reduced)
        assert_check(f"{strategy} is caught", bool(missing), {"missing_outcomes": len(missing)})

    control_full = len(replayed["exhaustive"]["commuting_control"])
    control_pred = len(replayed["predicate_dpor"]["commuting_control"])
    reduction = 1 - control_pred / control_full if control_full else 0.0
    assert_check("commuting control reduction >= 20 percent", reduction >= 0.20,
                 {"exhaustive": control_full, "predicate_dpor": control_pred,
                  "reduction_fraction": reduction})
    assert_check("at least one node-only unsafe omission",
                 any(set(packed(r["outcome"]) for r in replayed["exhaustive"][cid])
                     - set(packed(r["outcome"]) for r in replayed["node_only_dpor"][cid])
                     for cid in ("matching_insert", "rename_into_set", "enable_into_set",
                                 "modal_scope_change", "incomplete_enumeration", "aba_membership")),
                 None)

    return {"schema": "gui-query-dpor-independent-audit-v1",
            "allocation_id": RUN_ID, "base_commit": BASE,
            "status": "PASS_DPOR_PREDICATE_SCOPED" if not error_list else "FAIL_AUDIT",
            "auditor": "separate implementation; reads FREEZE.json, MODEL.json, candidate_raw.json only",
            "python": sys.version.split()[0], "platform": platform.platform(),
            "audited_at_utc": datetime.now(timezone.utc).isoformat(),
            "case_results": coverage, "commuting_control_reduction_fraction": reduction,
            "checks_passed": sum(x["pass"] for x in checks), "checks_total": len(checks),
            "errors": error_list, "checks": checks}


def table_event(case, ident):
    return next(e for e in case["events"] if e["id"] == ident)


def replay_schedule(case, schedule):
    lookup = {e["id"]: e for e in case["events"]}
    if len(schedule) != len(lookup) or len(set(schedule)) != len(lookup) or set(schedule) != set(lookup):
        raise ValueError("not a complete schedule")
    state = starting(case)
    done = set()
    for ident in schedule:
        ev = lookup[ident]
        if not set(ev.get("requires", [])) <= done:
            raise ValueError("schedule violates prerequisites")
        state = step(state, ev)
        done.add(ident)
    return state


def unsafe_classes_from(rows, case_id):
    # Recompute policy classes from raw schedule plus replayed terminal outputs.
    # For each retained row, the exact event types between original query and admission
    # make the counterexample replayable without trusting candidate labels.
    answer = set()
    case = next(c for c in load(ROOT / "MODEL.json")["cases"] if c["id"] == case_id)
    for row in rows:
        schedule = row["schedule"]
        state = replay_schedule(case, schedule)
        q_at, a_at = schedule.index("query"), schedule.index("admit")
        causes = tuple(sorted(table_event(case, x)["kind"] for x in schedule[q_at + 1:a_at]))
        for policy, outcome in state["admission"].items():
            if outcome["unsafe"]:
                answer.add((case_id, policy, causes))
    return answer


def pair_commutes(case, state, prefix, left, right):
    table = {e["id"]: e for e in case["events"]}
    done = set(prefix)
    if left not in runnable(case["events"], done) or right not in runnable(case["events"], done):
        return False
    l_then_r = step(step(state, table[left]), table[right])
    r_then_l = step(step(state, table[right]), table[left])
    return (packed(final_record(l_then_r)) == packed(final_record(r_then_l))
            and set(runnable(case["events"], done | {left, right}))
            == set(runnable(case["events"], done | {right, left})))


def main():
    report = check()
    (ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(report["status"], report["checks_passed"], "/", report["checks_total"],
          "reduction", f"{report['commuting_control_reduction_fraction']:.6f}")
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
