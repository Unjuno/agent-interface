"""Deterministic concurrency characterization for the Allocation 06 host gate."""
import importlib.util
import json
import subprocess
import sys
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ALLOCATION_DIR = ROOT / "research" / "live_control" / "owner_keyup_formal_x11_5156_20261001_06"
if str(ALLOCATION_DIR) not in sys.path:
    sys.path.insert(0, str(ALLOCATION_DIR))
import invoke_allocation as original


def _load_guard():
    path = Path(__file__).with_name("race_guard.py")
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("race_guard_t1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot():
    return {
        "main_sha": original.FROZEN_MAIN,
        "docker_context": original.CONTEXT,
        "running_containers": [],
        "image_id": original.IMAGE_ID,
        "image_platform": original.PLATFORM,
        "queue_reconciled": True,
        "queue_conflict": False,
    }


def _trial(dispatch, rendezvous_after_gate=False):
    counts = {"candidate": 0, "audit": 0}
    counts_lock = threading.Lock()
    start_barrier = threading.Barrier(2)
    gate_barrier = threading.Barrier(2) if rendezvous_after_gate else None
    now = datetime(2026, 9, 30, 17, 40, tzinfo=timezone.utc)

    def candidate():
        with counts_lock:
            counts["candidate"] += 1
        return {"returncode": 0, "stdout": "fixture", "stderr": ""}

    def auditor():
        with counts_lock:
            counts["audit"] += 1
        return {"returncode": 0, "stdout": "audit", "stderr": ""}

    previous_gate = original.gate_errors
    if gate_barrier is not None:
        def synchronized_gate(snapshot, checked_at, results_dir):
            errors = previous_gate(snapshot, checked_at, results_dir)
            gate_barrier.wait(timeout=5)
            return errors
        original.gate_errors = synchronized_gate
    try:
        with tempfile.TemporaryDirectory() as temporary:
            result_dir = Path(temporary)
            statuses = []
            def worker():
                start_barrier.wait(timeout=5)
                return dispatch(_snapshot(), now, candidate, auditor, result_dir)
            threads = [threading.Thread(target=lambda: statuses.append(worker()))
                       for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            if any(thread.is_alive() for thread in threads):
                raise TimeoutError("concurrent dispatch did not finish")
            result = {"statuses": sorted(statuses), "counts": counts}
            for name in ("START.json", "EXECUTION.json", "INVOCATION_CLAIM.json"):
                path = result_dir / name
                if path.is_file():
                    result[name] = json.loads(path.read_text(encoding="utf-8"))
            return result
    finally:
        original.gate_errors = previous_gate


class InvocationRaceTests(unittest.TestCase):
    def test_experiment_entrypoint_imports_from_a_clean_python_process(self):
        package = Path(__file__).parent
        result = subprocess.run(
            [sys.executable, "-c", "import run_experiment"],
            cwd=package, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_dispatcher_reproduces_two_candidates_after_both_pass_gate(self):
        result = _trial(original.run_one_shot, rendezvous_after_gate=True)
        self.assertEqual(result["counts"]["candidate"], 2)
        self.assertEqual(result["counts"]["audit"], 2)
        self.assertEqual(result["statuses"], [0, 0])

    def test_atomic_claim_dispatch_admits_only_one_candidate(self):
        guard = _load_guard()
        self.assertIsNotNone(guard, "atomic reservation implementation not yet written")
        result = _trial(guard.run_reserved)
        self.assertEqual(result["counts"]["candidate"], 1)
        self.assertEqual(result["counts"]["audit"], 1)
        self.assertEqual(result["statuses"], [0, 2])
        self.assertEqual(result["INVOCATION_CLAIM.json"]["state"], "RESERVED_NO_RETRY")


if __name__ == "__main__":
    unittest.main()
