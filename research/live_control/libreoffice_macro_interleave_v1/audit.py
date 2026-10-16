#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--evidence", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    evidence = Path(args.evidence)
    schedule = json.loads((root / "schedule.json").read_text(encoding="utf-8"))["cases"]
    rows = json.loads((evidence / "ledger.json").read_text(encoding="utf-8"))
    errors = []
    counts = {"window_stable": 0, "window_concurrent": 0}
    passes = {"window_stable": 0, "window_concurrent": 0}
    if len(rows) != len(schedule):
        errors.append(f"ledger_len={len(rows)} expected={len(schedule)}")
    for index, scenario in enumerate(schedule):
        if index >= len(rows):
            break
        row = rows[index]
        counts[scenario] += 1
        if row.get("index") != index or row.get("scenario") != scenario:
            errors.append(f"{index}:schedule_mismatch")
            continue
        if row.get("returncode") != 0:
            errors.append(f"{index}:returncode={row.get('returncode')}")
            continue
        r = row.get("result") or {}
        m = ((r.get("macro") or {}).get("macro") or {})
        if not (m.get("status") == "APPLIED" and m.get("before_x") == 1000 and m.get("after_x") == 1200):
            errors.append(f"{index}:macro_base={m}")
        if r.get("final_b_x") != 5000 or r.get("final_a_x") != 1200:
            errors.append(f"{index}:final={r.get('final_a_x')},{r.get('final_b_x')}")
        events = json.loads((evidence / row["case_id"] / "events.json").read_text(encoding="utf-8"))
        names = [event["event"] for event in events]
        expected_names = ["fixture_ready"] + (["writer_ready"] if scenario == "window_concurrent" else []) + ["validation_barrier_seen"] + (["writer_go", "writer_complete"] if scenario == "window_concurrent" else []) + ["macro_complete"]
        if names != expected_names:
            errors.append(f"{index}:events={names}")
        if scenario == "window_stable":
            if m.get("prewrite_x") != 1000:
                errors.append(f"{index}:stable_prewrite={m.get('prewrite_x')}")
        else:
            w = r.get("writer") or {}
            timing = (
                m.get("validation_ns") < w.get("set_call_start_ns") < w.get("set_call_end_ns") <
                m.get("prewrite_ns") < m.get("set_start_ns") <= m.get("set_end_ns") <
                (r.get("macro") or {}).get("invoke_end_ns")
            ) if all(v is not None for v in [
                m.get("validation_ns"), w.get("set_call_start_ns"), w.get("set_call_end_ns"),
                m.get("prewrite_ns"), m.get("set_start_ns"), m.get("set_end_ns"),
                (r.get("macro") or {}).get("invoke_end_ns")
            ]) else False
            if not (w.get("ok") is True and w.get("before_x") == 1000 and w.get("after_x") == 1700 and m.get("prewrite_x") == 1700 and timing):
                errors.append(f"{index}:concurrent w={w} m={m}")
        if r.get("case_gate_pass") is not True:
            errors.append(f"{index}:case_gate_false")
        else:
            passes[scenario] += 1
    if counts != {"window_stable": 5, "window_concurrent": 5}:
        errors.append(f"counts={counts}")
    if passes != {"window_stable": 5, "window_concurrent": 5}:
        errors.append(f"passes={passes}")
    outcome = "CONCURRENT_UNO_INTERLEAVES_MACRO_SCOPED" if not errors else "AUDIT_FAIL"
    source_files = [
        "conditional_window_macro.py", "writer_wait.py", "macro_invoker.py",
        "run_case.py", "run_block.py", "audit.py", "schedule.json", "prereg.json",
    ]
    report = {
        "audit_pass": not errors,
        "outcome": outcome,
        "counts": counts,
        "passes": passes,
        "errors": errors,
        "source_sha256": {name: sha(root / name) for name in source_files},
    }
    (evidence / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())
