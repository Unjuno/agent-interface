"""Construction-only tests: these must never call the trainer or formal orchestrator."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
import runner
import loader
import formal


class RobustnessConstructionTests(unittest.TestCase):
    def test_seed_component_streams_do_not_overlap(self):
        streams = [{seed + offset for offset in range(13)} for seed in formal.SEEDS]
        retired = (3788, 3789, 3790, *range(3792, 4693, 100), *range(100000, 100901, 100))
        retired_streams = {seed + offset for seed in retired for offset in range(13)}
        self.assertEqual(len(formal.SEEDS), 10)
        self.assertEqual(len(set(formal.SEEDS)), 10)
        self.assertFalse(set.union(*streams) & retired_streams)
        for i, left in enumerate(streams):
            for right in streams[i + 1:]:
                self.assertFalse(left & right)

    def test_seeded_data_and_teacher_are_deterministic_without_training(self):
        with patch.object(runner, "train", side_effect=AssertionError("construction called train")):
            x = runner.data(16, 3793)
            self.assertTrue(torch.equal(x, runner.data(16, 3793)))
            self.assertFalse(torch.equal(x, runner.data(16, 3794)))
            self.assertTrue(torch.equal(runner.labels(x, "A"), runner.labels(x, "A")))
            self.assertTrue(torch.all(runner.labels(x, "B") != runner.labels(x, "A")))

    def test_loader_binds_exact_artifact_digest_and_contract(self):
        state = {"enc.0.weight": [[0.0] * 8 for _ in range(16)],
                 "enc.0.bias": [0.0] * 16,
                 "head.weight": [[0.0] * 16 for _ in range(4)],
                 "head.bias": [0.0] * 4}
        adapter = {"core.enc.0.weight": [[0.0] * 8 for _ in range(16)],
                   "core.enc.0.bias": [0.0] * 16,
                   "core.head.weight": [[0.0] * 16 for _ in range(4)],
                   "core.head.bias": [0.0] * 4,
                   "a": [[0.0] * 2 for _ in range(16)],
                   "b": [[0.0] * 4 for _ in range(2)]}
        value = {"schema": loader.SCHEMA, "generation": 913000,
                 "architecture": {"input": 8, "hidden": 16, "classes": 4,
                                  "rank": 2, "roles": ["A", "B", "C"]},
                 "graph": {"nodes": [{"id": r, "version": r + "-v1"} for r in ("A", "B", "C")],
                           "edges": [["A", "B"], ["B", "C"]], "scope": "synthetic-fixture-v1"},
                 "provenance": {"allocation": loader.ALLOCATION, "issue": 4619,
                                "issue_contract_sha256": loader.ISSUE_CONTRACT_SHA256,
                                "predecessor_issue": 3890, "seed": 913000,
                                "family": "synthetic-role-adapter-v1"},
                 "tensors": {"A": state, "B": adapter, "C": adapter}}
        value["payload_sha256"] = loader.hash_payload(value)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "skill.json"
            p.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            obj, raw_sha = loader.validate(p, 913000)
            self.assertEqual(raw_sha, hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(obj["payload_sha256"], value["payload_sha256"])
            value["payload_sha256"] = "0" * 64
            p.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(ValueError):
                loader.validate(p, 913000)

    def test_missing_or_invalid_training_environment_stops_before_fit(self):
        with patch.dict(os.environ, {"NEEDLE_SEED": "", "NEEDLE_OUTPUT": ""}):
            with patch.object(runner, "train") as fit:
                with self.assertRaises(SystemExit) as raised:
                    runner.main()
                self.assertEqual(str(raised.exception), "STOP_INVALID_TRAINING_ENV")
                fit.assert_not_called()

    def test_builder_output_is_gzip_deterministic_schema_only_no_fit(self):
        raw = json.dumps({"seed": 913000, "rows": [[0.0] * 8]},
                         sort_keys=True, separators=(",", ":")).encode()
        first = gzip.compress(raw, mtime=0)
        second = gzip.compress(raw, mtime=0)
        self.assertEqual(first, second)
        self.assertEqual(gzip.decompress(first), raw)

    def test_docker_command_builder_has_isolation_and_disjoint_mounts(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source"
            output = Path(td) / "out"
            source.mkdir()
            output.mkdir()
            cmd = formal.commands(source, output, formal.SEEDS[0])
            for name, argv in cmd.items():
                joined = " ".join(argv)
                self.assertIn("--network none", joined)
                self.assertIn("--read-only", joined)
                self.assertIn("--pids-limit 64", joined)
                self.assertIn("--memory 2g", joined)
                self.assertIn("--cpus 1", joined)
                self.assertIn(formal.IMAGE_ID, joined)
                self.assertNotIn("needle-pilot05:local", joined)
                self.assertEqual(argv.count("--mount"), 3 if name != "builder" else 2)
                if name == "builder":
                    self.assertIn("NEEDLE_SEED=913000", argv)
                    self.assertIn("NEEDLE_OUTPUT=/out", argv)
                    self.assertEqual(argv.count("--env"), 2)
            builder_mounts = [arg for arg in cmd["builder"] if arg.startswith("type=bind") and "target=/out" in arg]
            self.assertEqual(len(builder_mounts), 1)
            self.assertIn("seed-913000/builder", builder_mounts[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
