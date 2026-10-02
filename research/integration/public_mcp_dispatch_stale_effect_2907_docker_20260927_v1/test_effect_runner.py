import os
import unittest

os.environ.setdefault("SOURCE_COMMIT", "construction-only")
os.environ.setdefault("EXPERIMENT_IMAGE_ID", "construction-only")

import runner_effect


class ProgramFreezeTests(unittest.TestCase):
    def test_program_binds_observation_and_revision_and_ends_released(self):
        row = runner_effect.program(
            "test-program", 7, 3,
            [{"op": "focus", "target": "chromium"},
             {"op": "key_chord", "keys": ["F6"]}])
        self.assertEqual(row["source"], {"observation_seq": 7, "binding_revision": 3})
        self.assertIs(row["terminal"]["release_all_required"], True)
        self.assertEqual(row["ops"][-1], {"op": "release_all"})
        self.assertEqual(sum(op["op"] == "release_all" for op in row["ops"]), 1)

    def test_stale_control_changes_only_source_sequence(self):
        stale = runner_effect.program("stale", 4, 2, [{"op": "key_chord", "keys": ["F6"]}])
        current = runner_effect.program("current", 5, 2, [{"op": "key_chord", "keys": ["F6"]}])
        self.assertEqual(stale["ops"], current["ops"])
        self.assertEqual(stale["source"]["binding_revision"], current["source"]["binding_revision"])
        self.assertEqual(stale["source"]["observation_seq"] + 1, current["source"]["observation_seq"])


if __name__ == "__main__":
    unittest.main()
