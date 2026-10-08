"""One-shot private-Xvfb Tk focus-order diagnostic for Issue #5260."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
INPUT = "hxy"
TARGETS = ("child", "managed")
LOADS = ("idle", "busy")
ROUNDS = 8
SCHEDULE = [("child", "idle"), ("managed", "busy"),
            ("managed", "idle"), ("child", "busy")] * ROUNDS


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def busy_worker() -> int:
    value = 0
    while True:
        value = (value * 1664525 + 1013904223) & 0xFFFFFFFF


def app_worker(target_kind: str) -> int:
    import tkinter as tk
    from Xlib import X, display
    from Xlib.ext import xtest

    root = tk.Tk()
    root.title("5260-private-entry")
    root.geometry("420x180+80+70")
    root.attributes("-topmost", True)
    target = tk.Entry(root, width=32)
    decoy = tk.Entry(root, width=12)
    decoy.pack(padx=12, pady=8, anchor="w")
    target.pack(padx=12, pady=8, anchor="w")
    record = {"pid": os.getpid(), "target_kind": target_kind,
              "input": INPUT, "events": [], "click": {}, "key_requests": []}
    done = False

    def event(name: str, widget: tk.Widget, ev: object | None = None) -> None:
        row = {"kind": name, "widget": "target" if widget is target else "decoy",
               "monotonic_ns": time.monotonic_ns()}
        if ev is not None:
            row.update(keycode=getattr(ev, "keycode", None),
                       keysym=getattr(ev, "keysym", None),
                       char=getattr(ev, "char", None))
        record["events"].append(row)

    target.bind("<FocusIn>", lambda e: event("FocusIn", target))
    target.bind("<FocusOut>", lambda e: event("FocusOut", target))
    target.bind("<KeyPress>", lambda e: event("KeyPress", target, e), add="+")
    target.bind("<Button-1>", lambda e: root.after_idle(lambda: target.focus_force()))
    decoy.bind("<FocusIn>", lambda e: event("FocusIn", decoy))
    decoy.bind("<FocusOut>", lambda e: event("FocusOut", decoy))

    xd = display.Display()
    root.update_idletasks()

    def click_and_type() -> None:
        nonlocal done
        if done:
            return
        root_id = root.winfo_id()
        child_id = target.winfo_id()
        if target_kind == "child":
            target_id = child_id
            cx = target.winfo_rootx() + target.winfo_width() // 2
            cy = target.winfo_rooty() + target.winfo_height() // 2
        else:
            target_id = root_id
            cx = root.winfo_rootx() + target.winfo_x() + target.winfo_width() // 2
            cy = root.winfo_rooty() + target.winfo_y() + target.winfo_height() // 2
        before = time.monotonic_ns()
        xtest.fake_input(xd, X.ButtonPress, detail=1, x=cx, y=cy)
        xtest.fake_input(xd, X.ButtonRelease, detail=1, x=cx, y=cy)
        xd.sync()
        after = time.monotonic_ns()
        record["click"] = {"target_id": target_id, "child_id": child_id,
            "managed_id": root_id, "x": cx, "y": cy,
            "request_started_ns": before, "sync_returned_ns": after}
        root.after(50, type_character, 0)

    def type_character(index: int) -> None:
        if index >= len(INPUT):
            root.after(250, finish)
            return
        char = INPUT[index]
        keysym = xd.keysym_to_keycode(ord(char))
        start = time.monotonic_ns()
        xtest.fake_input(xd, X.KeyPress, detail=keysym)
        xtest.fake_input(xd, X.KeyRelease, detail=keysym)
        xd.sync()
        returned = time.monotonic_ns()
        record["key_requests"].append({"index": index, "char": char,
            "keycode": keysym, "request_started_ns": start,
            "sync_returned_ns": returned})
        root.after(20, type_character, index + 1)

    def finish() -> None:
        nonlocal done
        if done:
            return
        done = True
        record["final_value"] = target.get()
        try:
            focus = xd.get_input_focus().focus
            record["final_x_focus_id"] = getattr(focus, "id", None)
        except Exception as exc:  # retain diagnostic, do not convert to pass
            record["final_focus_error"] = type(exc).__name__
        record["ended_ns"] = time.monotonic_ns()
        print(json.dumps(record, sort_keys=True), flush=True)
        root.destroy()
        xd.close()

    root.after(250, lambda: decoy.focus_force())
    root.after(400, click_and_type)
    root.mainloop()
    return 0


def audit(raw_path: Path, report_path: Path) -> int:
    """Independent structural and decision audit; never repairs raw evidence."""
    from collections import Counter

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    expected = [list(x) for x in SCHEDULE]
    if raw.get("schema") != "tk-first-char-focus-order-raw-v1":
        errors.append("schema")
    if raw.get("allocation") != FREEZE["allocation"] or raw.get("base_main") != FREEZE["base_main"]:
        errors.append("allocation_or_base")
    if raw.get("source_sha256") != FREEZE["source_sha256"]:
        errors.append("source_hashes")
    if raw.get("schedule") != expected:
        errors.append("schedule")
    if raw.get("requested_input") != INPUT or raw.get("click_to_first_key_ms") != 50 or raw.get("inter_key_gap_ms") != 20:
        errors.append("fixed_protocol")
    env = raw.get("environment")
    if not isinstance(env, dict) or env.get("display") != FREEZE["display"] or env.get("xkb_layout") != "us" or env.get("tk") != "8.6":
        errors.append("environment")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(SCHEDULE):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []

    pids: set[int] = set()
    counts: Counter[tuple[str, str]] = Counter()
    missing = []
    focus_order = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"row_{i}_type")
            continue
        if i >= len(SCHEDULE) or (row.get("index"), row.get("target"), row.get("load"), row.get("round")) != (i, *SCHEDULE[i], i // 4):
            errors.append(f"row_{i}_identity")
        counts[(row.get("target"), row.get("load"))] += 1
        pid = row.get("app_pid")
        if type(pid) is not int or pid in pids:
            errors.append(f"row_{i}_pid")
        else:
            pids.add(pid)
        if row.get("app_exit") != 0 or row.get("app_parse_error") is not None or not isinstance(row.get("app"), dict):
            errors.append(f"row_{i}_process")
            continue
        app = row["app"]
        if app.get("pid") != pid or app.get("target_kind") != row.get("target") or app.get("input") != INPUT:
            errors.append(f"row_{i}_app_identity")
        click, keys, events = app.get("click"), app.get("key_requests"), app.get("events")
        if not isinstance(click, dict) or not isinstance(keys, list) or len(keys) != 3 or not isinstance(events, list):
            errors.append(f"row_{i}_event_schema")
            continue
        if type(click.get("request_started_ns")) is not int or type(click.get("sync_returned_ns")) is not int or click["sync_returned_ns"] < click["request_started_ns"]:
            errors.append(f"row_{i}_click_timing")
        want_id = click.get("child_id") if row.get("target") == "child" else click.get("managed_id")
        if click.get("target_id") != want_id or type(want_id) is not int:
            errors.append(f"row_{i}_target_id")
        previous = -1
        for j, key in enumerate(keys):
            if not isinstance(key, dict) or key.get("index") != j or key.get("char") != INPUT[j]:
                errors.append(f"row_{i}_key_{j}_identity")
                continue
            start, end = key.get("request_started_ns"), key.get("sync_returned_ns")
            if type(start) is not int or type(end) is not int or start < previous or end < start:
                errors.append(f"row_{i}_key_{j}_timing")
            previous = end if type(end) is int else previous
        key_events = [e for e in events if isinstance(e, dict) and e.get("kind") == "KeyPress" and e.get("widget") == "target"]
        focus_events = [e for e in events if isinstance(e, dict) and e.get("kind") == "FocusIn" and e.get("widget") == "target"]
        first_key_ns = key_events[0].get("monotonic_ns") if key_events else None
        first_focus_ns = focus_events[0].get("monotonic_ns") if focus_events else None
        focus_order.append("focus_before" if type(first_focus_ns) is int and type(first_key_ns) is int and first_focus_ns <= first_key_ns else "key_before_or_no_focus")
        value = app.get("final_value")
        if not isinstance(value, str):
            errors.append(f"row_{i}_value_type")
        elif value != INPUT:
            missing.append({"index": i, "target": row.get("target"), "load": row.get("load"), "final_value": value,
                "key_chars": [e.get("char") for e in key_events]})
        if row.get("load") == "busy":
            if type(row.get("load_pid")) is not int or row.get("load_exit") != 0:
                errors.append(f"row_{i}_load_process")
        elif row.get("load_pid") is not None or row.get("load_exit") is not None:
            errors.append(f"row_{i}_unexpected_load")
    if set(counts.values()) != {8} or len(counts) != 4:
        errors.append("cell_cardinality")
    disposition = "STOP_PROVENANCE_OR_RUNNER" if errors else (
        "FAIL_INITIAL_CHAR_LOSS_REPRODUCED" if missing else "NO_LOSS_IN_32_ROWS")
    report = {"schema": "tk-first-char-focus-order-audit-v1", "allocation": FREEZE["allocation"],
        "raw_sha256": sha(raw_path.read_bytes()), "checks": "PASS" if not errors else "FAIL",
        "errors": errors, "decision": disposition, "rows": len(rows),
        "missing_or_mismatched_input_rows": missing,
        "focus_order_counts": dict(Counter(focus_order)),
        "scope": "local synthetic Tk/Xvfb diagnostic only; not Docker, not a causal or product-wide claim"}
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 2


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    if os.environ.get("DISPLAY") != FREEZE["display"]:
        raise RuntimeError("unexpected DISPLAY; only the frozen private Xvfb is permitted")
    actual = {name: sha((HERE / name).read_bytes()) for name in FREEZE["source_files"]}
    if actual != FREEZE["source_sha256"]:
        raise RuntimeError("source hash mismatch before run")

    rows = []
    for index, (target, load) in enumerate(SCHEDULE):
        load_proc = None
        if load == "busy":
            load_proc = subprocess.Popen([sys.executable, str(HERE / "study.py"),
                "--busy-worker"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            time.sleep(0.1)
        command = [sys.executable, str(HERE / "study.py"), "--app-worker", target]
        start = time.monotonic_ns()
        proc = subprocess.run(command, capture_output=True, text=True, timeout=8)
        end = time.monotonic_ns()
        if load_proc is not None:
            load_proc.terminate()
            try:
                load_stderr = load_proc.communicate(timeout=2)[1].decode("utf-8", "replace")
                load_exit = load_proc.returncode
            except subprocess.TimeoutExpired:
                load_proc.kill()
                load_stderr = load_proc.communicate()[1].decode("utf-8", "replace")
                load_exit = load_proc.returncode
        else:
            load_stderr, load_exit = "", None
        try:
            app = json.loads(proc.stdout.strip().splitlines()[-1])
            parse_error = None
        except Exception as exc:
            app, parse_error = None, f"{type(exc).__name__}: {exc}"
        rows.append({"index": index, "round": index // 4,
            "target": target, "load": load, "app_pid": app.get("pid") if app else None,
            "app_exit": proc.returncode, "app_stdout_sha256": sha(proc.stdout.encode()),
            "app_stderr": proc.stderr, "app_parse_error": parse_error, "app": app,
            "case_started_ns": start, "case_ended_ns": end,
            "load_pid": load_proc.pid if load_proc else None,
            "load_exit": load_exit, "load_stderr": load_stderr})
        if proc.returncode != 0 or app is None:
            break

    raw = {"schema": "tk-first-char-focus-order-raw-v1",
        "allocation": FREEZE["allocation"], "base_main": FREEZE["base_main"],
        "environment": {"python": sys.version, "tk": "8.6",
            "display": os.environ.get("DISPLAY"), "xkb_layout": FREEZE["xkb_layout"]},
        "source_sha256": actual, "schedule": [list(x) for x in SCHEDULE],
        "requested_input": INPUT, "click_to_first_key_ms": 50,
        "inter_key_gap_ms": 20, "rows": rows,
        "runner_pid": os.getpid(), "started_ns": min((r["case_started_ns"] for r in rows), default=None),
        "ended_ns": max((r["case_ended_ns"] for r in rows), default=None)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "expected": len(SCHEDULE),
        "raw_sha256": sha(output.read_bytes()), "output": str(output)}, sort_keys=True))
    return raw


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--app-worker":
        raise SystemExit(app_worker(sys.argv[2]))
    if len(sys.argv) == 2 and sys.argv[1] == "--busy-worker":
        raise SystemExit(busy_worker())
    if len(sys.argv) == 4 and sys.argv[1] == "--audit":
        raise SystemExit(audit(Path(sys.argv[2]), Path(sys.argv[3])))
    if len(sys.argv) != 2:
        raise SystemExit("usage: study.py RAW_OUTPUT.json")
    run(Path(sys.argv[1]))
