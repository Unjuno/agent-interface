"""Pinned-runtime unit gate for the v10 15-second observe-only lease."""
from __future__ import annotations

import threading
import time
import unittest

from executor_v12 import Executor


class Backend:
    sequence = 1

    def validate(self, steps):
        if steps != [{"op": "observe"}]:
            raise ValueError("observe-only refresh expected")

    def execute(self, step, cancel, identifier, index):
        if step != {"op": "observe"}:
            raise AssertionError(step)

    def release_all(self):
        return {"verified": True, "keys_down": [], "buttons_down": []}


class RefreshLeaseTests(unittest.TestCase):
    def test_fifteen_second_observe_is_admitted_completed_and_released(self):
        rows = []
        terminal = threading.Event()

        def emit(row):
            rows.append(row)
            if row.get("event") == "terminal":
                terminal.set()

        executor = Executor(Backend(), emit)
        try:
            executor.submit(
                "refresh-15s",
                [{"op": "observe"}],
                1,
                time.perf_counter_ns() + 15_000_000_000,
            )
            self.assertTrue(terminal.wait(3), rows)
            accepted = next(row for row in rows if row.get("event") == "accepted")
            result = next(row for row in rows if row.get("event") == "terminal")
            self.assertEqual(accepted["id"], "refresh-15s")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(
                result["release"],
                {"verified": True, "keys_down": [], "buttons_down": []},
            )
        finally:
            executor.close()

    def test_expired_deadline_is_rejected(self):
        executor = Executor(Backend(), lambda _: None)
        try:
            with self.assertRaisesRegex(Exception, "intent validity expired"):
                executor.submit(
                    "expired", [{"op": "observe"}], 1,
                    time.perf_counter_ns() - 1_000_000,
                )
        finally:
            executor.close()

    def test_over_thirty_second_deadline_is_rejected(self):
        executor = Executor(Backend(), lambda _: None)
        try:
            with self.assertRaisesRegex(
                ValueError, "deadline exceeds 30 second admission horizon"
            ):
                executor.submit(
                    "over30", [{"op": "observe"}], 1,
                    time.perf_counter_ns() + 31_000_000_000,
                )
        finally:
            executor.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
