"""Zero-fit construction guards for CPU binding, oracle shape and identity."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit
import formal
import runner
import torch


class ConstructionTests(unittest.TestCase):
    def test_formal_seed_block_is_fresh_and_exact(self):
        self.assertEqual(runner.SEEDS, (91004321, 91004531, 91004749))
        self.assertEqual(audit.SEEDS, runner.SEEDS)
        self.assertEqual(runner.ARMS, {"CPU2_CONTINUOUS": 2, "CPU2_PULSED": 2})

    def test_cpu_quota_is_exactly_one_or_two(self):
        self.assertEqual(runner.parse_cpu_max("100000 100000")["quota_cores"], 1)
        self.assertEqual(runner.parse_cpu_max("200000 100000")["quota_cores"], 2)
        for value in ("max 100000", "0 100000", "100000 0", "100000"):
            with self.assertRaises(RuntimeError):
                runner.parse_cpu_max(value)

    def test_live_container_quota_matches_selected_construction_arm(self):
        expected = int(os.environ["NEEDLE_EXPECTED_CPUS"])
        self.assertIn(expected, (1, 2))
        self.assertEqual(runner.cpu_quota()["quota_cores"], expected)

    def test_query_oracle_keeps_all_four_logits_without_fitting(self):
        base = {"w1": [[0.0] * 8 for _ in range(16)], "b1": [0.0] * 16,
                "w2": [[0.0] * 16 for _ in range(4)], "b2": [0.0] * 4}
        adapter = {"a": [[0.0] * 16 for _ in range(2)], "b": [[0.0] * 2 for _ in range(4)]}
        got = audit.oracle(base, adapter, [0.0] * 8)
        self.assertEqual(tuple(got.shape), (4,))
        self.assertEqual(got.numel(), 4)
        self.assertTrue(audit.valid_logits(got))
        self.assertFalse(audit.valid_logits(torch.tensor(1.0)))
        self.assertFalse(audit.valid_logits(torch.zeros((1, 4))))

    def test_seed_identity_rejects_mismatched_source_metadata(self):
        raw = {"seed": 88117, "arm": "CPU2_CONTINUOUS"}
        self.assertNotEqual(raw["seed"], 91004321)
        self.assertIn("seed_or_arm_identity",
                      audit.identity_errors(raw, Path("seed_91004321_cpu2_continuous.json"),
                                            91004321, "CPU2_PULSED"))

    def test_snapshot_digest_and_timing_boundaries_are_exact(self):
        item = {"version": 3, "a": [[0.0]], "b": [[1.0]]}
        item["sha256"] = audit.digest(item)
        self.assertEqual(audit.snapshot_digest(item), item["sha256"])
        self.assertFalse(runner.deadline_missed(100, 100))
        self.assertTrue(runner.deadline_missed(101, 100))
        self.assertTrue(runner.intervals_overlap(10, 20, [[19, 21]]))
        self.assertFalse(runner.intervals_overlap(10, 20, [[20, 21]]))

    def test_cow_publication_keeps_captured_versions_immutable_and_rejects_unknown(self):
        lock = __import__("threading").Lock()
        old_a, old_b = torch.zeros((2, 16)), torch.zeros((4, 2))
        active = {"current": runner.immutable_snapshot(old_a, old_b, 0)}
        captured = runner.capture_active(active, lock)
        new_a, new_b = torch.ones((2, 16)), torch.ones((4, 2))
        runner.atomic_publish(active, lock, runner.immutable_snapshot(new_a, new_b, 1))
        new_a.zero_()
        self.assertEqual(captured["version"], 0)
        self.assertTrue(torch.equal(captured["a"], old_a))
        current = runner.capture_active(active, lock)
        self.assertEqual(current["version"], 1)
        self.assertTrue(torch.equal(current["a"], torch.ones((2, 16))))
        with self.assertRaisesRegex(ValueError, "unknown_or_stale_version"):
            audit.available_snapshot({"0": {}}, 1)

    def test_two_cpu_arm_does_not_change_any_training_schedule_constant(self):
        self.assertEqual((runner.ARRIVALS, runner.STEPS_PER_ARRIVAL, runner.BATCH,
                          runner.QUERIES, runner.PERIOD_NS), (12, 16, 512, 120, 16_666_667))
        self.assertEqual(runner.PULSE_AFTER_QUERY_INDICES, tuple(range(0, 120, 10)))

    def test_host_commands_change_only_cpu_quota_and_required_env(self):
        continuous = formal.trainer_argv("src", "out", 91004321, "CPU2_CONTINUOUS", 2)
        pulsed = formal.trainer_argv("src", "out", 91004321, "CPU2_PULSED", 2)
        self.assertEqual(continuous[continuous.index("--cpus") + 1], "2")
        self.assertEqual(pulsed[pulsed.index("--cpus") + 1], "2")
        self.assertEqual(continuous[continuous.index("--cpus") + 1],
                         pulsed[pulsed.index("--cpus") + 1])
        self.assertIn("NEEDLE_EXPECTED_CPUS=2", continuous)
        self.assertIn("NEEDLE_EXPECTED_CPUS=2", pulsed)
        self.assertIn("--network=none", continuous)
        self.assertIn("--read-only", continuous)
        self.assertIn("--pull=never", continuous)

    def test_formal_freeze_guard_stops_before_docker_or_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "src"
            out = Path(temp) / "out"
            source.mkdir()
            (source / "FREEZE.json").write_text(json.dumps({"formal_seeds": []}), encoding="utf-8")
            with patch.object(formal.subprocess, "run") as run:
                with self.assertRaisesRegex(SystemExit, "STOP_FREEZE_SEED_SET"):
                    formal.run(source, out)
                run.assert_not_called()
            self.assertFalse((out / "FORMAL_STARTED.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
