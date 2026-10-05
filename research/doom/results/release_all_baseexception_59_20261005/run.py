"""Run a frozen ExecutorV13 cleanup-interruption comparison from Git sources."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FREEZE = Path(__file__).with_name("FREEZE.json")
RAW = Path(__file__).with_name("raw.json")
LIVE = ROOT / "research" / "live_control"
EXECUTOR_PATH = "research/live_control/executor_v13.py"
DEPENDENCIES = (
    "research/live_control/executor_v12.py",
    "research/live_control/executor_v3.py",
    "research/live_control/lease_release_v1.py",
)
CUSTODY = {
    "schema": "release-batch-delivery-v1",
    "identifier": "cleanup-interrupt",
    "step": 0,
    "size": 1,
    "positions": [{"position": 0, "step": 0, "key": "a", "state": "unknown"}],
}


def git_blob(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def executor_from_commit(commit):
    source = git_blob(commit, EXECUTOR_PATH)
    module_name = f"executor_v13_release_a01_{commit[:8]}"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(source, f"<{commit}:{EXECUTOR_PATH}>", "exec"), module.__dict__)
    return module.Executor, source


def run_case(commit, include_custody):
    Executor, executor_source = executor_from_commit(commit)

    class SyntheticBackend:
        sequence = 1

        def validate(self, steps):
            return None

        def execute(self, step, lease, identifier, index):
            return None

        def release_all(self):
            error = KeyboardInterrupt("release sink interrupted during cleanup")
            if include_custody:
                error.release_batch_publication = dict(CUSTODY)
            raise error

    events = []
    escaped = []
    escaped_event = threading.Event()
    previous_hook = threading.excepthook

    def capture_worker_exception(args):
        escaped.append(type(args.exc_value).__name__)
        escaped_event.set()

    threading.excepthook = capture_worker_exception
    executor = Executor(SyntheticBackend(), events.append)
    try:
        executor.submit(
            "cleanup-interrupt", [{"op": "pointer_drag"}], 1,
            time.perf_counter_ns() + 1_000_000_000,
        )
        escaped_event.wait(2)
        executor.close()
    finally:
        threading.excepthook = previous_hook

    terminals = [event for event in events if event.get("event") == "terminal"]
    terminal = terminals[0] if terminals else None
    return {
        "commit": commit,
        "executor_source_sha256": sha256(executor_source),
        "include_custody": include_custody,
        "terminal_count": len(terminals),
        "terminal_status": terminal.get("status") if terminal else None,
        "terminal_error": terminal.get("error") if terminal else None,
        "release": terminal.get("release") if terminal else None,
        "worker_excepthook": escaped,
        "active_after_close": executor.active is not None,
    }


def main():
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    baseline = frozen["sources"]["baseline_commit"]
    candidate = frozen["sources"]["candidate_commit"]
    sys.path.insert(0, str(LIVE))
    baseline_dependencies = {path: sha256(git_blob(baseline, path)) for path in DEPENDENCIES}
    candidate_dependencies = {path: sha256(git_blob(candidate, path)) for path in DEPENDENCIES}
    result = {
        "experiment": frozen["experiment"],
        "host": sys.platform,
        "python": sys.version.split()[0],
        "dependency_sha256": baseline_dependencies,
        "dependencies_identical": baseline_dependencies == candidate_dependencies,
        "baseline": run_case(baseline, include_custody=True),
        "candidate": run_case(candidate, include_custody=True),
        "scope": "synthetic ExecutorV13/release sink only; no OS input or live allocation",
    }
    result["candidate_dependency_sha256"] = candidate_dependencies
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    RAW.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
