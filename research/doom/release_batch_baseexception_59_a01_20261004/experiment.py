"""Compare frozen and patched ExecutorV13 behavior for BaseException custody."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
LIVE = HERE.parents[1] / "live_control"
BASELINE = HERE / "baseline_executor_v13.py"
CANDIDATE = LIVE / "executor_v13.py"
PAYLOAD = {
    "status": "delivery_unknown", "identifier": "base-sink-failure",
    "step": 0, "size": 2, "position": 1,
    "confirmed_positions": [0], "not_attempted_positions": [],
    "event": "input_release_transition", "key": "b",
    "error_type": "KeyboardInterrupt",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_executor(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load executor: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.Executor


def run(executor_cls, label: str) -> dict:
    events = []
    thread_errors = []
    original_hook = threading.excepthook
    threading.excepthook = lambda args: thread_errors.append({
        "exception_type": args.exc_type.__name__,
        "exception": str(args.exc_value),
    })

    class Backend:
        sequence = 1

        def validate(self, steps):
            pass

        def execute(self, step, lease, identifier, index):
            error = KeyboardInterrupt("release sink acknowledgement interrupted")
            error.release_batch_publication = dict(PAYLOAD)
            raise error

        def release_all(self):
            return {"verified": True, "keys_down": [], "buttons_down": []}

    try:
        executor = executor_cls(Backend(), events.append)
        executor.submit(label, [{"op": "synthetic_release_batch"}], 1,
                        time.perf_counter_ns() + 1_000_000_000)
        deadline = time.monotonic() + 1
        while not any(event.get("event") == "terminal" for event in events) and time.monotonic() < deadline:
            time.sleep(.002)
        executor.close()
        terminal = next(event for event in events if event.get("event") == "terminal")
        return {"events": events, "terminal": terminal, "thread_errors": thread_errors}
    finally:
        threading.excepthook = original_hook


def main() -> int:
    sys.path.insert(0, str(LIVE))
    try:
        baseline_executor = load_executor("baseline_executor_v13", BASELINE)
        candidate_executor = load_executor("candidate_executor_v13", CANDIDATE)
        output = {
            "experiment_id": "release-batch-baseexception-59-a01",
            "command": "python experiment.py; python audit.py",
            "baseline_commit": "bf57eb60009867bfa36243a9b48e37bd576682c7",
            "baseline_git_blob": "7ef003f5d1ae9c2aef4ac9eb4a4cb7a1ced1195c",
            "baseline_source_sha256": sha256(BASELINE),
            "candidate_source_sha256": sha256(CANDIDATE),
            "experiment_source_sha256": sha256(Path(__file__).resolve()),
            "freeze_sha256": sha256(HERE / "FREEZE.json"),
            "custody_payload": PAYLOAD,
            "baseline": run(baseline_executor, "base-sink-failure"),
            "candidate": run(candidate_executor, "base-sink-failure"),
        }
    finally:
        sys.path.remove(str(LIVE))
        sys.modules.pop("executor_v13", None)
    (HERE / "RUN.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
