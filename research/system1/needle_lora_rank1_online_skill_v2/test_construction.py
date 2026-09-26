"""Construction-only checks. No optimizer step or formal output is produced."""
import json
import tempfile
from pathlib import Path
import unittest

import formal
from runner import (ALLOCATION, DOCKER_IMAGE_ID, H, ISSUE, N_SUPPORT, RANKS, SEED_OFFSETS,
                    SEEDS, UPDATES_PER_ARRIVAL, Core, LoRA, initialize_paired_adapters,
                    make_schedule, output_directory_ready, route)
import torch

ROOT = Path(__file__).resolve().parent


class ConstructionTests(unittest.TestCase):
    def test_fresh_seed_offset_ranges_are_disjoint(self):
        derived = [{seed + off for off in SEED_OFFSETS} for seed in SEEDS]
        for index, left in enumerate(derived):
            for right in derived[index + 1:]:
                self.assertTrue(left.isdisjoint(right))
        predecessor = {seed + off for seed in (73111, 73222, 73333) for off in SEED_OFFSETS}
        self.assertTrue(all(block.isdisjoint(predecessor) for block in derived))
        self.assertEqual(len(SEEDS), 3)

    def test_rank_shapes_and_initial_function_are_paired(self):
        torch.manual_seed(1)
        base = Core()
        arms = initialize_paired_adapters(base, SEEDS[0])
        self.assertEqual(tuple(arms), RANKS)
        self.assertEqual(tuple(arms[1][0].a.shape), (H, 1))
        self.assertEqual(tuple(arms[2][0].a.shape), (H, 2))
        self.assertEqual(tuple(arms[1][0].b.shape), (1, 4))
        self.assertEqual(tuple(arms[2][0].b.shape), (2, 4))
        x = torch.randn(8, 8)
        with torch.no_grad():
            self.assertTrue(torch.equal(arms[1][0](x), arms[2][0](x)))

    def test_frozen_schedule_has_sixteen_arrivals_and_128_updates(self):
        _, schedule = make_schedule(SEEDS[0])
        self.assertEqual(len(schedule), N_SUPPORT)
        self.assertTrue(all(len(item["batches"]) == UPDATES_PER_ARRIVAL for item in schedule))
        self.assertEqual(sum(len(item["batches"]) for item in schedule), 128)

    def test_role_version_gate_fails_closed(self):
        self.assertEqual(route("A", 0, {}), "BASE")
        self.assertEqual(route("B", 1, {"B": object()}), "LORA_B")
        for role, version, adapters in (("C", 1, {"B": object()}), ("B", 0, {"B": object()}),
                                        ("B", 2, {"B": object()}), ("B", 1, {})):
            self.assertEqual(route(role, version, adapters), "YIELD")

    def test_docker_invocations_are_local_isolated_and_hashable(self):
        train = formal.docker_command("image-id", ROOT, ROOT, "runner.py", ["--out", "/out"])
        audit = formal.docker_command("image-id", ROOT, ROOT, "audit.py", ["--source", "/src", "--out", "/out"])
        for argv in (train, audit):
            joined = " ".join(argv)
            for token in ("--pull=never", "--platform linux/amd64", "--network none",
                          "--read-only", "--pids-limit 64", "--memory 2g", "--cpus 1"):
                self.assertIn(token, joined)
            self.assertEqual(argv[argv.index("--entrypoint") + 1], "python")
            self.assertEqual(argv.count("--mount"), 2)
        self.assertEqual(json.loads((ROOT / "PREREGISTRATION.json").read_text())["issue"], ISSUE)

    def test_output_contract_accepts_only_exact_invocation_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            self.assertTrue(output_directory_ready(out))
            marker = {"schema": "needle-rank1-formal-invocation.v1", "allocation": ALLOCATION,
                      "issue": ISSUE, "formal_invocations": 1, "retry_count": 0,
                      "docker_image_id": DOCKER_IMAGE_ID}
            (out / "FORMAL_INVOCATION.json").write_text(json.dumps(marker), encoding="utf-8")
            self.assertTrue(output_directory_ready(out))
            marker["retry_count"] = 1
            (out / "FORMAL_INVOCATION.json").write_text(json.dumps(marker), encoding="utf-8")
            self.assertFalse(output_directory_ready(out))
            marker["retry_count"] = 0
            marker["issue"] = 4507
            (out / "FORMAL_INVOCATION.json").write_text(json.dumps(marker), encoding="utf-8")
            self.assertFalse(output_directory_ready(out))
            (out / "unrelated.txt").write_text("x", encoding="utf-8")
            self.assertFalse(output_directory_ready(out))


if __name__ == "__main__":
    unittest.main(verbosity=2)
