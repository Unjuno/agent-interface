"""Run met and unmet local visual barriers against fresh X11 Inkscape sessions."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

from executor_v3 import Executor
from session_v23 import Backend, suite


HERE = Path(__file__).resolve().parent
SOURCES = [
    "probe_local_visual_barrier_x11_v1.py", "session_v23.py",
    "local_visual_barrier_program_v1.py", "local_visual_barrier_v1.py",
    "session_v22.py", "session_v21.py", "session_v20.py", "session_v19.py",
    "session_v18.py", "session_v17.py", "session_v16.py", "session_v15.py",
    "session_v14.py", "session_v13.py", "session_v12.py", "session_v11.py",
    "session_v10.py", "session_v9.py", "executor_v3.py", "lease.py",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def barrier(identifier, sequence, box, minimum):
    return {
        "op": "local_visual_barrier", "barrier_id": identifier,
        "source_sequence": sequence, "box": box,
        "metric": "persistent_rgb_change", "rgb_threshold": 20,
        "minimum_changed_pixels": minimum, "required_samples": 2,
        "sample_interval_ms": 50, "timeout_ms": 500,
        "on_unmet": "needs_decision",
    }


def run_case(case, out):
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
        sequence = backend.sequence
        if case == "met":
            box = [max(0, before[0] - 16), max(0, before[1] - 16),
                   min(backend.decoder.frame.width, before[2] + 48),
                   min(backend.decoder.frame.height, before[3] + 16)]
            first = {"op": "pointer_drag", "points": [
                {"x": x, "y": y}, {"x": x + 12, "y": y}, {"x": x + 24, "y": y}],
                "duration_ms": 200}
            minimum = 100
        else:
            box = [800, 500, 900, 600]
            first = {"op": "pointer_click", "x": x, "y": y, "duration_ms": 40}
            minimum = 9000
        steps = [first, barrier(case, sequence, box, minimum),
                 {"op": "chord", "modifier": "Control_L", "key": "s"}]
        engine.submit(case, steps, sequence, time.perf_counter_ns() + 5_000_000_000)
        engine.active[2].join()
        terminal = next(record for record in events if record.get("event") == "terminal")
        outcome = next(record for record in events if record.get("event") == "local_visual_barrier")
        started = [record["step"] for record in events if record.get("event") == "step_started"]
        after = suite.red_bbox(backend.decoder.frame)
        row = {
            "case": case, "before_bbox": before, "after_bbox": after,
            "terminal": terminal, "barrier": outcome, "steps_started": started,
            "later_save_step_started": 2 in started,
        }
        (out / "result.json").write_text(json.dumps(row, indent=2) + "\n")
        if case == "met":
            assert terminal["status"] == "completed" and terminal["steps_completed"] == 3
            assert outcome["reason"] == "met" and row["later_save_step_started"] is True
            assert after[0] - before[0] in (23, 24, 25)
        else:
            assert terminal["status"] == "needs_decision" and terminal["steps_completed"] == 1
            assert outcome["reason"] == "unmet" and row["later_save_step_started"] is False
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
        "status": "scripted_x11_integration_probe",
        "order": ["met", "unmet"],
        "seed": 991003,
        "sources": {name: sha(HERE / name) for name in SOURCES},
        "scope": "fresh scripted Inkscape X11 sessions; executor continuation boundary only; no model, semantic correctness, speed, token or generalization claim",
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    rows = []
    failures = []
    for case in manifest["order"]:
        try:
            rows.append(run_case(case, args.out / case))
        except AssertionError as exc:
            result = json.loads((args.out / case / "result.json").read_text())
            rows.append(result)
            failures.append({"case": case, "error": "asserted task-relative effect did not hold",
                             "detail": repr(exc)})
    report = {
        "passed": not failures, "cases": rows, "failures": failures,
        "decision": ("HOLD_FOR_AGENT_AUTHORED_CONTEXT_PROBE;_NO_BENCHMARK_PROMOTION"
                     if not failures else
                     "REJECT_SINGLE_ROI_CHANGE_AS_CONTINUATION_BARRIER;_KEEP_ADVISORY_ONLY"),
        "scope": manifest["scope"],
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
