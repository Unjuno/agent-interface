import copy
import json
import unittest
from pathlib import Path

import audit_hardened
import candidate
import runner


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(Path("/input/RAW.json").read_text(encoding="utf-8"))

    def test_unchanged_baseline_reconstructs(self):
        result = audit_hardened.audit_document(self.raw)
        self.assertEqual((result["rows"], result["distributions"]), (336, 21))

    def test_python_equality_canary_is_rejected_by_type_gate(self):
        mutated = copy.deepcopy(self.raw)
        runner.set_path(mutated, ("cost", "A"), True)
        with self.assertRaises(candidate.TypeShapeReject):
            candidate.audit_document(mutated, self.raw, audit_hardened)

    def test_exact_shape_accepts_original(self):
        candidate.require_same_json_types(self.raw, self.raw)

    def test_boolean_is_not_an_integer_or_float(self):
        for replacement, reference in ((True, 1), (False, 0.0), (1, True)):
            with self.subTest(replacement=replacement, reference=reference):
                with self.assertRaises(candidate.TypeShapeReject):
                    candidate.require_same_json_types(replacement, reference)


if __name__ == "__main__":
    unittest.main(verbosity=2)
