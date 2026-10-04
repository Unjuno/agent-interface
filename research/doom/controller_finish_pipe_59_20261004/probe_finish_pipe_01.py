"""Single-run WSLc probe for a full child-stdin pipe during exception cleanup."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time


def load_cleanup(source):
    spec = importlib.util.spec_from_file_location(
        "frozen_controller_failure_cleanup", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ControllerFailureCleanup


class Planner:
    def __init__(self):
        self.closed = threading.Event()

    def close(self, timeout=1):
        self.closed.set()


def fill_pipe(child):
    fd = child.stdin.fileno()
    os.set_blocking(fd, False)
    total = 0
    try:
        while True:
            total += os.write(fd, b"x" * 65536)
    except BlockingIOError:
        pass
    finally:
        os.set_blocking(fd, True)
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cleanup_source = args.source / "doom_controller_failure_cleanup_v1.py"
    helper_hash = hashlib.sha256(cleanup_source.read_bytes()).hexdigest()
    cleanup_type = load_cleanup(cleanup_source)
    child = subprocess.Popen(
        [sys.executable, "-u", "-c", "import time; time.sleep(60)"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    filled = fill_pipe(child)
    planner = Planner()
    primary = RuntimeError("frozen-primary-controller-error")
    result = {"schema": "doom-controller-finish-pipe-probe-v1",
              "source_sha256": helper_hash, "pipe_fill_bytes": filled,
              "primary_exception_preserved": False,
              "blocked_after_barrier": False, "child_alive_at_barrier": False,
              "planner_closed_at_barrier": None,
              "external_cleanup": None, "cleanup_thread_error": None}

    def trigger_cleanup():
        try:
            with cleanup_type(planner, args.out) as scope:
                scope.track(child)
                raise primary
        except RuntimeError as error:
            result["primary_exception_preserved"] = error is primary
        except BaseException as error:
            result["cleanup_thread_error"] = type(error).__name__

    worker = threading.Thread(target=trigger_cleanup, name="cleanup-probe", daemon=True)
    started = time.monotonic_ns()
    worker.start()
    worker.join(.5)
    result["blocked_after_barrier"] = worker.is_alive()
    result["child_alive_at_barrier"] = child.poll() is None
    result["planner_closed_at_barrier"] = planner.closed.is_set()
    result["barrier_elapsed_ms"] = (time.monotonic_ns() - started) / 1e6
    if worker.is_alive():
        child.kill()
        result["external_cleanup"] = {"action": "probe_kill_owned_child",
                                       "exit_code": child.wait(timeout=3)}
        worker.join(3)
    else:
        result["external_cleanup"] = {"action": "not_needed"}
    result["cleanup_thread_joined"] = not worker.is_alive()
    result["planner_closed_after_external_release"] = planner.closed.is_set()
    report = args.out / "result.json"
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if worker.is_alive():
        return 2
    return 0 if result["blocked_after_barrier"] and not result[
        "planner_closed_at_barrier"] and result["external_cleanup"]["action"] == \
        "probe_kill_owned_child" else 1


if __name__ == "__main__":
    raise SystemExit(main())
