"""Pre-freeze builder/auditor construction and hostile-mutation controls."""
import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate

ROOT = Path(__file__).parent
MODEL_BYTES = (ROOT / "model.json").read_bytes()
MODEL = json.loads(MODEL_BYTES)


def raw_fixture():
    raw = candidate.build(copy.deepcopy(MODEL))
    import hashlib
    raw["model_file_sha256"] = hashlib.sha256(MODEL_BYTES).hexdigest()
    return raw


class ScheduleFixtureTests(unittest.TestCase):
    def test_valid_four_arm_schedule(self):
        self.assertEqual(auditor.audit(raw_fixture()), [])

    def test_missing_rare_exception_rejected(self):
        raw = raw_fixture()
        states = raw["checkpoint_histories"]["per_episode"]
        states[2]["derived_memory"] = []
        self.assertTrue(auditor.audit(raw))

    def test_missing_source_provenance_rejected(self):
        raw = raw_fixture()
        claim = next(c for c in raw["checkpoint_histories"]["per_episode"][2]["derived_memory"] if c["id"] == "rare_publish_exception")
        claim["source_ids"] = []
        self.assertTrue(auditor.audit(raw))

    def test_conflict_silently_resolved_rejected(self):
        raw = raw_fixture()
        claim = next(c for c in raw["checkpoint_histories"]["per_episode"][4]["derived_memory"] if c["id"] == "revision_r7_mode")
        claim["value"] = "published"
        self.assertTrue(auditor.audit(raw))

    def test_episode_mutation_rejected(self):
        raw = raw_fixture()
        raw["episodes"][0]["exact_effect"] = "publish"
        self.assertTrue(auditor.audit(raw))

    def test_checkpoint_misalignment_rejected(self):
        raw = raw_fixture()
        raw["checkpoint_histories"]["batch_2"][2]["checkpoint"] = 4
        self.assertTrue(auditor.audit(raw))

    def test_heldout_conjunction_inference_rejected(self):
        raw = raw_fixture()
        raw["checkpoint_histories"]["terminal"][-1]["derived_memory"].append({"id":"heldout_conjunction"})
        self.assertTrue(auditor.audit(raw))

    def test_query_budget_change_rejected(self):
        raw = raw_fixture()
        raw["checkpoint_histories"]["terminal"][-1]["query_budget"]["model_calls"] = 1
        self.assertTrue(auditor.audit(raw))


if __name__ == "__main__":
    unittest.main()
