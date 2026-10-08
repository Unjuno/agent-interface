import json
from pathlib import Path
import unittest

from audit_raw import check, mutations

ROOT = Path(__file__).resolve().parents[3]


class CorrectedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((ROOT / "research/integration/broker_fake_child_boundary_4485_orbstack_successor_v1"
                                  / "formal01/RESULT.json").read_text(encoding="utf-8"))

    def test_original_matrix_passes_semantic_contract(self):
        self.assertEqual(check(self.payload), [])

    def test_all_eight_corruption_controls_are_rejected(self):
        controls = {name: bool(check(mutant)) for name, mutant in mutations(self.payload)}
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(controls.values()), controls)

    def test_freeze_broker_digest_is_nested(self):
        freeze = json.loads((ROOT / "research/integration/broker_fake_child_boundary_4485_orbstack_audit_successor_v1"
                             / "parent_FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(freeze["target_source"]["sha256"], "e44822269b921aa6327563b27e48a6d8ef4ebe35a182f50de541cf66fce6199c")


if __name__ == "__main__":
    unittest.main()
