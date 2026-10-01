#!/usr/bin/env python3
"""Excluded synthetic-clock construction and raw-only mutation controls."""
import copy
import errno
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import audit
import study

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "PLAN.json").read_text())
SOURCE = hashlib.sha256((ROOT / "study.py").read_bytes()).hexdigest()

class FakeTimer:
    """Explicit deterministic construction oracle; no OS timer is armed."""
    def __init__(self):
        self.now = 1_000_000_000
        self.first = self.period = self.taken = 0
    def clock(self):
        self.now += 1000
        return self.now
    def sleep(self, seconds):
        self.now += round(seconds * 1_000_000_000)
    def settime(self, fd, **kw):
        self.first, self.period, self.taken = kw["initial"], kw["interval"], 0
        return (0, 0)
    def read(self, fd, size):
        if size < 8:
            raise OSError(errno.EINVAL, "synthetic short read")
        total = 0 if self.first == 0 or self.now < self.first else (1 if self.period == 0 else 1+(self.now-self.first)//self.period)
        count = total-self.taken
        if count <= 0:
            raise BlockingIOError(errno.EAGAIN, "synthetic empty")
        self.taken = total
        return count.to_bytes(8, sys.byteorder)
    def fstat(self, fd):
        raise OSError(errno.EBADF, "synthetic closed")

def envelope(row):
    text = study.encoded(row)
    return {"index": row["index"], "command": ["synthetic-excluded"], "returncode": 0,
            "stdout": text, "stderr": "", "stdout_sha256": audit.sha(text.encode())}

def synthetic(spec):
    fake = FakeTimer()
    with patch.object(study.time, "monotonic_ns", fake.clock), \
         patch.object(study.time, "sleep", fake.sleep), \
         patch.object(study.os, "timerfd_create", return_value=17), \
         patch.object(study.os, "timerfd_gettime_ns", return_value=(0, 0)), \
         patch.object(study.os, "get_inheritable", return_value=False), \
         patch.object(study.os, "timerfd_settime_ns", fake.settime), \
         patch.object(study.os, "read", fake.read), \
         patch.object(study.os, "close", return_value=None), \
         patch.object(study.os, "fstat", fake.fstat), \
         patch.object(study.select, "select", return_value=([17], [], [])):
        return envelope(study.worker(spec))

def mutations(base, spec, source=SOURCE, order=sys.byteorder):
    controls = {}
    def check(name, edit):
        changed = copy.deepcopy(base)
        row = json.loads(changed["stdout"])
        edit(changed, row)
        changed["stdout"] = study.encoded(row)
        changed["stdout_sha256"] = audit.sha(changed["stdout"].encode())
        errors, _ = audit.check_case(changed, spec, source, order)
        controls[name] = {"rejected": bool(errors), "errors": errors}
    def firstread(row):
        return next(e for e in row["events"] if e["op"] == "read")
    def callback(row):
        return next(e for e in row["events"] if e["op"] == "observe")
    check("declared_count", lambda e, r: firstread(r).__setitem__("count", firstread(r)["count"]+1))
    check("raw_count", lambda e, r: firstread(r).__setitem__("hex", (1).to_bytes(8, order).hex()))
    check("boolean_count", lambda e, r: firstread(r).__setitem__("count", True))
    check("wrong_generation", lambda e, r: firstread(r).__setitem__("generation", 5))
    check("future_deadline", lambda e, r: next(x for x in r["events"] if x["op"] == "arm").__setitem__("first", 10**18))
    check("reversed_clock", lambda e, r: firstread(r).__setitem__("after", firstread(r)["before"]-1))
    check("missing_callback", lambda e, r: r["events"].remove(callback(r)))
    check("authority", lambda e, r: callback(r).__setitem__("authority", "input"))
    check("source_hash", lambda e, r: r.__setitem__("source_sha256", "0"*64))
    check("lost_exit", lambda e, r: e.__setitem__("returncode", None))
    check("bad_close", lambda e, r: r["events"][-1].__setitem__("errno", 0))
    check("false_accounting", lambda e, r: r["accounting"].__setitem__("callback_receipts", r["accounting"]["reported_expirations"]))
    return controls

class Tests(unittest.TestCase):
    def test_all_synthetic_modes(self):
        for spec in PLAN["schedule"]:
            with self.subTest(spec=spec):
                errors, _ = audit.check_case(synthetic(spec), spec, SOURCE, sys.byteorder)
                self.assertEqual(errors, [])
    def test_twelve_mutations(self):
        controls = mutations(synthetic(PLAN["schedule"][0]), PLAN["schedule"][0])
        self.assertEqual(len(controls), 12)
        self.assertTrue(all(v["rejected"] for v in controls.values()), controls)
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError): audit.loads('{"a":1,"a":2}')
    def test_exact_uint64(self):
        for n in (1, 31, 2**63+9, 2**64-1):
            self.assertEqual(int.from_bytes(n.to_bytes(8, sys.byteorder), sys.byteorder), n)
    def test_schedule(self):
        self.assertEqual(len(PLAN["schedule"]), 21)
        self.assertEqual([x["index"] for x in PLAN["schedule"]], list(range(21)))
        for mode in audit.MODES:
            self.assertEqual(sum(s["mode"] == mode for s in PLAN["schedule"]), 3)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--formal":
        out = Path(sys.argv[2])
        baseline = audit.audit(ROOT, out)
        if baseline["errors"]:
            print(json.dumps({"STOP": "BASELINE_AUDIT_FAILED", "errors": baseline["errors"]}, indent=2))
            raise SystemExit(2)
        base = audit.loads((out / "RAW.jsonl").read_text().splitlines()[0])
        controls = mutations(base, PLAN["schedule"][0])
        print(json.dumps({"controls": controls, "rejected": sum(x["rejected"] for x in controls.values()),
                          "total": len(controls), "formal_reruns": 0}, indent=2, sort_keys=True))
        raise SystemExit(0 if all(x["rejected"] for x in controls.values()) else 1)
    unittest.main()
