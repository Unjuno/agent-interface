"""Finite synthetic proposal-concurrency fixture for Issue #5318."""
import json

POLICIES = ("RAW_COALESCE", "GLOBAL_SERIAL", "SEMANTIC_SERIALIZABILITY",
            "OPTIMISTIC_VALIDATE_COMMIT", "UNKNOWN_AS_CONFLICT")


def tx(txid, reads, writes, kind, key=None, value=None, delta=None, quality="EXACT",
       effect="REVERSIBLE", delay=0, commute_rule=None, guard=None):
    return {"id": txid, "reads": list(reads), "writes": list(writes), "kind": kind,
            "key": key, "value": value, "delta": delta, "quality": quality,
            "effect": effect, "delay": delay, "commute_rule": commute_rule, "guard": guard}


def scenarios():
    return [
        {"id": "disjoint", "initial": {"a": 0, "b": 0}, "tx": [
            tx("p1", [], ["a"], "set", "a", value=1), tx("p2", [], ["b"], "set", "b", value=1)]},
        {"id": "commuting_add", "initial": {"x": 0}, "tx": [
            tx("p1", [], ["x"], "add", "x", delta=1, commute_rule="integer-add-v1"),
            tx("p2", [], ["x"], "add", "x", delta=2, commute_rule="integer-add-v1")]},
        {"id": "same_set", "initial": {"x": 0}, "tx": [
            tx("p1", [], ["x"], "set", "x", value=1), tx("p2", [], ["x"], "set", "x", value=2)]},
        {"id": "write_skew_cycle", "initial": {"x": 0, "y": 0}, "tx": [
            tx("p1", ["x"], ["y"], "conditional_set", "y", value=1, guard="x-zero"),
            tx("p2", ["y"], ["x"], "conditional_set", "x", value=1, guard="y-zero")]},
        {"id": "unknown_overlap", "initial": {"left": 0, "right": 0}, "tx": [
            tx("p1", ["left"], ["right"], "conditional_set", "right", value=1,
               guard="left-zero", quality="UNKNOWN"),
            tx("p2", [], ["left"], "set", "left", value=1)]},
        {"id": "delayed_irreversible", "initial": {"ticket": 0, "log": 0}, "tx": [
            tx("p1", [], ["ticket"], "set", "ticket", value=1, effect="IRREVERSIBLE", delay=2),
            tx("p2", ["ticket"], ["log"], "conditional_set", "log", value=1,
               guard="ticket-one", delay=1)]},
    ]


def apply_one(state, item, reads=None):
    reads = state if reads is None else reads
    if item["kind"] == "set":
        state[item["key"]] = item["value"]
    elif item["kind"] == "add":
        state[item["key"]] += item["delta"]
    elif item["kind"] == "conditional_set":
        guard_key = item["reads"][0]
        if item["guard"].endswith("zero") and reads[guard_key] == 0:
            state[item["key"]] = item["value"]
        elif item["guard"].endswith("one") and reads[guard_key] == 1:
            state[item["key"]] = item["value"]


def run_serial(initial, transactions):
    state = dict(initial)
    for item in transactions:
        apply_one(state, item)
    return state


def run_parallel(initial, transactions):
    snapshot = dict(initial)
    state = dict(initial)
    writes = []
    for item in transactions:
        local = dict(snapshot)
        apply_one(local, item, snapshot)
        writes.append((item, local))
    for key in snapshot:
        writers = [(item, local) for item, local in writes if key in item["writes"] and local[key] != snapshot[key]]
        if len(writers) > 1 and all(item["kind"] == "add" and item["commute_rule"] == "integer-add-v1"
                                    for item, _ in writers):
            state[key] = snapshot[key] + sum(item["delta"] for item, _ in writers)
        elif writers:
            state[key] = writers[-1][1][key]
    return state


def conflict(a, b):
    if a["quality"] != "EXACT" or b["quality"] != "EXACT":
        return True
    aw, bw = set(a["writes"]), set(b["writes"])
    ar, br = set(a["reads"]), set(b["reads"])
    if aw & br or bw & ar:
        return True
    if aw & bw:
        same_trusted_commutative_resource = (
            a["kind"] == b["kind"] == "add" and a["commute_rule"] == b["commute_rule"] == "integer-add-v1")
        return not same_trusted_commutative_resource
    return False


def cycle(a, b):
    return bool(set(a["writes"]) & set(b["reads"]) and set(b["writes"]) & set(a["reads"]))


def serial_outcomes(case):
    first, second = case["tx"]
    return [run_serial(case["initial"], [first, second]),
            run_serial(case["initial"], [second, first])]


def decide(case, policy):
    first, second = case["tx"]
    if policy == "GLOBAL_SERIAL":
        return "SERIALIZE", run_serial(case["initial"], [first, second]), [first["id"], second["id"]]
    if policy == "RAW_COALESCE":
        if first["key"] == second["key"] and first["kind"] == second["kind"]:
            return "COALESCE", run_serial(case["initial"], [first]), [first["id"]]
        return "PARALLEL", run_parallel(case["initial"], [first, second]), [first["id"], second["id"]]
    if policy == "OPTIMISTIC_VALIDATE_COMMIT":
        if conflict(first, second):
            return "ABORT", dict(case["initial"]), []
        return "PARALLEL", run_parallel(case["initial"], [first, second]), [first["id"], second["id"]]
    if policy == "UNKNOWN_AS_CONFLICT" and (first["quality"] != "EXACT" or second["quality"] != "EXACT"):
        return "DEFER", dict(case["initial"]), []
    if cycle(first, second):
        return "ABORT", dict(case["initial"]), []
    if conflict(first, second):
        order = [first, second]
        return "SERIALIZE", run_serial(case["initial"], order), [x["id"] for x in order]
    return "PARALLEL", run_parallel(case["initial"], [first, second]), [first["id"], second["id"]]


def run():
    for case in scenarios():
        for policy in POLICIES:
            decision, final, committed = decide(case, policy)
            row = {"scenario": case["id"], "policy": policy, "decision": decision,
                   "initial": case["initial"], "transactions": case["tx"],
                   "final": final, "committed": committed,
                   "legal_serial_finals": serial_outcomes(case),
                   "parallel_count": int(decision == "PARALLEL"),
                   "delayed_effects": [t["id"] for t in case["tx"] if t["delay"] > 0],
                   "irreversible_sources": [t["id"] for t in case["tx"] if t["effect"] == "IRREVERSIBLE"]}
            print(json.dumps(row, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    run()

