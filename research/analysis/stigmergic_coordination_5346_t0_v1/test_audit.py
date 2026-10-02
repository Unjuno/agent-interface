import copy
import unittest

from audit import validate
from candidate import run_all


class RawAuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.raw = run_all()

    def test_clean_raw_is_accepted(self):
        self.assertEqual(validate(self.raw), [])

    def test_marker_authority_mutation_rejected(self):
        bad = copy.deepcopy(self.raw)
        cell = next(c for c in bad["cells"] if c["scenario"] == "forged_marker"
                    and c["policy"] == "LOCAL_MARKERS")
        cell["events"].append({"tick": 2, "kind": "LEASE_GRANTED", "worker": 1,
                               "target": "A", "basis": "marker"})
        self.assertTrue(any("non-authoritative" in e for e in validate(bad)))

    def test_missing_cell_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["cells"].pop()
        self.assertIn("cell identity/uniqueness mismatch", validate(bad))

    def test_completion_mutation_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["cells"][0]["completion_count"] = 1
        self.assertTrue(any("completion" in e for e in validate(bad)))

    def test_collision_mutation_rejected(self):
        bad = copy.deepcopy(self.raw)
        cell = next(c for c in bad["cells"] if c["scenario"] == "visible_contention"
                    and c["policy"] == "NO_COORDINATION")
        cell["collision_retries"] = 0
        self.assertTrue(any("collision" in e for e in validate(bad)))

    def test_forged_admission_basis_mutation_rejected(self):
        bad = copy.deepcopy(self.raw)
        cell = next(c for c in bad["cells"] if c["scenario"] == "visible_contention"
                    and c["policy"] == "LOCAL_MARKERS")
        next(e for e in cell["events"] if e["kind"] == "LEASE_GRANTED")["basis"] = "marker"
        self.assertTrue(any("non-authoritative" in e for e in validate(bad)))


if __name__ == "__main__":
    unittest.main()
