"""Frozen candidate: bounded sleep-set comparison for GUI query histories."""
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


def read_json(path: Path):
    return json.loads(path.read_text())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def member_set(state):
    return sorted(n["id"] for n in state["nodes"]
                  if n["scope"] == state["active_scope"]
                  and n["name"] == "Save" and n["enabled"] is True
                  and n["visible"] is True)


def snapshot(state):
    ids = member_set(state)
    versions = {n["id"]: n["version"] for n in state["nodes"] if n["id"] in ids}
    return {"members": ids, "versions": versions, "scope": state["active_scope"],
            "complete": state["complete"], "predicate_epoch": state["predicate_epoch"],
            "scope_epoch": state["scope_epoch"]}


def initial_state(case):
    return {"active_scope": case["initial"]["active_scope"],
            "complete": case["initial"]["complete"],
            "predicate_epoch": 0, "scope_epoch": 0,
            "nodes": copy.deepcopy(case["initial"]["nodes"]),
            "query": None, "validated": False, "admission": None}


def _node(state, ident):
    return next((n for n in state["nodes"] if n["id"] == ident), None)


def _matches_node(n):
    return n["name"] == "Save" and n["enabled"] is True and n["visible"] is True


def transition(state, event):
    s = copy.deepcopy(state)
    kind = event["kind"]
    if kind == "query":
        s["query"] = snapshot(s)
    elif kind == "validate":
        s["validated"] = True
    elif kind == "admit":
        s["admission"] = evaluate(s)
    elif kind == "insert":
        before = set(member_set(s))
        s["nodes"].append(copy.deepcopy(event["node"]))
        if set(member_set(s)) != before:
            s["predicate_epoch"] += 1
    elif kind == "remove":
        before = set(member_set(s))
        s["nodes"] = [n for n in s["nodes"] if n["id"] != event["target"]]
        if set(member_set(s)) != before:
            s["predicate_epoch"] += 1
    elif kind == "rename":
        n = _node(s, event["target"])
        before = set(member_set(s))
        if n is not None:
            n["name"] = event["name"]
            n["version"] += 1
        if set(member_set(s)) != before:
            s["predicate_epoch"] += 1
    elif kind == "enable":
        n = _node(s, event["target"])
        before = set(member_set(s))
        if n is not None:
            n["enabled"] = event["value"]
            n["version"] += 1
        if set(member_set(s)) != before:
            s["predicate_epoch"] += 1
    elif kind == "scope":
        if s["active_scope"] != event["value"]:
            s["active_scope"] = event["value"]
            s["scope_epoch"] += 1
            s["predicate_epoch"] += 1
    elif kind == "incomplete":
        if s["complete"] is not False:
            s["complete"] = False
            s["predicate_epoch"] += 1
    elif kind == "unknown":
        s["complete"] = None
        s["scope_epoch"] += 1
        s["predicate_epoch"] += 1
    elif kind == "aba":
        n = _node(s, event["target"])
        if n is not None:
            n["enabled"] = not n["enabled"]
            n["version"] += 1
            s["predicate_epoch"] += 1
            n["enabled"] = not n["enabled"]
            n["version"] += 1
            s["predicate_epoch"] += 1
    elif kind == "decorate":
        n = _node(s, event["target"])
        if n is not None:
            n[event["field"]] = event["value"]
    else:
        raise ValueError(f"unknown event kind: {kind}")
    return s


def _same_original_selection(s):
    q = s["query"]
    if q is None or q["complete"] is not True or s["complete"] is not True:
        return False
    if q["scope"] != s["active_scope"] or q["scope_epoch"] != s["scope_epoch"]:
        return False
    if q["predicate_epoch"] != s["predicate_epoch"] or q["members"] != member_set(s):
        return False
    if len(q["members"]) != 1:
        return False
    selected = _node(s, q["members"][0])
    return selected is not None and selected["version"] == q["versions"][selected["id"]]


def evaluate(s):
    q = s["query"]
    current = member_set(s)
    node_ok = (q is not None and q["complete"] is True and len(q["members"]) == 1
               and _node(s, q["members"][0]) is not None
               and _node(s, q["members"][0])["version"] == q["versions"][q["members"][0]])
    predicate_ok = node_ok and _same_original_selection(s)
    always_ok = s["complete"] is True and len(current) == 1
    always_target = current[0] if always_ok else None
    original_stable = _same_original_selection(s)
    return {
        "node_only": {"accepted": node_ok, "target": q["members"][0] if node_ok else None,
                       "unsafe": bool(node_ok and not original_stable),
                       "reason": "accepted" if node_ok else _node_failure(s)},
        "predicate_cert": {"accepted": predicate_ok,
                           "target": q["members"][0] if predicate_ok else None,
                           "unsafe": bool(predicate_ok and not original_stable),
                           "reason": "accepted" if predicate_ok else _predicate_failure(s)},
        "always_requery": {"accepted": always_ok, "target": always_target,
                           "unsafe": False,
                           "reason": "accepted" if always_ok else _fresh_failure(s, current)}
    }


def _node_failure(s):
    q = s["query"]
    if q is None:
        return "no_query"
    if q["complete"] is not True:
        return "query_incomplete"
    if len(q["members"]) != 1:
        return "query_empty" if not q["members"] else "query_ambiguous"
    n = _node(s, q["members"][0])
    return "target_missing_or_changed" if n is None or n["version"] != q["versions"][n["id"]] else "refused"


def _predicate_failure(s):
    q = s["query"]
    if q is None:
        return "no_query"
    if q["complete"] is not True or s["complete"] is not True:
        return "incomplete"
    if q["scope"] != s["active_scope"] or q["scope_epoch"] != s["scope_epoch"]:
        return "scope_changed"
    if q["members"] != member_set(s):
        return "membership_changed"
    if q["predicate_epoch"] != s["predicate_epoch"]:
        return "predicate_epoch_changed"
    if len(q["members"]) != 1:
        return "query_empty" if not q["members"] else "query_ambiguous"
    n = _node(s, q["members"][0])
    return "target_missing_or_changed" if n is None or n["version"] != q["versions"][n["id"]] else "refused"


def _fresh_failure(s, current):
    if s["complete"] is not True:
        return "incomplete"
    if not current:
        return "empty"
    return "ambiguous"


def _core(event):
    return event["kind"] in {"query", "validate", "admit"}


def _possible_predicate_effect(event, case, state):
    kind = event["kind"]
    if kind in {"scope", "incomplete", "unknown", "aba"}:
        return True
    if kind == "insert":
        if _matches_node(event["node"]):
            return True
        ident = event["node"]["id"]
        return any(e.get("target") == ident and e["kind"] in {"rename", "enable", "remove"}
                   for e in case["events"])
    if kind == "remove":
        return True
    if kind in {"rename", "enable"}:
        # These write selector fields; another event can make the written value
        # relevant even when the target is not currently a member.
        return True
    return False


def independent(state, left, right, mode, case):
    a = next(e for e in case["events"] if e["id"] == left)
    b = next(e for e in case["events"] if e["id"] == right)
    if a["kind"] == "unknown" or b["kind"] == "unknown":
        return mode == "mutant_unknown_independent"
    if _core(a) and _core(b):
        return False
    if _core(a) != _core(b):
        ui = b if _core(a) else a
        predicate_modes = {"predicate", "mutant_cross_scope", "mutant_unknown_independent"}
        if mode in predicate_modes:
            if _possible_predicate_effect(ui, case, state):
                return mode == "mutant_cross_scope" and ui["kind"] == "scope"
            return True
        # Node-only tracks only fields of the concrete current query members.
        read_nodes = set(member_set(state))
        writes = set()
        if ui["kind"] in {"remove", "rename", "enable", "decorate"}:
            writes.add(ui["target"])
        elif ui["kind"] == "insert":
            writes.add(ui["node"]["id"])
        if ui["kind"] in {"scope", "incomplete", "unknown", "aba"}:
            return True if mode != "node_only" else True
        return not bool(read_nodes & writes)
    if a["kind"] in {"unknown"} or b["kind"] in {"unknown"}:
        return mode == "mutant_unknown_independent"
    if mode in {"predicate", "mutant_cross_scope", "mutant_unknown_independent"}:
        if _possible_predicate_effect(a, case, state) or _possible_predicate_effect(b, case, state):
            return False
    if a["kind"] in {"scope", "incomplete", "aba"} or b["kind"] in {"scope", "incomplete", "aba"}:
        return False
    # UI transitions commute only when their concrete writes are disjoint.
    def write_set(e):
        if e["kind"] == "insert":
            return {(e["node"]["id"], "*")}
        if e["kind"] in {"remove", "rename", "enable"}:
            field = {"remove": "*", "rename": "name", "enable": "enabled"}[e["kind"]]
            return {(e["target"], field)}
        if e["kind"] == "decorate":
            return {(e["target"], e["field"])}
        return {("?", "?")}
    wa, wb = write_set(a), write_set(b)
    if any(na == nb and (fa == "*" or fb == "*" or fa == fb)
           for na, fa in wa for nb, fb in wb):
        return False
    return True


def enabled(events, done):
    return sorted(e["id"] for e in events
                  if e["id"] not in done and set(e.get("requires", [])) <= done)


def exhaustive(case):
    by_id = {e["id"]: e for e in case["events"]}
    traces = []

    def visit(s, done, order):
        if len(done) == len(by_id):
            traces.append({"schedule": list(order), "outcome": outcome(s)})
            return
        for ident in enabled(case["events"], done):
            visit(transition(s, by_id[ident]), done | {ident}, order + [ident])

    visit(initial_state(case), set(), [])
    return traces


def sleep_set(case, mode):
    by_id = {e["id"]: e for e in case["events"]}
    traces = []
    claims = []

    def visit(s, done, asleep, order):
        avail = enabled(case["events"], done)
        if len(done) == len(by_id):
            traces.append({"schedule": list(order), "outcome": outcome(s)})
            return
        sleeping = set(asleep) & set(avail)
        for ident in avail:
            if ident in sleeping:
                continue
            child = transition(s, by_id[ident])
            child_done = done | {ident}
            child_avail = set(enabled(case["events"], child_done))
            child_sleep = {other for other in sleeping
                           if other in child_avail and independent(s, other, ident, mode, case)}
            for other in sleeping:
                claims.append({"prefix": list(order), "left": other, "right": ident,
                               "declared_independent": independent(s, other, ident, mode, case)})
            visit(child, child_done, child_sleep, order + [ident])
            sleeping.add(ident)

    visit(initial_state(case), set(), set(), [])
    return traces, claims


def outcome(s):
    nodes = [{k: n[k] for k in sorted(n)} for n in sorted(s["nodes"], key=lambda x: x["id"])]
    q = s["query"]
    return {"final": {"active_scope": s["active_scope"], "complete": s["complete"],
                       "predicate_epoch": s["predicate_epoch"], "scope_epoch": s["scope_epoch"],
                       "nodes": nodes},
            "query": copy.deepcopy(q), "admission": copy.deepcopy(s["admission"])}


def verify_freeze():
    frozen = read_json(ROOT / "FREEZE.json")
    for rel, expected in frozen["sha256"].items():
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"freeze mismatch: {rel}")
    if frozen["base_commit"] != BASE or frozen["allocation_id"] != RUN_ID:
        raise SystemExit("freeze anchor mismatch")
    return frozen


def run():
    started = datetime.now(timezone.utc).isoformat()
    frozen = verify_freeze()
    model_path = ROOT / "MODEL.json"
    model = read_json(model_path)
    if hashlib.sha256(model_path.read_bytes()).hexdigest() != frozen["model_sha256"]:
        raise SystemExit("model hash mismatch")
    all_runs = {"exhaustive": {}, "node_only_dpor": {}, "predicate_dpor": {},
                "mutant_missing_predicate": {}, "mutant_cross_scope": {},
                "mutant_unknown_independent": {}}
    for case in model["cases"]:
        for key, rows in (("exhaustive", exhaustive(case)),):
            all_runs[key][case["id"]] = rows
        for key, mode in (("node_only_dpor", "node_only"),
                          ("predicate_dpor", "predicate"),
                          ("mutant_missing_predicate", "node_only"),
                          ("mutant_cross_scope", "mutant_cross_scope"),
                          ("mutant_unknown_independent", "mutant_unknown_independent")):
            rows, claims = sleep_set(case, mode)
            all_runs[key][case["id"]] = rows
            # Keep dependency claims for the two sound/intended relations and all mutants.
            if key != "node_only_dpor":
                all_runs.setdefault("claims", {}).setdefault(key, {})[case["id"]] = claims
    raw = {"schema": "gui-query-dpor-candidate-raw-v1", "allocation_id": RUN_ID,
           "base_commit": BASE, "model_sha256": frozen["model_sha256"],
           "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
           "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
           "formal_candidate_runs": 1, "runs": all_runs}
    (ROOT / "candidate_raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print("candidate_complete", "cases", len(model["cases"]), "raw_bytes",
          (ROOT / "candidate_raw.json").stat().st_size)


if __name__ == "__main__":
    run()
