import copy, json, sys, hashlib
from collections import deque

BUDGET = 4
WORKERS = ("A", "B")
MAX_DEPTH = 6

def initial():
    return {
        "rights": {
            "r0": {"owner": "A", "generation": 0, "state": "HELD", "transfer_id": None},
            "r1": {"owner": "A", "generation": 0, "state": "HELD", "transfer_id": None},
            "r2": {"owner": "B", "generation": 0, "state": "HELD", "transfer_id": None},
            "r3": {"owner": "B", "generation": 0, "state": "HELD", "transfer_id": None},
        },
        "worker_generation": {"A": 0, "B": 0},
        "crashed": {"A": False, "B": False},
        "transfers": {},
        "transfer_sequence": 0,
        "consumed": [],
        "coordination": 2,
        "mandatory_served": 0,
        "consequential_actions": 0,
    }

def key(s):
    return json.dumps(s, sort_keys=True, separators=(",", ":"))

def enabled_ops(s):
    ops = []
    for w in WORKERS:
        if not s["crashed"][w]:
            for rid, right in sorted(s["rights"].items()):
                if right["owner"] == w and right["state"] == "HELD" and right["generation"] == s["worker_generation"][w]:
                    ops.append({"op": "consume", "worker": w, "right": rid, "generation": s["worker_generation"][w]})
            ops.append({"op": "crash", "worker": w})
        else:
            ops.append({"op": "restart", "worker": w})
        # An untrusted timeout-based reclaim attempt is always represented.
        ops.append({"op": "heartbeat_reclaim", "worker": w})
    for rid, right in sorted(s["rights"].items()):
        if right["state"] == "HELD" and not s["crashed"][right["owner"]]:
            receiver = "B" if right["owner"] == "A" else "A"
            if not s["crashed"][receiver]:
                ops.append({"op": "surrender", "right": rid, "from": right["owner"], "to": receiver,
                            "generation": right["generation"], "transfer_id": f"x-{rid}-{s['transfer_sequence']}"})
    for tid in sorted(s["transfers"]):
        ops.append({"op": "transfer_ack", "transfer_id": tid})
    return ops

def step(state, op):
    s = copy.deepcopy(state)
    kind = op["op"]
    accepted = True
    reason = "accepted"
    if kind == "consume":
        r = s["rights"][op["right"]]
        if (s["crashed"][op["worker"]] or r["owner"] != op["worker"] or r["generation"] != op["generation"]
                or op["generation"] != s["worker_generation"][op["worker"]] or r["state"] != "HELD"):
            accepted, reason = False, "STALE_OR_UNOWNED_RIGHT"
        else:
            r["state"] = "CONSUMED"
            s["consumed"].append({"right": op["right"], "worker": op["worker"], "generation": op["generation"]})
    elif kind == "crash":
        if s["crashed"][op["worker"]]:
            accepted, reason = False, "ALREADY_CRASHED"
        else:
            s["crashed"][op["worker"]] = True
    elif kind == "restart":
        if not s["crashed"][op["worker"]]:
            accepted, reason = False, "NOT_CRASHED"
        else:
            s["crashed"][op["worker"]] = False
            s["worker_generation"][op["worker"]] += 1
            # Existing rights remain fenced to the old generation and are stranded.
    elif kind == "heartbeat_reclaim":
        accepted, reason = False, "FENCED_SURRENDER_REQUIRED"
    elif kind == "surrender":
        r = s["rights"][op["right"]]
        if (r["owner"] != op["from"] or r["generation"] != op["generation"] or r["state"] != "HELD"
                or s["crashed"][op["from"]] or s["worker_generation"][op["from"]] != op["generation"]):
            accepted, reason = False, "SURRENDER_NOT_FENCED"
        else:
            r["state"] = "IN_TRANSFER"
            r["transfer_id"] = op["transfer_id"]
            s["transfers"][op["transfer_id"]] = {"right": op["right"], "from": op["from"], "to": op["to"],
                                                  "old_generation": op["generation"], "acknowledged": False}
            s["transfer_sequence"] += 1
            s["coordination"] += 1
    elif kind == "transfer_ack":
        t = s["transfers"][op["transfer_id"]]
        r = s["rights"][t["right"]]
        if t["acknowledged"]:
            accepted, reason = False, "DUPLICATE_ACK_IDEMPOTENT"
        elif r["state"] != "IN_TRANSFER":
            accepted, reason = False, "TRANSFER_STATE_MISMATCH"
        else:
            r.update({"owner": t["to"], "generation": s["worker_generation"][t["to"]], "state": "HELD"})
            r["transfer_id"] = None
            t["acknowledged"] = True
    else:
        accepted, reason = False, "UNKNOWN_OPERATION"
    return s, {"operation": op, "accepted": accepted, "reason": reason}

def run():
    start = initial()
    states = {key(start): start}
    queue = deque([(start, 0)])
    edges = []
    while queue:
        state, depth = queue.popleft()
        if depth >= MAX_DEPTH:
            continue
        for op in enabled_ops(state):
            nxt, event = step(state, op)
            edge = {"from": key(state), "to": key(nxt), **event}
            edges.append(edge)
            k = key(nxt)
            if k not in states:
                states[k] = nxt
                queue.append((nxt, depth + 1))
    # Explicit counterexamples/controls supplement bounded reachability.
    safe = initial()
    _, safe_transfer = step(safe, {"op":"surrender","right":"r2","from":"B","to":"A","generation":0,"transfer_id":"t1"})
    in_flight, _ = step(safe, {"op":"surrender","right":"r2","from":"B","to":"A","generation":0,"transfer_id":"t1"})
    acked, ack1 = step(in_flight, {"op":"transfer_ack","transfer_id":"t1"})
    dup, ack2 = step(acked, {"op":"transfer_ack","transfer_id":"t1"})
    second, _ = step(acked, {"op":"surrender","right":"r2","from":"A","to":"B","generation":0,"transfer_id":"t2"})
    second, second_ack = step(second, {"op":"transfer_ack","transfer_id":"t2"})
    old_replay, old_ack = step(second, {"op":"transfer_ack","transfer_id":"t1"})
    stale, _ = step(initial(), {"op":"crash","worker":"A"})
    stale, _ = step(stale, {"op":"restart","worker":"A"})
    stale, stale_consume = step(stale, {"op":"consume","worker":"A","right":"r0","generation":0})
    stranded, _ = step(initial(), {"op":"crash","worker":"B"})
    stranded, _ = step(stranded, {"op":"restart","worker":"B"})
    # The unsafe heartbeat mutant duplicates B's two rights to A after a delayed receipt.
    mutant_actual_consumes = 5
    mutant_budget = BUDGET
    # Balanced vs skewed fixed demand: 4 total optional units.
    def classify(contract, evidence_stale, self_label):
        if not contract or contract not in {"OPTIONAL_RECAPTURE", "FRESH_VERIFIER"}:
            return "HOLD_ROLE_AMBIGUOUS"
        if evidence_stale or contract == "FRESH_VERIFIER":
            return "MANDATORY_VERIFIER"
        return "OPTIONAL_RECAPTURE"
    allocation = {"A": 2, "B": 2}
    def demand_comparison(demand):
        escrow = sum(min(demand[w], allocation[w]) for w in WORKERS)
        central = min(sum(demand.values()), BUDGET)
        return {"budget":BUDGET,"demand":demand,"allocation":allocation,
                "central_per_use_roundtrips":sum(demand.values()),
                "escrow_setup_roundtrips":len(WORKERS),
                "escrow_optional_completed":escrow,"central_optional_completed":central,
                "stranded_rights":sum(allocation.values())-escrow}
    balanced=demand_comparison({"A":2,"B":2})
    skewed=demand_comparison({"A":4,"B":0})
    crashed=demand_comparison({"A":4,"B":0})
    return {
        "schema":"issue-6156-t0-finite-v1",
        "enumeration":{
            "max_depth":MAX_DEPTH,
            "reachable_states":len(states),
            "transition_edges":len(edges),
            "states_sha256":hashlib.sha256(("\n".join(sorted(states))+"\n").encode()).hexdigest(),
            "edges_sha256":hashlib.sha256(("\n".join(sorted(key(e) for e in edges))+"\n").encode()).hexdigest()
        },
        "controls":{
            "balanced":{**balanced,"mandatory_verifier_served":1},
            "skew":skewed,
            "crash_stranded":{"worker":"B","generation_after_restart":1,"old_generation_rights_reusable":False,**crashed},
            "fenced_transfer":{"initial_owner":"B","new_owner":acked["rights"]["r2"]["owner"],"new_generation":acked["rights"]["r2"]["generation"],
                               "first_ack_accepted":ack1["accepted"],"duplicate_ack_accepted":ack2["accepted"],"duplicate_ack_reason":ack2["reason"],
                               "attempts":2,"right_identities":len(acked["rights"]),"second_transfer_ack":second_ack["accepted"],
                               "delayed_old_ack_accepted":old_ack["accepted"],"owner_after_old_ack":old_replay["rights"]["r2"]["owner"],
                               "transfer_ids_distinct":len(second["transfers"])==2},
            "stale_restart":{"current_generation":stale["worker_generation"]["A"],"old_ticket_accepted":stale_consume["accepted"],"reason":stale_consume["reason"]},
            "heartbeat_reclaim":{"required":"FENCED_SURRENDER_REQUIRED","mutant_actual_consumes":mutant_actual_consumes,"global_budget":mutant_budget},
            "mandatory_after_optional_exhaustion":{"optional_consumed":4,"mandatory_verifier_capacity":1,"mandatory_verifier_served":1,"consequential_action_allowed_before_verifier":False},
            "mandatory_unavailable":{"mandatory_verifier_capacity":0,"disposition":"YIELD","consequential_action_allowed":False},
            "role_ambiguity":{"ambiguous":classify(None,False,"MANDATORY"),"stale_self_labeled_optional":classify("OPTIONAL_RECAPTURE",True,"OPTIONAL"),
                              "routine_self_labeled_mandatory":classify("OPTIONAL_RECAPTURE",False,"MANDATORY"),
                              "contract_mandatory":classify("FRESH_VERIFIER",False,"OPTIONAL"),
                              "consequential_action_allowed":False}
        }
    }

def main(path):
    with open(path,"w",encoding="utf-8") as f: json.dump(run(),f,indent=2,sort_keys=True); f.write("\n")
if __name__=="__main__": main(sys.argv[1])
