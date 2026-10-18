import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("schedule_a02_audit", Path(__file__).with_name("audit.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditContract(unittest.TestCase):
    def test_reconstruction_matches_retained_raw(self):
        import json
        fixture = json.loads(audit.FIXTURE_PATH.read_bytes())
        raw = json.loads(audit.RAW_PATH.read_bytes())
        self.assertEqual(audit.reconstruct(fixture), raw)

    def test_all_five_hostile_mutations_change_raw(self):
        import json
        fixture = json.loads(audit.FIXTURE_PATH.read_bytes())
        raw = json.loads(audit.RAW_PATH.read_bytes())
        self.assertEqual(sum(audit.hostile_controls(raw, audit.reconstruct(fixture)).values()), 5)

    def test_schedule_shape_and_counts(self):
        import json
        raw = json.loads(audit.RAW_PATH.read_bytes())
        expected = {"episodic_only": (0, 16), "per_episode": (12, 16),
                    "batch_4": (3, 16), "terminal": (1, 16)}
        actual = {arm: (len(raw["schedules"][arm]["updates"]),
                        len(raw["schedules"][arm]["query_visibility"]))
                  for arm in audit.ARMS}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
