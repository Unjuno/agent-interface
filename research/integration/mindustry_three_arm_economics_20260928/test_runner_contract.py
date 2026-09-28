"""Construction checks for the host-only six-task lifecycle contract."""

import unittest

from runner_contract import Lifecycle, arm_schedule, load_plan


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_plan()

    def test_exact_arm_call_totals_and_routes(self):
        expected = {"plain": (6, 6), "ephemeral": (6, 6), "persistent": (6, 2)}
        for arm, totals in expected.items():
            with self.subTest(arm=arm):
                schedule = arm_schedule(self.plan, arm)
                self.assertEqual((len(schedule), sum(t.model_calls for t in schedule)), totals)
                self.assertEqual([t.layout for t in schedule], ["A", "A", "A", "B", "B", "B"])

    def test_failed_score_forbids_reset_and_advance(self):
        run = Lifecycle(self.plan)
        run.score(False)
        with self.assertRaisesRegex(ValueError, "passing score"):
            run.reset(True)
        with self.assertRaisesRegex(ValueError, "verified reset"):
            run.advance()

    def test_unverified_reset_witness_stops_before_next_task(self):
        run = Lifecycle(self.plan)
        run.score(True)
        run.reset(False)
        with self.assertRaisesRegex(ValueError, "verified reset"):
            run.advance()
        self.assertEqual(run.current.task_id, "A1")

    def test_geometry_flip_occurs_once_between_a3_and_b1(self):
        run = Lifecycle(self.plan)
        ready = []
        for expected in ("A1", "A2", "A3", "B1", "B2", "B3"):
            self.assertEqual(run.current.task_id, expected)
            run.score(True)
            run.reset(True)
            ready.append(run.advance())
        changes = [e for e in run.events if e["event"] == "geometry_mutation"]
        self.assertEqual(changes, [{"event": "geometry_mutation",
            "after": "A3.reset_witness", "before": "B1.task_ready",
            "from_layout": "A", "to_layout": "B"}])
        self.assertEqual([e["task_id"] for e in ready if e and e["event"] == "task_ready"],
                         ["A2", "A3", "B1", "B2", "B3"])
        self.assertEqual(run.phase, "complete")

    def test_rejects_schedule_drift(self):
        mutated = dict(self.plan)
        mutated["routes"] = dict(self.plan["routes"])
        mutated["routes"]["persistent"] = ["cold"] * 6
        with self.assertRaisesRegex(ValueError, "route or model-call schedule"):
            arm_schedule(mutated, "persistent")


if __name__ == "__main__":
    unittest.main()
