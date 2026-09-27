#!/usr/bin/env python3
"""Independent raw-only auditor; never imports or executes study.py."""
import errno
import hashlib
import json
from pathlib import Path
import sys

MODES = ["PERIODIC_20MS", "PERIODIC_60MS", "ONESHOT_20MS", "ONESHOT_60MS",
         "DISARMED", "SHORT_READ", "REARM"]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value

def loads(data):
    return json.loads(data, object_pairs_hook=no_duplicates)

def integer(value):
    return type(value) is int

def check_case(envelope, spec, source_sha, byteorder):
    errors = []
    def need(test, message):
        if not test:
            errors.append(message)
    try:
        need(type(envelope["returncode"]) is int and envelope["returncode"] == 0, "worker exit")
        need(envelope["stderr"] == "", "worker stderr")
        need(envelope["index"] == spec["index"] and integer(envelope["index"]), "envelope identity")
        need(sha(envelope["stdout"].encode()) == envelope["stdout_sha256"], "stdout hash")
        row = loads(envelope["stdout"])
        for key in ("index", "rep", "mode"):
            need(row[key] == spec[key] and type(row[key]) is type(spec[key]), "row " + key)
        need(integer(row["pid"]) and row["pid"] > 0, "pid")
        need(row["source_sha256"] == source_sha, "worker source")
        need(row["byteorder"] == byteorder, "byteorder")
        need(row["result"] == "COMPLETE", "worker result")
        need(row["authority"] == "none" and type(row["gui_observations"]) is int and
             row["gui_observations"] == 0 and type(row["input_calls"]) is int and
             row["input_calls"] == 0, "authority")
        ev = row["events"]
        op = [e["op"] for e in ev]
        mode = spec["mode"]
        shape = {
            "DISARMED": ["create", "read", "close"],
            "SHORT_READ": ["create", "arm", "wait", "read", "read", "observe", "read", "close"],
            "REARM": ["create", "arm", "wait", "ready", "arm", "read", "wait", "read", "observe", "read", "close"]}
        if mode.startswith("PERIODIC"):
            expected = ["create", "arm", "wait", "read", "observe", "wait", "read", "observe", "close"]
        else:
            expected = shape.get(mode, ["create", "arm", "wait", "read", "observe", "read", "close"])
        need(op == expected, "event sequence")
        need(ev[0]["inheritable"] is False and ev[0]["initial"] == [0, 0] and
             all(integer(x) for x in ev[0]["initial"]), "new timer")
        need(ev[-1]["errno"] == errno.EBADF and integer(ev[-1]["errno"]), "descriptor cleanup")
        prev_time = 0
        arms, accumulated, callbacks = {}, {}, []
        successful, error_reads, waits = [], [], []
        for k, event in enumerate(ev):
            if event["op"] == "observe":
                t = event["time"]
                need(integer(t) and t >= prev_time, "callback clock")
                need(event["mock"] is True and event["history"] == "UNKNOWN" and event["authority"] == "none", "callback scope")
                need(k > 0 and ev[k-1]["op"] == "read" and ev[k-1]["errno"] == 0, "callback origin")
                need(event["generation"] == ev[k-1]["generation"] and integer(event["generation"]), "callback generation")
                callbacks.append(event)
                need(integer(event["receipt"]) and event["receipt"] == len(callbacks), "callback receipt")
                prev_time = t
                continue
            a, b = event["before"], event["after"]
            need(integer(a) and integer(b) and 0 < a <= b and a >= prev_time, "event clocks")
            prev_time = b
            if event["op"] == "arm":
                g, first, period = event["generation"], event["first"], event["period"]
                need(integer(g) and g == len(arms), "arm generation")
                need(integer(first) and first > b and 0 < first-a <= 50_000_000, "arm deadline")
                need(integer(period) and period == (2_000_000 if mode.startswith("PERIODIC") else 0), "arm period")
                need(len(event["old_timer"]) == 2 and all(integer(v) and v >= 0 for v in event["old_timer"]), "old timer format")
                arms[g], accumulated[g] = event, 0
            if event["op"] == "wait":
                need(integer(event["target"]) and b >= event["target"], "wait lower bound")
                waits.append(event)
            if event["op"] == "ready":
                need(event["ready"] is True and event["generation"] == 0, "unread old readiness")
            if event["op"] != "read":
                continue
            g, nbytes, error = event["generation"], event["size"], event["errno"]
            need(integer(g) and integer(nbytes) and integer(error), "read types")
            data = bytes.fromhex(event["hex"])
            if error:
                need(not data and "count" not in event, "error has no count")
                error_reads.append((nbytes, error))
                if mode == "REARM" and len(error_reads) == 1:
                    need(b < arms[1]["first"] and g == 1, "rearm prefuture read")
                continue
            count = int.from_bytes(data, byteorder)
            need(nbytes == 8 and len(data) == 8 and integer(event["count"]) and
                 event["count"] == count and count >= 1, "native uint64 count")
            need(g in arms, "read armed generation")
            accumulated[g] += count
            arm = arms[g]
            if arm["period"]:
                # Two independent clock brackets enclose the kernel read instant.
                low = max(0, (a-arm["first"]) // arm["period"] + 1)
                high = max(0, (b-arm["first"]) // arm["period"] + 1)
                need(low <= accumulated[g] <= high, "cumulative expiration bracket")
            else:
                need(count == 1 and accumulated[g] == 1 and a >= arm["first"], "one-shot count")
            need(k+1 < len(ev) and ev[k+1]["op"] == "observe", "one callback per read")
            successful.append(event)
        expected_errors = {
            "DISARMED": [(8, errno.EAGAIN)],
            "SHORT_READ": [(7, errno.EINVAL), (8, errno.EAGAIN)],
            "REARM": [(8, errno.EAGAIN), (8, errno.EAGAIN)]}
        need(error_reads == expected_errors.get(mode, [] if mode.startswith("PERIODIC") else [(8, errno.EAGAIN)]), "error controls")
        if mode != "DISARMED":
            delay = 60_000_000 if mode.endswith("60MS") else 20_000_000
            need(waits[0]["target"] == arms[0]["first"] + delay, "initial delay schedule")
        if mode.startswith("PERIODIC"):
            need(waits[1]["target"] >= successful[0]["after"] + 20_000_000, "second silence")
            need(len(successful) == 2 and all(e["count"] > 1 for e in successful), "periodic overrun exposed")
        if mode == "REARM":
            need(waits[1]["target"] == arms[1]["first"] + 20_000_000, "rearm delay")
            need(len(successful) == 1 and successful[0]["generation"] == 1 and accumulated[0] == 0, "rearm attribution")
        n, r = sum(e["count"] for e in successful), len(callbacks)
        stats = row["accounting"]
        for key, expected_value in [("reported_expirations", n), ("callback_receipts", r),
                                    ("unobserved_from_reported", n-r), ("naive_observation_count", n)]:
            need(integer(stats[key]) and stats[key] == expected_value, "accounting " + key)
        need(stats["discarded_unread_history"] is (mode == "REARM"), "rearm history unknown")
        return errors, {"index": spec["index"], "mode": mode, "reported_expirations": n,
                        "callback_receipts": r, "unobserved_from_reported": n-r}
    except (KeyError, ValueError, TypeError, IndexError, OverflowError) as exc:
        return errors + ["malformed: " + type(exc).__name__ + ": " + str(exc)], None

def audit(root, out):
    errors = []
    freeze = loads((root/"FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if sha((root/name).read_bytes()) != expected:
            errors.append("source hash: " + name)
    plan = loads((root/"PLAN.json").read_text())
    env = loads((root/"ENVIRONMENT.json").read_text())
    expected_schedule = []
    for rep in range(3):
        for mode in MODES[rep:] + MODES[:rep]:
            expected_schedule.append({"index": len(expected_schedule), "rep": rep, "mode": mode})
    if plan["schedule"] != expected_schedule:
        errors.append("planned schedule")
    raw = (out/"RAW.jsonl").read_bytes()
    envelopes = [loads(line) for line in raw.splitlines()]
    inv, terminal, exit_rec = [loads((out/name).read_text()) for name in ("INVOCATION.json", "COMPLETE.json", "RUN_EXIT.json")]
    if len(envelopes) != 21: errors.append("case denominator")
    if terminal["raw_sha256"] != sha(raw): errors.append("raw hash")
    if terminal["status"] != "COMPLETE" or type(terminal["completed_envelopes"]) is not int or terminal["completed_envelopes"] != 21: errors.append("terminal")
    if type(exit_rec["returncode"]) is not int or exit_rec["returncode"] != 0: errors.append("supervisor exit")
    if inv["allocation"] != plan["allocation"] or inv["freeze_sha256"] != sha((root/"FREEZE.json").read_bytes()): errors.append("invocation binding")
    rows = []
    for i, (envelope, spec) in enumerate(zip(envelopes, expected_schedule)):
        problems, summary = check_case(envelope, spec, freeze["sha256"]["study.py"], env["byteorder"])
        errors.extend(str(i)+":"+problem for problem in problems)
        if summary: rows.append(summary)
    return {"decision": "PASS_TIMERFD_OBSERVATION_ACCOUNTING_SCOPED" if not errors else "FAIL_TIMERFD_ACCOUNTING_OR_EVIDENCE",
            "errors": errors, "cases": len(envelopes), "rows": rows,
            "naive_policy_periodic_failures": sum(r["mode"].startswith("PERIODIC") and r["reported_expirations"] > r["callback_receipts"] for r in rows),
            "new_gui_or_model_evidence": False}

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    try:
        report = audit(root, Path(sys.argv[1]).resolve())
    except Exception as exc:
        report = {"decision": "STOP_AUDIT_INPUT", "errors": [type(exc).__name__ + ": " + str(exc)]}
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if not report["errors"] else 1)
