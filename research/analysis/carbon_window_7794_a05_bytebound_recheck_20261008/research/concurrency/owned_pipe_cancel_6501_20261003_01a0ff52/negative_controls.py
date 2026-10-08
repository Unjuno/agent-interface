"""Predeclared, copied-raw controls; never replay the candidate."""
import copy
import hashlib
import json
import pathlib
import sys

import audit


NAMES = ("read_before_write", "wrong_native_thread", "closed_fd_reported_open", "boolean_fd",
         "terminal_before_cancel_request", "harness_release_relabelled_primary", "missing_control_ack",
         "exit_before_read_close", "aggregate_boolean_alias", "native_thread_still_alive",
         "wrong_control_byte", "duplicate_close", "wrong_post_close_syscall", "boolean_write_receipt",
         "boolean_footer_count", "unknown_trial_field")


def event(row, kind, **where):
    return next(e for e in row["events"] if e["kind"] == kind and all(e.get(k) == v for k, v in where.items()))


def move_before(row, target, prerequisite):
    row["events"].remove(target)
    row["events"].insert(row["events"].index(prerequisite), target)


def mutate(records, name):
    records = copy.deepcopy(records)
    cancel, close, control = records[1], records[3], records[5]
    if name == "read_before_write":
        move_before(cancel, event(cancel, "read_return"), event(cancel, "write_requested"))
    elif name == "wrong_native_thread":
        event(close, "blocked_observed", label="after_action")["observation"]["tid"] += 1
    elif name == "closed_fd_reported_open":
        close["checkpoint"]["fds"]["data_r"]["open"] = True
        event(close, "primary_checkpoint")["state"]["fds"]["data_r"]["open"] = True
    elif name == "boolean_fd":
        event(cancel, "fd_owned", resource="data_r")["fd"] = True
    elif name == "terminal_before_cancel_request":
        move_before(cancel, event(cancel, "wrapper_cancelled"), event(cancel, "cancel_requested"))
    elif name == "harness_release_relabelled_primary":
        for e in cancel["events"]:
            if e["kind"] in {"write_requested", "write_return"}:
                e["purpose"] = "primary_data"
    elif name == "missing_control_ack":
        control["events"].remove(event(control, "control_ack"))
    elif name == "exit_before_read_close":
        move_before(control, event(control, "worker_exit"), event(control, "fd_closed", resource="data_r"))
    elif name == "aggregate_boolean_alias":
        cancel["checkpoint"]["future_done"] = 0
    elif name == "native_thread_still_alive":
        event(cancel, "executor_joined")["thread_alive"] = True
    elif name == "wrong_control_byte":
        event(control, "control_ack")["hex"] = "44"
    elif name == "duplicate_close":
        e = event(close, "fd_closed", resource="data_r")
        close["events"].insert(close["events"].index(e) + 1, copy.deepcopy(e))
    elif name == "wrong_post_close_syscall":
        event(close, "blocked_observed", label="after_action")["observation"]["syscall_nr"] = 22
    elif name == "boolean_write_receipt":
        event(cancel, "write_return")["count"] = True
    elif name == "boolean_footer_count":
        records[-1]["trials"] = True
    elif name == "unknown_trial_field":
        cancel["claimed_success"] = True
    else:
        raise ValueError(name)
    for row in records[1:-1]:
        for i, e in enumerate(row["events"]):
            e["seq"] = i
    return records


def main():
    root = pathlib.Path(__file__).resolve().parent
    raw = pathlib.Path(sys.argv[1]).read_bytes()
    records = [json.loads(line) for line in raw.decode().splitlines()]
    freeze_raw = (root / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    pin = hashlib.sha256(freeze_raw).hexdigest()
    baseline = audit.audit(records, pin, freeze["environment"])
    if baseline["errors"]:
        raise RuntimeError("baseline must pass before copied controls: " + str(baseline))
    out = pathlib.Path(sys.argv[2])
    out.mkdir(exist_ok=False)
    results = []
    for name in NAMES:
        variant = mutate(records, name)
        data = ("\n".join(json.dumps(r, sort_keys=True) for r in variant) + "\n").encode()
        if data == raw:
            raise RuntimeError("ineffective control: " + name)
        (out / (name + ".jsonl")).write_bytes(data)
        result = audit.audit(variant, pin, freeze["environment"])
        results.append({"name": name, "sha256": hashlib.sha256(data).hexdigest(), **result})
    summary = {"classification": "copied raw-only negative controls, no formal replay", "baseline": baseline,
               "controls": results, "rejected": sum(bool(r["errors"]) for r in results)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"baseline": baseline["status"], "rejected": summary["rejected"], "total": len(results)}))
    return 0 if summary["rejected"] == len(NAMES) else 2


if __name__ == "__main__":
    raise SystemExit(main())
