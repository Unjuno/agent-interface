import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import invoke_allocation as invoke


def snapshot(**changes):
    state = {
        "main_sha": invoke.FROZEN_MAIN,
        "docker_context": invoke.CONTEXT,
        "running_containers": [],
        "image_id": invoke.IMAGE_ID,
        "image_platform": invoke.PLATFORM,
        "queue_reconciled": True,
        "queue_conflict": False,
    }
    state.update(changes)
    return state


class AllocationWindowGuardTests(unittest.TestCase):
    def test_exact_start_is_allowed_when_full_bounded_budget_remains(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors = invoke.gate_errors(snapshot(), invoke.WINDOW_START, Path(temporary))
            self.assertEqual(errors, [])

    def test_end_boundary_is_outside_the_window(self):
        self.assertIn("outside exact assigned UTC window",
                      invoke.gate_errors(snapshot(), invoke.WINDOW_END))

    def test_naive_clock_is_rejected(self):
        naive = datetime(2026, 9, 30, 17, 40)
        self.assertIn("clock must be timezone-aware UTC", invoke.gate_errors(snapshot(), naive))

    def test_drift_conflict_and_running_container_each_fail_closed(self):
        for altered in (
            snapshot(main_sha="different"),
            snapshot(queue_reconciled=False),
            snapshot(queue_conflict=True),
            snapshot(running_containers=["unrelated-id"]),
        ):
            self.assertTrue(invoke.gate_errors(altered, invoke.WINDOW_START))

    def test_image_and_context_must_match_exact_freeze(self):
        self.assertIn("Docker context mismatch",
                      invoke.gate_errors(snapshot(docker_context="default"), invoke.WINDOW_START))
        self.assertIn("cached image digest mismatch or unavailable",
                      invoke.gate_errors(snapshot(image_id="sha256:wrong"), invoke.WINDOW_START))
        self.assertIn("cached image platform mismatch",
                      invoke.gate_errors(snapshot(image_platform="linux/arm64"), invoke.WINDOW_START))

    def test_window_must_have_time_for_candidate_and_audit_bounds(self):
        late = datetime(2026, 9, 30, 17, 48, tzinfo=timezone.utc)
        self.assertIn("insufficient window remains for bounded runner and audit",
                      invoke.gate_errors(snapshot(), late))

    def test_started_or_stopped_allocation_cannot_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            (results / "START.json").write_text("{}", encoding="utf-8")
            self.assertIn("allocation already has a terminal/start marker; retry forbidden",
                          invoke.gate_errors(snapshot(), invoke.WINDOW_START, results))


class OneShotDispatchTests(unittest.TestCase):
    def test_preflight_stop_invokes_neither_container(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            calls = []
            code = invoke.run_one_shot(snapshot(main_sha="drift"), invoke.WINDOW_START,
                                       lambda: calls.append("candidate"),
                                       lambda: calls.append("audit"), results)
            self.assertEqual(code, 2)
            self.assertEqual(calls, [])
            stop = json.loads((results / "STOP.json").read_text(encoding="utf-8"))
            self.assertEqual(stop["candidate_invocations"], 0)

    def test_failed_candidate_is_not_audited_and_cannot_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            calls = []
            code = invoke.run_one_shot(
                snapshot(), invoke.WINDOW_START,
                lambda: (calls.append("candidate") or {"returncode": 1, "stdout": "", "stderr": "fail"}),
                lambda: (calls.append("audit") or {"returncode": 0}), results)
            self.assertEqual(code, 1)
            self.assertEqual(calls, ["candidate"])
            self.assertEqual(invoke.run_one_shot(snapshot(), invoke.WINDOW_START,
                                                 lambda: calls.append("retry"), lambda: {}, results), 2)
            self.assertEqual(calls, ["candidate"])

    def test_zero_exit_candidate_runs_one_separate_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            calls = []
            code = invoke.run_one_shot(
                snapshot(), invoke.WINDOW_START,
                lambda: (calls.append("candidate") or {"returncode": 0, "stdout": "ok", "stderr": ""}),
                lambda: (calls.append("audit") or {"returncode": 0, "stdout": "pass", "stderr": ""}), results)
            self.assertEqual(code, 0)
            self.assertEqual(calls, ["candidate", "audit"])
            execution = json.loads((results / "EXECUTION.json").read_text(encoding="utf-8"))
            self.assertEqual(execution["candidate_invocations"], 1)
            self.assertEqual(execution["audit_invocations"], 1)
            self.assertEqual(execution["retry"], False)


if __name__ == "__main__":
    unittest.main()
