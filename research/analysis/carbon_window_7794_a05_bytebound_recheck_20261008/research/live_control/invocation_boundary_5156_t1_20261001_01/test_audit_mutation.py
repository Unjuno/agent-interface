import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from audit import main


ROOT = Path(__file__).resolve().parent


class MutationControlTests(unittest.TestCase):
    def test_frozen_positive_row_is_actually_mutated_and_all_controls_reject(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "AUDIT.json"
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(str(ROOT / "inputs.json"),
                                 str(ROOT / "results" / "raw.jsonl"),
                                 str(output))
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0, result)
        self.assertEqual(result["decision"], "PASS_INVOCATION_BOUNDARY_AUDIT")
        self.assertEqual(result["mutation_controls_rejected"], 6)
        self.assertEqual(result["mutation_controls_total"], 6)
        self.assertEqual(result["positive_row_mutation"], {
            "from": "PASS_INVOCATION_BOUNDARY_CONTRACT",
            "to": "STOP_INVOCATION_PROVENANCE_OR_BOUNDARY",
            "changed_from_pristine": True,
            "rejected_by_reconstruction": True,
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
