import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("readiness_once.py")


class ReadinessOnceTests(unittest.TestCase):
    def barrier(self):
        self.assertTrue(MODULE.is_file(), "readiness reentrancy guard missing")
        spec = importlib.util.spec_from_file_location("ready_guard", MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.ReadinessOnce()

    def test_reentrant_update_schedules_only_one_finalizer(self):
        gate = self.barrier()
        calls = []
        def update():
            calls.append("update")
            self.assertFalse(gate.prepare(lambda: calls.append("nested-update"),
                lambda: True, lambda: calls.append("retry"),
                lambda: calls.append("nested-schedule")))
        self.assertTrue(gate.prepare(update, lambda: True,
                        lambda: calls.append("retry"), lambda: calls.append("schedule")))
        self.assertEqual(calls, ["update", "schedule"])

    def test_repeated_map_callbacks_cannot_schedule_again(self):
        gate = self.barrier()
        calls = []
        args = (lambda: calls.append("update"), lambda: True,
                lambda: calls.append("retry"), lambda: calls.append("schedule"))
        self.assertTrue(gate.prepare(*args))
        self.assertFalse(gate.prepare(*args))
        self.assertEqual(calls, ["update", "schedule"])

    def test_not_ready_allows_a_later_bounded_poll(self):
        gate = self.barrier()
        calls = []
        self.assertFalse(gate.prepare(lambda: calls.append("u1"), lambda: False,
            lambda: calls.append("retry"), lambda: calls.append("wrong-schedule")))
        self.assertTrue(gate.prepare(lambda: calls.append("u2"), lambda: True,
            lambda: calls.append("wrong-retry"), lambda: calls.append("schedule")))
        self.assertEqual(calls, ["u1", "retry", "u2", "schedule"])

    def test_finalizer_cannot_reenter_or_repeat(self):
        gate = self.barrier()
        gate.prepare(lambda: None, lambda: True, lambda: None, lambda: None)
        calls = []
        def finish():
            calls.append("first")
            self.assertFalse(gate.finalize(lambda: calls.append("nested")))
        self.assertTrue(gate.finalize(finish))
        self.assertFalse(gate.finalize(lambda: calls.append("repeat")))
        self.assertEqual(calls, ["first"])

    def test_finalization_before_readiness_is_refused(self):
        gate = self.barrier()
        calls = []
        self.assertFalse(gate.finalize(lambda: calls.append("premature")))
        self.assertEqual(calls, [])

    def test_update_failure_is_not_automatically_retried(self):
        gate = self.barrier()
        def fail():
            raise RuntimeError("first failure")
        with self.assertRaisesRegex(RuntimeError, "first failure"):
            gate.prepare(fail, lambda: True, lambda: None, lambda: None)
        calls = []
        self.assertFalse(gate.prepare(lambda: calls.append("replay"), lambda: True,
            lambda: None, lambda: calls.append("schedule")))
        self.assertFalse(gate.finalize(lambda: calls.append("finish")))
        self.assertEqual(calls, [])

    def test_finalizer_failure_is_not_automatically_retried(self):
        gate = self.barrier()
        gate.prepare(lambda: None, lambda: True, lambda: None, lambda: None)
        def fail():
            raise RuntimeError("first failure")
        with self.assertRaisesRegex(RuntimeError, "first failure"):
            gate.finalize(fail)
        calls = []
        self.assertFalse(gate.finalize(lambda: calls.append("replay")))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
