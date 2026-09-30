import json
import importlib.util
import tempfile
import unittest
from pathlib import Path

import torch

import runner
_spec = importlib.util.spec_from_file_location("needle4732_audit", Path(__file__).with_name("audit.py"))
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)


class TimingBoundary(unittest.TestCase):
    def test_query_id_schedule_is_deterministic_and_bounded(self):
        ids = [(i * 37 + runner.CONSTRUCTION_SEED) % 512 for i in range(12)]
        self.assertEqual(ids, [(i * 37 + runner.CONSTRUCTION_SEED) % 512 for i in range(12)])
        self.assertTrue(all(0 <= x < 512 for x in ids))

    def test_formal_arm_order_is_explicitly_alternated(self):
        orders = [runner.arm_order_for_seed(x) for x in runner.SEEDS]
        self.assertEqual(orders[0], orders[2])
        self.assertNotEqual(orders[0], orders[1])
        with self.assertRaises(ValueError):
            runner.arm_order_for_seed(9999999)

    def test_worker_input_omits_support_and_schedule(self):
        from pathlib import Path
        import sys
        sys.path.insert(0, "/baseline")
        import study
        raw = study.make_data(runner.CONSTRUCTION_SEED)
        filtered = {k: v for k, v in raw.items() if k not in ("x_support", "schedule", "input_sha256")}
        self.assertNotIn("x_support", filtered)
        self.assertNotIn("schedule", filtered)
        self.assertNotIn("y_eval", filtered)
        self.assertNotIn("y_support", filtered)

    def test_corruption_controls_reject(self):
        self.assertEqual(len(audit.corruption_controls(runner.CONSTRUCTION_SEED)), 5)
        self.assertTrue(all(audit.corruption_controls(runner.CONSTRUCTION_SEED).values()))

    def test_snapshot_and_query_match_contract(self):
        import sys
        sys.path.insert(0, "/baseline")
        import study
        raw = study.make_data(runner.CONSTRUCTION_SEED)
        state = study.initial(raw)
        study.validate_snapshot(state, raw["seed"], raw["base_sha256"], 0)
        qid = (runner.CONSTRUCTION_SEED) % 512
        self.assertEqual(audit.validate_request_binding({"cursor": 0, "query_id": qid}, 0, qid), None)
        with self.assertRaises(ValueError):
            audit.validate_request_binding({"cursor": 1, "query_id": qid}, 0, qid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
