"""Engineering-only X11 probe of A/B navigation through the checked socket path."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-runtime-probe-02"
SEED = 991026


def first(records, event):
    return next(row for row in records if row.get("event") == event)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    runtime = OUT / "runtime"
    errors = (OUT / "stderr.txt").open("w", encoding="utf-8", newline="\n")
    process = subprocess.Popen([
        sys.executable, "-u", str(HERE / "integrated_efficiency_socket_v1.py"),
        "integrated-efficiency-chromium-v1", "serve", "--", "--app", "chromium",
        "--seed", str(SEED), "--out", str(runtime),
    ], stdout=subprocess.PIPE, stderr=errors, text=True)
    temporary = tempfile.TemporaryDirectory(prefix="integrated-runtime-probe-")
    journal = Path(temporary.name) / "journal.jsonl"
    results = []
    try:
        endpoint = json.loads(process.stdout.readline())
        initial = request_once(endpoint["socket"], start(endpoint["socket"]),
                               {"events": ["observation"], "timeout": 30})
        ready = first(initial["reply"]["records"], "ready")
        initialize(journal, initial["continuation"])

        def call(spec):
            result = run(journal, spec)
            assert result["state"]["pending"] is None
            return result

        def clock():
            result = call({"command": {"op": "clock"}, "timeout": 3})
            return result["state"]["last_resolution"]["clock"]

        def submit(steps):
            current = clock()
            return call({"command": {"op": "submit",
                "expected_sequence": current["sequence"],
                "valid_until_ns": current["runtime_ns"] + 10_000_000_000,
                "steps": steps}, "timeout": 10})

        for task_index in (0, 3):
            task = ready["goal"]["tasks"][task_index]
            navigation = submit([
                {"op": "chord", "modifier": "Control_L", "key": "l"},
                {"op": "text", "text": task["url"]},
                {"op": "key", "key": "Return"},
                {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
            ])
            assert first(navigation["reply"]["records"], "terminal")["status"] == "completed"
            observed = submit([{"op": "observe"}])
            observation = first(observed["reply"]["records"], "observation")
            image = runtime / Path(observation["image"]).name
            results.append({"task_id": task["task_id"], "layout": task["layout"],
                            "sequence": observation["sequence"], "exact": observation["exact"],
                            "image": image.name,
                            "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest()})

        state = load(journal)["continuation"]
        finished = request_once(endpoint["socket"], state, {
            "events": ["independent_evaluation"], "timeout": 10,
            "command": {"op": "finish"}, "request_id": "finish-runtime-probe"})
        evaluation = first(finished["reply"]["records"], "independent_evaluation")
        assert evaluation["success"] is False and evaluation["record_count"] == 0
        assert len(evaluation["missing"]) == 6
        assert all(row["exact"] for row in results)
        assert results[0]["image_sha256"] != results[1]["image_sha256"]
        shutil.copy2(journal, OUT / "journal.jsonl")
        report = {"schema": "integrated_efficiency_runtime_probe_v1",
                  "passed": True, "seed": SEED, "observations": results,
                  "independent_evaluation": evaluation, "model_calls": 0,
                  "task_inputs": 0}
        (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
        print(json.dumps(report, indent=2))
    finally:
        temporary.cleanup()
        errors.close()
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
