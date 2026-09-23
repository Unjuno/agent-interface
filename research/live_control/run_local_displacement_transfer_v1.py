"""Run a frozen model-authored displacement condition in fresh X11 sessions."""
import hashlib
import json
import shutil
import time
from pathlib import Path

from executor_v3 import Executor
from session_v24 import Backend, suite


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/local-displacement-transfer-01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name, allocation, spec, out):
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
        pointer_delta = allocation["pointer_delta"]
        points = [{"x": x + offset, "y": y} for offset in range(0, pointer_delta + 1, 2)]
        steps = [
            {"op": "pointer_drag", "points": points, "duration_ms": 240},
            {"op": "key", "key": "Escape"},
            {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
            spec,
            {"op": "chord", "modifier": "Control_L", "key": "s"},
        ]
        engine.submit(name, steps, backend.sequence, time.perf_counter_ns() + 6_000_000_000)
        engine.active[2].join()
        terminal = next(row for row in events if row.get("event") == "terminal")
        condition = next(row for row in events if row.get("event") == "local_displacement_postcondition")
        started = [row["step"] for row in events if row.get("event") == "step_started"]
        after = suite.red_bbox(backend.decoder.frame)
        result = {
            "name": name, "before_bbox": before, "after_bbox": after,
            "observed_visual_delta": [after[0] - before[0], after[1] - before[1]],
            "postcondition": condition, "terminal": terminal, "steps_started": started,
            "save_started": 4 in started,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
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
    plan = json.loads((OUT / "preregistration.json").read_text())
    assert plan["status"] == "preregistered_before_fresh_x11_execution"
    for name, expected in plan["sources"].items():
        assert sha(HERE / name) == expected, name
    authored_source = Path(plan["authored_source"])
    assert sha(authored_source) == plan["authored_source_sha256"]
    assert sha(OUT / "authored-postcondition.json") == plan["authored_output_sha256"]
    spec = json.loads((OUT / "authored-postcondition.json").read_text())
    assert spec == plan["authored_output"]
    rows = []
    for name in plan["order"]:
        result = run_case(name, plan["allocations"][name], spec, OUT / name)
        rows.append(result)
        (OUT / "execution.json").write_text(json.dumps(rows, indent=2) + "\n")
    passed = all(
        row["observed_visual_delta"] == plan["allocations"][row["name"]]["expected_visual_delta"] and
        row["postcondition"]["reason"] == plan["allocations"][row["name"]]["expected_postcondition"] and
        row["save_started"] is plan["allocations"][row["name"]]["save"] and
        row["terminal"]["release"]["verified"] is True
        for row in rows
    )
    report = {
        "passed": passed, "cases": rows,
        "decision": ("RETAIN_MODEL_AUTHORED_FRESH_TRANSFER;_REPLICATE_BEFORE_PROMOTION"
                     if passed else "HOLD_MODEL_AUTHORED_TRANSFER;_PRESERVE_FAILURE"),
        "scope": plan["interpretation"],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
