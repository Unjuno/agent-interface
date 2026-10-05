"""Independent raw socket transcript reconstruction; no study/transport imports."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

MODES = {"independent", "predicate_inflight", "scope_inflight", "scope_cache"}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def audit(raw, fixtures):
    require(type(raw) is dict and set(raw) == {"schema", "environment", "trials"}, "raw schema")
    require(raw["schema"] == "socket-scope-transfer-v1", "schema identity")
    require(type(raw["trials"]) is list, "trials type")
    env = raw["environment"]
    require(type(env) is dict and set(env) == {"python", "system", "machine"} and all(type(x) is str and x for x in env.values()), "environment")
    cases = {c["id"]: c for c in fixtures["cases"]}
    expected = set(itertools.product(cases, MODES))
    seen = set()
    invocations = {m: 0 for m in MODES}
    mismatches = {m: 0 for m in MODES}
    callers_count = 0
    details = []
    for trial in raw["trials"]:
        require(type(trial) is dict and set(trial) == {"case_id", "mode", "callers", "server_events", "transport_errors", "active_server_threads_after_cleanup", "producer_threads_joined"}, "trial schema")
        identity = (trial["case_id"], trial["mode"])
        require(identity in expected and identity not in seen, "trial coverage")
        seen.add(identity)
        case, mode = cases[identity[0]], identity[1]
        require(trial["transport_errors"] == [], "transport error")
        require(type(trial["active_server_threads_after_cleanup"]) is int and trial["active_server_threads_after_cleanup"] == 0 and trial["producer_threads_joined"] is True, "cleanup")
        expected_waiters = {r["id"]: (index, r["scope"]) for index, wave in enumerate(case["waves"]) for r in wave}
        actual_waiters = {}
        received, sent, clients = {}, {}, {}
        require(type(trial["callers"]) is list, "callers type")
        require(type(trial["server_events"]) is list, "events type")
        prior_tick = -1
        for index, event in enumerate(trial["server_events"]):
            require(type(event) is dict, "event type")
            tag = event.get("event")
            require(tag in {"server_received", "server_sent", "client_received"}, "event kind")
            fields = {"index", "event", "monotonic_ns", "call_id", "wire_hex", "sha256", "request" if tag == "server_received" else "response"}
            require(set(event) == fields, "event schema")
            require(type(event["index"]) is int and event["index"] == index, "event index")
            tick = event["monotonic_ns"]
            require(type(tick) is int and tick >= prior_tick, "clock order")
            prior_tick = tick
            blob = bytes.fromhex(event["wire_hex"])
            require(hashlib.sha256(blob).hexdigest() == event["sha256"] and blob.endswith(b"\n") and len(blob) <= 8192, "wire hash/bound")
            decoded = json.loads(blob)
            stored = event["request" if tag == "server_received" else "response"]
            require(decoded == stored and decoded["call_id"] == event["call_id"], "wire decoding")
            require(type(event["call_id"]) is str and event["call_id"].startswith("rpc-"), "call identity type")
            if tag == "server_received":
                require(type(stored) is dict and set(stored) == {"call_id", "scope"}, "request schema")
                require(type(stored["scope"]) is dict and set(stored["scope"]) == set(fixtures["scope_fields"]) and all(type(v) is str and v for v in stored["scope"].values()), "request scope types")
            bucket = received if tag == "server_received" else sent if tag == "server_sent" else clients
            require(event["call_id"] not in bucket, "duplicate transport event")
            bucket[event["call_id"]] = stored
        require(set(received) == set(sent) == set(clients), "complete transport triples")
        for call_id in received:
            response = sent[call_id]
            require(set(response) == {"call_id", "scope", "role", "answer"} and response["answer"] is True and response["role"] == "read_only_descriptive", "response role/schema")
            require(response == clients[call_id] and response["scope"] == received[call_id]["scope"], "response source identity")
        for caller in trial["callers"]:
            require(type(caller) is dict and set(caller) == {"id", "wave", "required_scope", "call_id", "response", "descriptive_match", "role"}, "caller schema")
            require(caller["id"] in expected_waiters and caller["id"] not in actual_waiters, "waiter coverage")
            wave, required_scope = expected_waiters[caller["id"]]
            require(type(caller["wave"]) is int and caller["wave"] == wave and caller["required_scope"] == required_scope, "waiter request binding")
            require(caller["call_id"] in clients and caller["response"] == clients[caller["call_id"]] and caller["role"] == "read_only_descriptive", "caller transport binding")
            match = caller["response"]["scope"] == required_scope
            require(type(caller["descriptive_match"]) is bool and caller["descriptive_match"] is match, "per-waiter descriptive gate")
            actual_waiters[caller["id"]] = caller
            mismatches[mode] += not match
        require(set(actual_waiters) == set(expected_waiters), "missing waiter")
        # Reconstruct equivalence using complete field vectors, not producer key code.
        # Completed-wave cache reuse is a deliberately different lifetime contract.
        cohorts = {}
        for waiter, (wave, scope) in expected_waiters.items():
            if mode == "independent":
                key = (waiter,)
            elif mode == "predicate_inflight":
                key = (wave, scope["predicate"])
            else:
                key = tuple(sorted(scope.items()))
                if mode == "scope_inflight":
                    key = (wave, key)
            cohorts.setdefault(key, []).append(waiter)
        require(len(received) == len(cohorts), "invocation count")
        seen_call_ids = set()
        for waiters in cohorts.values():
            ids = {actual_waiters[w]["call_id"] for w in waiters}
            require(len(ids) == 1 and not (ids & seen_call_ids), "coalescing equivalence")
            call_id = next(iter(ids))
            require(received[call_id]["scope"] == expected_waiters[waiters[0]][1], "first owner request")
            seen_call_ids.update(ids)
        require(seen_call_ids == set(received), "extra producer call")
        invocations[mode] += len(received)
        callers_count += len(expected_waiters)
        details.append(dict(case_id=identity[0], mode=mode, actual_invocations=len(received), callers=len(actual_waiters)))
    require(seen == expected, "missing trial")
    require(invocations == {"independent": 14, "predicate_inflight": 7, "scope_inflight": 11, "scope_cache": 10}, "frozen total calls")
    require(mismatches == {"independent": 0, "predicate_inflight": 4, "scope_inflight": 0, "scope_cache": 0}, "frozen scope control outcomes")
    return dict(status="PASS_SOCKET_SCOPE_TRANSFER_SCOPED", trials=len(seen), callers=callers_count,
                actual_socket_invocations=invocations, wrong_scope_descriptive_refusals=mismatches,
                details=sorted(details, key=lambda x: (x["case_id"], x["mode"])))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("fixtures", type=Path)
    p.add_argument("raw", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = audit(json.loads(args.raw.read_text()), json.loads(args.fixtures.read_text()))
    with args.output.open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "details"}, sort_keys=True))
