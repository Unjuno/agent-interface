"""Fresh X11 met/partial pair for a displacement-gated later Save step."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

from executor_v3 import Executor
from session_v24 import Backend, suite


HERE = Path(__file__).resolve().parent
SOURCES = [
    "probe_local_displacement_x11_v1.py", "session_v24.py",
    "local_displacement_postcondition_v1.py", "visual_anchor.py", "session_v23.py",
    "local_visual_barrier_program_v1.py", "local_visual_barrier_v1.py",
    "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
    "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
    "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
    "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def condition(sequence, box):
    return {
        "op": "local_displacement_postcondition", "postcondition_id": "red-rectangle-24px",
        "source_sequence": sequence, "box": box, "target_delta": [24, 0],
        "tolerance_px": 1, "required_samples": 2, "sample_interval_ms": 50,
        "timeout_ms": 500, "on_unmet": "needs_decision",
    }


def run_case(case, pointer_delta, out):
    out.mkdir()
    events = []
    session = suite.Session()
    backend = None
    engine = None
    output = None

    def emit(record):
        events.append(record)
        with (out / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")

    try:
        goal, output, _ = suite.prepare(session, "inkscape", 991003, "unused")
        backend = Backend(session, out, emit)
        engine = Executor(backend, emit)
        backend.snapshot("initial", 0)
        before = suite.red_bbox(backend.decoder.frame)
        x = (before[0] + before[2]) // 2
        y = (before[1] + before[3]) // 2
        box = [before[0] - 4, before[1] - 4,
               before[2] - before[0] + 9, before[3] - before[1] + 9]
        sequence = backend.sequence
        points = [{"x": x + offset, "y": y}
                  for offset in range(0, pointer_delta + 1, 2)]
        steps = [
            {"op": "pointer_drag", "points": points, "duration_ms": 240},
            {"op": "key", "key": "Escape"},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
            condition(sequence, box),
            {"op": "chord", "modifier": "Control_L", "key": "s"},
        ]
        engine.submit(case, steps, sequence, time.perf_counter_ns() + 6_000_000_000)
        engine.active[2].join()
        terminal = next(record for record in events if record.get("event") == "terminal")
        outcome = next(record for record in events
                       if record.get("event") == "local_displacement_postcondition")
        started = [record["step"] for record in events if record.get("event") == "step_started"]
        after = suite.red_bbox(backend.decoder.frame)
        row = {
            "case": case, "pointer_delta": pointer_delta,
            "before_bbox": before, "after_bbox": after,
            "observed_delta": [after[0] - before[0], after[1] - before[1]],
            "terminal": terminal, "postcondition": outcome, "steps_started": started,
            "later_save_step_started": 4 in started,
        }
        (out / "result.json").write_text(json.dumps(row, indent=2) + "\n")
        return row
    finally:
        if engine:
            engine.close()
        if backend:
            backend.close()
            (out / "owner-events.json").write_text(json.dumps(backend.owner.records, indent=2) + "\n")
        if output and output.exists():
            shutil.copy2(output, out / "shape.svg")
        session.close()
        (out / "cleanup.json").write_text(json.dumps({
            "all_owned_processes_exited": all(process.poll() is not None for process in session.procs),
        }) + "\n")
        shutil.rmtree(session.tmp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "scripted_x11_displacement_continuation_probe",
        "order": ["target", "partial"], "seed": 991003,
        "allocations": {"target": {"pointer_delta": 28, "visual_target": [24, 0]},
                        "partial": {"pointer_delta": 24, "visual_target": [24, 0]}},
        "sources": {name: sha(HERE / name) for name in SOURCES},
        "failure_policy": "retain first result; no replacement within an allocation",
        "scope": "fresh scripted Inkscape X11 sessions; no model, cross-domain, speed, token or generalization claim",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    rows = [run_case(name, values["pointer_delta"], args.out / name)
            for name, values in manifest["allocations"].items()]
    target, partial = rows
    passed = (
        target["postcondition"]["reason"] == "met" and target["later_save_step_started"] and
        abs(target["observed_delta"][0] - 24) <= 1 and
        partial["postcondition"]["reason"] != "met" and not partial["later_save_step_started"] and
        abs(partial["observed_delta"][0] - 24) > 1 and
        all(row["terminal"]["release"]["verified"] for row in rows)
    )
    report = {
        "passed": passed, "cases": rows,
        "decision": ("ADVANCE_TO_AGENT_AUTHORED_FIXED_CONTEXT_PROBE;_NO_BENCHMARK_PROMOTION"
                     if passed else "HOLD_DISPLACEMENT_POSTCONDITION;_PRESERVE_FAILURE"),
        "scope": manifest["scope"],
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
