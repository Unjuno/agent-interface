"""Raw-only reducer. Imports neither candidate nor its helpers."""
import datetime
import hashlib
import json
import pathlib
import sys

ALLOCATION = "6501-OWNED-PIPE-ORBSTACK-A01-20261003-01a0ff52-70ab"
PAIRS = [(p, c) for p in ("wrapper_cancel", "close_reader", "control_pipe")
         for c in ("cancel_blocked", "data_ready")]
FIELDS = {
    "fd_owned": {"resource", "fd"}, "fd_closed": {"resource", "fd", "actor"},
    "submit_requested": set(), "submit_return": set(), "worker_enter": {"tid"},
    "wrapper_wait": set(), "blocked_observed": {"label", "observation"},
    "cancel_requested": set(), "wrapper_cancelled": set(),
    "selector_ready": {"ready"}, "control_ack": {"hex"}, "read_return": {"hex"},
    "worker_exit": {"tid"}, "wrapper_delivered": {"value"},
    "write_requested": {"resource", "purpose", "hex"},
    "write_return": {"resource", "purpose", "count"},
    "primary_checkpoint": {"state"}, "future_collected": {"value"},
    "executor_joined": {"thread_alive"}, "final_checkpoint": {"state"},
}


def require(test, message):
    if not test:
        raise ValueError(message)


def exact_int(value):
    return type(value) is int


def check_state(state, owned, closed, cancelled, done, active):
    require(type(state) is dict and set(state) == {"wrapper_done", "wrapper_cancelled", "future_done",
            "future_cancelled", "worker_active", "fds"}, "state schema")
    expected = {"wrapper_done": True, "wrapper_cancelled": cancelled, "future_done": done,
                "future_cancelled": False, "worker_active": active}
    for name, value in expected.items():
        require(type(state[name]) is bool and state[name] is value, "state: " + name)
    require(type(state["fds"]) is dict and set(state["fds"]) == set(owned), "state resources")
    for name, fd in owned.items():
        item = state["fds"][name]
        require(type(item) is dict and set(item) == {"fd", "open"}, "FD state schema")
        require(exact_int(item["fd"]) and item["fd"] == fd, "FD state identity")
        require(type(item["open"]) is bool and item["open"] is (name not in closed), "FD state ownership")


def check_trial(row, index):
    require(type(row) is dict and set(row) == {"record", "index", "policy", "condition", "events",
            "checkpoint", "final", "failure"}, "trial schema")
    require(row["record"] == "trial" and exact_int(row["index"]) and row["index"] == index, "trial index")
    p, c = PAIRS[index]
    require((row["policy"], row["condition"]) == (p, c), "matrix pair")
    require(row["failure"] is None, "trial failure")
    events = row["events"]
    require(type(events) is list and 15 <= len(events) <= 40, "event cardinality")
    owned, closed, seen, writes = {}, set(), {}, {}
    before, after, tid = None, None, None
    cancelled = c == "cancel_blocked"
    expected_names = {"data_r", "data_w"} | ({"control_r", "control_w", "selector"} if p == "control_pipe" else set())
    expected_value = {"kind": "stopped", "hex": "43"} if p == "control_pipe" and cancelled else {"kind": "data", "hex": "44"}

    def occurred(kind):
        require(kind in seen, "causal prerequisite: " + kind)

    for seq, event in enumerate(events):
        require(type(event) is dict and type(event.get("kind")) is str, "event type")
        k = event["kind"]
        require(k in FIELDS and set(event) == {"seq", "kind"} | FIELDS[k], "event schema: " + k)
        require(exact_int(event["seq"]) and event["seq"] == seq, "event ordinal")
        if k not in {"fd_owned", "fd_closed", "blocked_observed", "write_requested", "write_return"}:
            require(k not in seen, "duplicate singleton: " + k)
        if k == "fd_owned":
            name, fd = event["resource"], event["fd"]
            require(type(name) is str and name in expected_names and name not in owned, "resource name")
            require(exact_int(fd) and fd >= 0 and fd not in owned.values(), "FD identity/type")
            owned[name] = fd
            if name == "selector":
                occurred("submit_requested")
        elif k == "fd_closed":
            name = event["resource"]
            require(type(name) is str and name in owned and name not in closed, "single owned close")
            require(exact_int(event["fd"]) and event["fd"] == owned[name], "close FD identity")
            actor = event["actor"]
            if name == "data_r" and p == "close_reader" and cancelled:
                require(actor == "caller", "caller close role")
                occurred("wrapper_cancelled")
            elif name in {"data_r", "control_r", "selector"}:
                require(actor == "worker", "worker close role")
                occurred("control_ack" if p == "control_pipe" and cancelled else "read_return")
            else:
                require(actor == "harness", "harness close role")
                occurred("executor_joined")
            closed.add(name)
        elif k == "submit_requested":
            require({"data_r", "data_w"}.issubset(owned), "submit resource setup")
        elif k == "submit_return":
            occurred("submit_requested")
        elif k == "worker_enter":
            occurred("submit_requested")
            require(set(owned) == expected_names and exact_int(event["tid"]) and event["tid"] > 0, "worker identity/resources")
            tid = event["tid"]
        elif k == "wrapper_wait":
            occurred("submit_return")
        elif k == "blocked_observed":
            occurred("worker_enter")
            occurred("wrapper_wait")
            label, obs = event["label"], event["observation"]
            require(type(obs) is dict and set(obs) == {"tid", "state", "wchan", "syscall_nr", "fd"}, "OS witness schema")
            for name in ("tid", "syscall_nr", "fd"):
                require(exact_int(obs[name]), "OS witness integer")
            require(obs["tid"] == tid and obs["state"] == "S", "blocked thread identity/state")
            require(obs["syscall_nr"] == (22 if p == "control_pipe" else 63), "blocked syscall")
            require(obs["fd"] == owned["selector" if p == "control_pipe" else "data_r"], "blocked FD")
            require(obs["wchan"] == ("__arm64_sys_epoll_pwait" if p == "control_pipe" else "anon_pipe_read"), "blocked wchan")
            if label == "before_action":
                require(before is None and "cancel_requested" not in seen and not writes, "pre-action OS witness")
                before = seq
            else:
                require(label == "after_action" and after is None and cancelled and p != "control_pipe", "post-action witness domain")
                occurred("wrapper_cancelled")
                if p == "close_reader":
                    require("data_r" in closed, "close precedes post-close blocked witness")
                after = seq
        elif k == "cancel_requested":
            require(cancelled and before is not None and not writes, "cancel trigger")
        elif k == "wrapper_cancelled":
            occurred("wrapper_wait")
            occurred("cancel_requested")
        elif k == "write_requested":
            purpose = event["purpose"]
            expected_purpose = "primary_stop" if p == "control_pipe" and cancelled else "harness_release" if cancelled else "primary_data"
            require(type(purpose) is str and purpose == expected_purpose and purpose not in writes, "write purpose/domain")
            name = "control_w" if purpose == "primary_stop" else "data_w"
            require(event["resource"] == name and name in owned and name not in closed, "write ownership")
            require(event["hex"] == ("43" if purpose == "primary_stop" else "44"), "write byte")
            require(before is not None, "write before blocked witness")
            if cancelled:
                occurred("wrapper_cancelled")
            if purpose == "harness_release":
                occurred("primary_checkpoint")
            writes[purpose] = {"resource": name, "returned": False}
        elif k == "write_return":
            purpose = event["purpose"]
            require(type(purpose) is str and purpose in writes and not writes[purpose]["returned"], "write return causality")
            require(event["resource"] == writes[purpose]["resource"] and exact_int(event["count"]) and event["count"] == 1, "write receipt")
            writes[purpose]["returned"] = True
        elif k == "selector_ready":
            require(p == "control_pipe" and event["ready"] == (["control"] if cancelled else ["data"]), "selector readiness")
            require(bool(writes), "selector ready before write request")
        elif k in {"control_ack", "read_return"}:
            require(event["hex"] == ("43" if k == "control_ack" else "44"), "read/ACK byte")
            purpose = "primary_stop" if k == "control_ack" else "harness_release" if cancelled else "primary_data"
            require(purpose in writes, "read before write request")
            if k == "control_ack":
                require(p == "control_pipe" and cancelled, "ACK domain")
            else:
                require(not (p == "control_pipe" and cancelled), "stop must not deliver data")
            if p == "control_pipe":
                occurred("selector_ready")
        elif k == "worker_exit":
            require(exact_int(event["tid"]) and event["tid"] == tid, "worker exit identity")
            require({"data_r", "control_r", "selector"}.intersection(owned).issubset(closed), "worker read resources closed before exit")
            occurred("control_ack" if p == "control_pipe" and cancelled else "read_return")
        elif k == "wrapper_delivered":
            require(not cancelled and event["value"] == expected_value, "wrapper delivery domain/value")
            occurred("wrapper_wait")
            occurred("worker_exit")
        elif k == "primary_checkpoint":
            require(before is not None and set(owned) == expected_names, "checkpoint ownership")
            if cancelled:
                occurred("wrapper_cancelled")
            else:
                occurred("wrapper_delivered")
            done = p == "control_pipe" or not cancelled
            if done:
                occurred("worker_exit")
                require(len(writes) == 1 and all(w["returned"] for w in writes.values()), "primary write receipt")
            else:
                require(after is not None and "worker_exit" not in seen and not writes, "blocked primary checkpoint")
            check_state(event["state"], owned, closed, cancelled, done, not done)
            require(json.dumps(row["checkpoint"], sort_keys=True) == json.dumps(event["state"], sort_keys=True), "checkpoint aggregate/event join")
        elif k == "future_collected":
            occurred("worker_exit")
            occurred("primary_checkpoint")
            require(event["value"] == expected_value, "Future value")
        elif k == "executor_joined":
            occurred("future_collected")
            require(type(event["thread_alive"]) is bool and event["thread_alive"] is False, "native thread joined")
        elif k == "final_checkpoint":
            occurred("executor_joined")
            require(closed == set(owned), "all owned FDs closed")
            check_state(event["state"], owned, closed, cancelled, True, False)
            require(json.dumps(row["final"], sort_keys=True) == json.dumps(event["state"], sort_keys=True) and seq == len(events) - 1, "final aggregate/event join")
        seen.setdefault(k, seq)
    required = {"submit_requested", "submit_return", "worker_enter", "wrapper_wait", "worker_exit",
                "primary_checkpoint", "future_collected", "executor_joined", "final_checkpoint"}
    required |= {"cancel_requested", "wrapper_cancelled"} if cancelled else {"wrapper_delivered"}
    required |= {"selector_ready"} if p == "control_pipe" else set()
    required |= {"control_ack"} if p == "control_pipe" and cancelled else {"read_return"}
    require(required.issubset(seen) and len(writes) == 1 and all(w["returned"] for w in writes.values()), "complete causal trace")


def audit(records, freeze_sha256, environment):
    errors = []
    try:
        require(type(records) is list and len(records) == 8, "header + six trials + footer")
        header, footer = records[0], records[-1]
        require(type(header) is dict and set(header) == {"record", "allocation", "started_utc", "environment", "freeze_sha256"}, "header schema")
        require(header["record"] == "header" and header["allocation"] == ALLOCATION, "allocation")
        require(header["freeze_sha256"] == freeze_sha256 and header["environment"] == environment, "frozen context")
        require(type(footer) is dict and set(footer) == {"record", "ended_utc", "trials", "status"}, "footer schema")
        require(footer["record"] == "footer" and footer["status"] == "COMPLETE" and exact_int(footer["trials"]) and footer["trials"] == 6, "first outcome completeness")
        start, end = datetime.datetime.fromisoformat(header["started_utc"]), datetime.datetime.fromisoformat(footer["ended_utc"])
        require(start.utcoffset() == datetime.timedelta(0) and end.utcoffset() == datetime.timedelta(0) and end >= start, "UTC receipt")
        for i, row in enumerate(records[1:-1]):
            check_trial(row, i)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        errors.append(str(exc))
    return {"status": "PASS_OWNED_PIPE_CANCEL_SCOPED" if not errors else "HOLD_EVIDENCE", "errors": errors,
            "trials": 6 if not errors else None}


def main():
    root = pathlib.Path(__file__).resolve().parent
    raw = pathlib.Path(sys.argv[1]).read_bytes()
    freeze_raw = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    try:
        records = [json.loads(line) for line in raw.decode().splitlines()]
        result = audit(records, hashlib.sha256(freeze_raw).hexdigest(), freeze["environment"])
    except (ValueError, UnicodeError) as exc:
        result = {"status": "HOLD_EVIDENCE", "errors": [str(exc)], "trials": None}
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    pathlib.Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
