"""V2 construction checks only: no optimizer step or formal model evaluation."""
import hashlib
import json
from pathlib import Path
import unittest

import formal_v2
import runner_v2

HERE = Path(__file__).resolve().parent
V1 = Path("/src/v1")
if not V1.is_dir():
    V1 = HERE.parent / "needle_lora_rank1_online_skill_v1"


class V2ConstructionTests(unittest.TestCase):
    def test_allocation_and_fresh_seed_ranges(self):
        self.assertEqual(runner_v2.ALLOCATION, "needle-lora-rank1-online-skill-v2")
        self.assertEqual(runner_v2.SEEDS, (74111, 74222, 74333))
        offsets = runner_v2.frozen_runner.SEED_OFFSETS
        blocks = [{seed + offset for offset in offsets} for seed in runner_v2.SEEDS]
        for index, left in enumerate(blocks):
            for right in blocks[index + 1:]:
                self.assertTrue(left.isdisjoint(right))

    def test_v1_dependency_hashes_and_stop_artifacts_are_preserved(self):
        freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        for relative, expected in freeze["dependency_sha256"].items():
            observed = hashlib.sha256((V1 / relative).read_bytes()).hexdigest()
            self.assertEqual(observed, expected, relative)
        self.assertTrue((V1 / "formal" / "stop-01" / "STOP.json").is_file())

    def test_rank_schedule_and_routing_are_unchanged_without_training(self):
        impl = runner_v2.frozen_runner
        self.assertEqual(impl.RANKS, (1, 2))
        _, schedule = impl.make_schedule(runner_v2.SEEDS[0])
        self.assertEqual(len(schedule), 16)
        self.assertTrue(all(len(item["batches"]) == 8 for item in schedule))
        self.assertEqual(impl.route("A", 0, {}), "BASE")
        self.assertEqual(impl.route("B", 1, {"B": object()}), "LORA_B")
        self.assertEqual(impl.route("B", 2, {"B": object()}), "YIELD")

    def test_training_writes_to_separate_empty_subdirectory(self):
        freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        image = freeze["docker_image_id"]
        train = formal_v2.docker_command(image, HERE, V1, HERE, "runner_v2.py",
                                         ["--out", "/out/training"])
        audit = formal_v2.docker_command(image, HERE, V1, HERE, "audit_v2.py",
                                         ["--source", "/src/v2", "--dependency", "/src/v1", "--out", "/out"])
        for argv in (train, audit):
            joined = " ".join(argv)
            for fragment in ("--pull=never", "--platform linux/amd64", "--network none",
                             "--read-only", "--memory 2g", "--cpus 1", "--pids-limit 64"):
                self.assertIn(fragment, joined)
            self.assertEqual(argv.count("--mount"), 3)
            self.assertEqual(argv[argv.index("--entrypoint") + 1], "python")
            self.assertIn("target=/src/v2,readonly", joined)
            self.assertIn("target=/src/v1,readonly", joined)
        self.assertIn("/out/training", train)
        self.assertNotIn("/out/training", audit)


if __name__ == "__main__":
    unittest.main(verbosity=2)
