"""Zero-fit construction tests for exact launcher and online-window contracts."""
from pathlib import Path
import tempfile
import unittest

import protocol


class DockerArgvContract(unittest.TestCase):
    def test_realized_argv_matches_exact_frozen_token_array(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "fresh-output"
            source.mkdir()
            output.mkdir()
            argv = protocol.docker_argv(source, output)
            self.assertTrue(protocol.exact_argv_matches(argv, list(argv)))
            self.assertEqual(argv.count("--network=none"), 1)
            self.assertIn("--entrypoint=python", argv)
            self.assertIn("-B", argv)
            self.assertIn("/src/runner.py", argv)

    def test_rejects_token_split_missing_extra_reordered_and_mount_mutations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "fresh-output"
            source.mkdir()
            output.mkdir()
            expected = protocol.docker_argv(source, output)
            mutations = []
            split_network = list(expected)
            at = split_network.index("--network=none")
            split_network[at:at + 1] = ["--network", "none"]
            mutations.append(split_network)
            mutations.append(expected[:-1])
            mutations.append(expected + ["--privileged"])
            reordered = list(expected)
            reordered[2], reordered[3] = reordered[3], reordered[2]
            mutations.append(reordered)
            wrong_mount = list(expected)
            mount_index = wrong_mount.index("--mount") + 1
            wrong_mount[mount_index] = wrong_mount[mount_index].replace("target=/src", "dst=/src")
            mutations.append(wrong_mount)
            for actual in mutations:
                self.assertFalse(protocol.exact_argv_matches(actual, expected), actual)

    def test_rejects_aliasing_and_nonexistent_mounts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "source", root / "source" / "output"
            source.mkdir()
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "disjoint"):
                protocol.docker_argv(source, output)
            with self.assertRaisesRegex(ValueError, "existing directories"):
                protocol.docker_argv(source, root / "missing")


class OnlineWindowContract(unittest.TestCase):
    def setUp(self):
        self.record = {
            "queries": [{"query_id": "q-1", "worker_id": "inference-1",
                         "inference_start_ns": 100, "inference_end_ns": 220,
                         "inference_calls": [{"call_start_ns": 110, "call_end_ns": 160}]}],
            "feedback": [{"feedback_id": "f-1", "query_id": "q-1",
                          "arrived_ns": 120, "consumed_ns": 145,
                          "update_start_ns": 130, "update_end_ns": 180,
                          "trainer_worker_id": "trainer-1"}],
        }

    def test_accepts_new_feedback_consumed_and_updated_inside_live_query(self):
        self.assertEqual(protocol.online_window_errors(self.record), [])

    def test_rejects_precomputed_or_late_feedback(self):
        for arrival in (99, 221):
            mutated = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0]) ]}
            mutated["feedback"][0]["arrived_ns"] = arrival
            self.assertTrue(protocol.online_window_errors(mutated))

    def test_rejects_nonoverlap_same_worker_and_missing_query(self):
        mutations = []
        late_update = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0])]}
        late_update["feedback"][0].update(update_start_ns=230, update_end_ns=250,
                                           consumed_ns=240)
        mutations.append(late_update)
        same_worker = {"queries": [dict(self.record["queries"][0])],
                       "feedback": [dict(self.record["feedback"][0])]}
        same_worker["feedback"][0]["trainer_worker_id"] = "inference-1"
        mutations.append(same_worker)
        missing_query = {"queries": [], "feedback": [dict(self.record["feedback"][0])]}
        mutations.append(missing_query)
        for record in mutations:
            self.assertTrue(protocol.online_window_errors(record))

    def test_rejects_wait_only_window_without_overlapping_inference_call(self):
        mutated = {"queries": [dict(self.record["queries"][0])],
                   "feedback": [dict(self.record["feedback"][0])]}
        mutated["queries"][0]["inference_calls"] = [
            {"call_start_ns": 190, "call_end_ns": 210}]
        self.assertTrue(protocol.online_window_errors(mutated))

    def test_rejects_empty_and_malformed_evidence(self):
        self.assertTrue(protocol.online_window_errors({"queries": [], "feedback": []}))
        self.assertTrue(protocol.online_window_errors(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
