import tempfile
import unittest
from pathlib import Path

import torch

import study


class Construction(unittest.TestCase):
    def test_candidate_outputs_four_logits(self):
        m = study.Adapted(study.Core())
        self.assertEqual(tuple(m(torch.zeros(5, study.D)).shape), (5, study.C))

    def test_snapshot_digest_and_cursor_are_bound(self):
        raw = {"seed": study.SEEDS[0], "base_sha256": "a" * 64,
               "base_state": study.state_dict_list(study.Core()),
               "initial_adapter": {"a": torch.zeros(study.H, 2).tolist(), "b": torch.zeros(2, study.C).tolist()}}
        s = study.initial(raw)
        study.validate_snapshot(s, raw["seed"], raw["base_sha256"], 0)
        s["cursor"] = 1
        with self.assertRaisesRegex(ValueError, "snapshot_digest"):
            study.validate_snapshot(s, raw["seed"], raw["base_sha256"], 0)

    def test_durable_atomic_write_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            sha = study.durable_write(p, {"cursor": 7, "value": [1, 2]})
            self.assertEqual(sha, __import__("hashlib").sha256(p.read_bytes()).hexdigest())
            self.assertEqual(list(Path(d).iterdir()), [p])

    def test_schedule_observes_only_revealed_support(self):
        order, schedule = study.schedule_for_seed(study.SEEDS[0])
        self.assertEqual(len(order), study.N_SUPPORT)
        self.assertEqual(len(schedule), study.N_SUPPORT)
        self.assertEqual(schedule[-1]["seen"], list(order))
        for cursor, entry in enumerate(schedule):
            self.assertEqual(entry["seen"], list(order[:cursor + 1]))
            self.assertEqual(entry["batches"], [[entry["row"]] for _ in range(study.UPDATES)])

    def test_trainer_input_contains_no_target_labels(self):
        raw = study.make_data(study.SEEDS[0])
        self.assertNotIn("y_support", raw)
        self.assertNotIn("y_eval", raw)
        for cursor, entry in enumerate(raw["schedule"]):
            self.assertEqual(entry["seen"], [e["row"] for e in raw["schedule"][:cursor + 1]])
            self.assertEqual(entry["batches"], [[entry["row"]] for _ in range(study.UPDATES)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
