"""Effective raw-evidence corruption controls for the #5260 auditor."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
INPUT = "hxy"
SCHEDULE = [("child", "idle"), ("managed", "busy"),
            ("managed", "idle"), ("child", "busy")] * 8


def synthetic_raw():
    rows = []
    for i, (target, load) in enumerate(SCHEDULE):
        pid = 10000 + i
        t = 1_000_000_000 + i * 10_000_000
        events = [{"kind": "FocusIn", "widget": "target", "monotonic_ns": t + 1}]
        keys = []
        for j, char in enumerate(INPUT):
            kt = t + 2 + j * 20_000_000
            keys.append({"index": j, "char": char, "keycode": 38 + j,
                         "request_started_ns": kt, "sync_returned_ns": kt + 1})
            events.append({"kind": "KeyPress", "widget": "target", "monotonic_ns": kt,
                           "char": char, "keysym": char, "keycode": 38 + j})
        app = {"pid": pid, "target_kind": target, "input": INPUT, "events": events,
               "click": {"target_id": 500 if target == "child" else 400,
                         "child_id": 500, "managed_id": 400,
                         "request_started_ns": t, "sync_returned_ns": t + 1},
               "key_requests": keys, "final_value": INPUT, "ended_ns": t + 70_000_000}
        rows.append({"index": i, "round": i // 4, "target": target, "load": load,
                     "app_pid": pid, "app_exit": 0, "app_stdout_sha256": "0" * 64,
                     "app_stderr": "", "app_parse_error": None, "app": app,
                     "case_started_ns": t, "case_ended_ns": t + 80_000_000,
                     "load_pid": 20000 + i if load == "busy" else None,
                     "load_exit": 0 if load == "busy" else None, "load_stderr": ""})
    return {"schema": "tk-first-char-focus-order-raw-v1", "allocation": FREEZE["allocation"],
            "base_main": FREEZE["base_main"],
            "environment": {"python": "3.12.3", "tk": "8.6", "display": FREEZE["display"], "xkb_layout": "us"},
            "source_sha256": FREEZE["source_sha256"], "schedule": [list(x) for x in SCHEDULE],
            "requested_input": INPUT, "click_to_first_key_ms": 50, "inter_key_gap_ms": 20,
            "rows": rows, "runner_pid": 9000, "started_ns": 1_000_000_000,
            "ended_ns": 1_390_000_000}


def audit(raw, root, label):
    inp, out = root / f"{label}.json", root / f"{label}.audit.json"
    inp.write_text(json.dumps(raw), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(HERE / "study.py"), "--audit", str(inp), str(out)],
                          capture_output=True, text=True, check=False)
    report = json.loads(out.read_text(encoding="utf-8"))
    return proc.returncode, report


def main():
    base = synthetic_raw()
    with tempfile.TemporaryDirectory(prefix="focus5260-audit-") as temp:
        root = Path(temp)
        code, report = audit(base, root, "baseline")
        assert code == 0 and report["checks"] == "PASS" and report["decision"] == "NO_LOSS_IN_32_ROWS", report
        controls = {}
        variants = {}
        value = copy.deepcopy(base); value["rows"].pop(); variants["missing_row"] = value
        value = copy.deepcopy(base); value["requested_input"] = "hxyz"; variants["altered_input"] = value
        value = copy.deepcopy(base); value["rows"][0]["app"]["key_requests"][0]["request_started_ns"] = -10; variants["negative_timestamp"] = value
        value = copy.deepcopy(base); value["source_sha256"]["study.py"] = "f" * 64; variants["altered_source_hash"] = value
        for label, raw in variants.items():
            code, report = audit(raw, root, label)
            controls[label] = {"rejected": code != 0 and report["checks"] == "FAIL", "errors": report["errors"]}
        assert all(v["rejected"] for v in controls.values()), controls
        summary = {"synthetic_baseline": report["schema"], "corruption_controls": controls,
                   "control_count": len(controls), "rejected_count": sum(v["rejected"] for v in controls.values())}
        print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
