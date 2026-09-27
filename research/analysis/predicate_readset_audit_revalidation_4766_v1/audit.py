import copy
import json
import sys
from pathlib import Path


POLICIES = ("FULL_RECOMPUTE", "DYNAMIC_READSET", "STATIC_DECLARED", "STATIC_ALL")
PREDICATES = ("READY_TO_SUBMIT", "TARGET_MATCH")


def expected_value(snapshot, predicate):
    context = snapshot["context"]
    if predicate == "READY_TO_SUBMIT":
        if context["form"]["mode"] != "submit":
            return "DEFER"
        return "ALLOW" if context["risk"]["level"] == "safe" else "YIELD"
    return context["target"]["id"] == context["intent"]["target_id"]


def expected_reads(snapshot, predicate):
    if predicate == "TARGET_MATCH":
        return ["intent", "intent.target_id", "target", "target.id"]
    if snapshot["context"]["form"]["mode"] == "submit":
        return ["form", "form.mode", "risk", "risk.level"]
    return ["form", "form.mode"]


def _errors(trace, rows):
    errors = []
    states = trace.get("states", [])
    expected_keys = {
        (policy, state["id"], predicate)
        for policy in POLICIES for state in states for predicate in PREDICATES
    }
    actual_keys = [(r.get("policy"), r.get("state"), r.get("predicate")) for r in rows]
    if len(rows) != len(expected_keys) or set(actual_keys) != expected_keys:
        errors.append("row_denominator_or_identity")
    if len(actual_keys) != len(set(actual_keys)):
        errors.append("duplicate_row")

    by_key = {key: row for key, row in zip(actual_keys, rows)}
    for policy in POLICIES:
        for predicate in PREDICATES:
            previous_oracle = None
            previous_row = None
            for state in states:
                key = (policy, state["id"], predicate)
                row = by_key.get(key)
                if row is None:
                    continue
                oracle = expected_value(state, predicate)
                if row.get("oracle_value") != oracle:
                    errors.append("oracle_value_mismatch:" + ":".join(key))
                if row.get("generations") != state.get("generations"):
                    errors.append("generation_snapshot_mismatch:" + ":".join(key))
                if row.get("action") in ("MISS", "RECOMPUTE") and row.get("value") != oracle:
                    errors.append("recomputed_value_mismatch:" + ":".join(key))
                if policy == "DYNAMIC_READSET" and row.get("value") != oracle:
                    errors.append("dynamic_value_mismatch:" + ":".join(key))
                if policy == "DYNAMIC_READSET" and (
                    not isinstance(row.get("reads"), list)
                    or row.get("reads") != expected_reads(state, predicate)
                ):
                    errors.append("read_paths_mismatch:" + ":".join(key))
                hit = row.get("cache_hit")
                if not isinstance(hit, bool) or hit != (row.get("action") == "HIT"):
                    errors.append("hit_action_mismatch:" + ":".join(key))
                expected_unsafe = row.get("action") == "HIT" and row.get("value") != oracle
                if row.get("unsafe_reuse") is not expected_unsafe:
                    errors.append("unsafe_reuse_flag_mismatch:" + ":".join(key))
                expected_false_invalidation = (
                    row.get("action") == "MISS" and previous_oracle is not None
                    and previous_oracle == oracle
                )
                if row.get("false_invalidation") is not expected_false_invalidation:
                    errors.append("false_invalidation_flag_mismatch:" + ":".join(key))
                if policy == "DYNAMIC_READSET" and row.get("action") == "HIT" and previous_row:
                    if row.get("reads") != previous_row.get("reads"):
                        errors.append("hit_readset_changed_without_recompute:" + ":".join(key))
                previous_oracle = oracle
                previous_row = row

    def row(policy, state, predicate):
        return by_key.get((policy, state, predicate), {})

    # The incomplete static declaration must miss the hidden risk transition.
    s2 = row("STATIC_DECLARED", "s2", "READY_TO_SUBMIT")
    if not (s2.get("cache_hit") and s2.get("value") != s2.get("oracle_value")):
        errors.append("static_negative_control_not_discriminating")
    d2 = row("DYNAMIC_READSET", "s2", "READY_TO_SUBMIT")
    if d2.get("action") != "MISS" or d2.get("reads") != ["form", "form.mode", "risk", "risk.level"]:
        errors.append("dynamic_hidden_dependency_not_reacquired")

    # Risk changes while the predicate is on the preview branch and not read.
    d4 = row("DYNAMIC_READSET", "s4", "READY_TO_SUBMIT")
    if not (d4.get("cache_hit") and d4.get("value") == "DEFER"):
        errors.append("dynamic_irrelevant_branch_change_not_reused")
    for sid in ("s5", "s6"):
        target = row("DYNAMIC_READSET", sid, "TARGET_MATCH")
        if target.get("action") != "MISS":
            errors.append("dynamic_target_generation_not_invalidated:" + sid)

    dynamic_false = sum(bool(r.get("false_invalidation")) for r in rows if r.get("policy") == "DYNAMIC_READSET")
    static_all_false = sum(bool(r.get("false_invalidation")) for r in rows if r.get("policy") == "STATIC_ALL")
    dynamic_unsafe = sum(bool(r.get("unsafe_reuse")) for r in rows if r.get("policy") == "DYNAMIC_READSET")
    dynamic_unrelated_hits = sum(
        bool(r.get("cache_hit")) and r.get("policy") == "DYNAMIC_READSET"
        and r.get("state") in ("s1", "s4")
        for r in rows
    )
    if dynamic_unsafe != 0:
        errors.append("dynamic_unsafe_reuse")
    if dynamic_unrelated_hits < 2:
        errors.append("insufficient_dynamic_unrelated_hits")
    if static_all_false <= dynamic_false:
        errors.append("static_all_not_more_overinvalidating")
    return errors, {
        "rows": len(rows),
        "dynamic_unsafe_reuse": dynamic_unsafe,
        "dynamic_false_invalidations": dynamic_false,
        "dynamic_unrelated_hits": dynamic_unrelated_hits,
        "static_declared_unsafe_reuse": sum(bool(r.get("unsafe_reuse")) for r in rows if r.get("policy") == "STATIC_DECLARED"),
        "static_all_false_invalidations": static_all_false,
    }


def audit(trace, rows, controls=True):
    errors, metrics = _errors(trace, rows)
    rejected = 0
    if controls and not errors:
        mutations = []
        m = copy.deepcopy(rows); m.pop(0); mutations.append(m)
        m = copy.deepcopy(rows); m[-1] = copy.deepcopy(m[0]); mutations.append(m)
        m = copy.deepcopy(rows); m[0]["value"] = "CORRUPTED"; mutations.append(m)
        m = copy.deepcopy(rows); m[1]["oracle_value"] = "CORRUPTED"; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "DYNAMIC_READSET" and r["state"] == "s0" and r["predicate"] == "READY_TO_SUBMIT")["reads"] = ["form.mode"]; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "DYNAMIC_READSET" and r["state"] == "s1" and r["predicate"] == "READY_TO_SUBMIT")["action"] = "MISS"; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "DYNAMIC_READSET" and r["state"] == "s2" and r["predicate"] == "READY_TO_SUBMIT")["unsafe_reuse"] = True; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "DYNAMIC_READSET" and r["state"] == "s6" and r["predicate"] == "TARGET_MATCH")["generations"]["target.id"] = 0; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "STATIC_ALL" and r["state"] == "s4" and r["predicate"] == "TARGET_MATCH")["value"] = "CORRUPTED"; mutations.append(m)
        m = copy.deepcopy(rows); next(r for r in m if r["policy"] == "STATIC_DECLARED" and r["state"] == "s0" and r["predicate"] == "READY_TO_SUBMIT")["value"] = "CORRUPTED"; mutations.append(m)
        for mutated in mutations:
            if _errors(trace, mutated)[0]:
                rejected += 1
        if rejected != len(mutations):
            errors.append("mutation_controls_rejected:" + str(rejected) + "/" + str(len(mutations)))
    elif controls:
        errors.append("controls_skipped_due_to_base_errors")
    metrics["mutation_controls_rejected"] = rejected
    result = "PASS_DYNAMIC_READSET_SCOPED" if not errors else "HOLD_AUDIT_OR_MECHANISM"
    return {"result": result, "errors": errors, "metrics": metrics}


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: python -B audit.py TRACE.json RAW.jsonl AUDIT.json")
    trace = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if line]
    result = audit(trace, rows)
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
