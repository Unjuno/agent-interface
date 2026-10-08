"""Independent support audit and false-suggestion mutation tests."""

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ResumeSuggestionAuditTests(unittest.TestCase):
    def test_auditor_reconstructs_support_and_rejects_six_false_certificates(self):
        self.assertIsNotNone(importlib.util.find_spec("candidate"), "candidate.py is not implemented")
        self.assertIsNotNone(importlib.util.find_spec("auditor"), "auditor.py is not implemented")
        import auditor
        import candidate

        fixture = json.loads((ROOT / "input.json").read_text(encoding="utf-8"))
        truth = json.loads((ROOT / "truth.json").read_text(encoding="utf-8"))
        result = candidate.run(fixture)
        audit = auditor.audit(fixture, result, truth)
        self.assertEqual("PASS_METHOD_SCOPED", audit["disposition"])
        self.assertEqual(0, audit["reconstruction_errors"])
        self.assertEqual(6, audit["mutation_controls_rejected"])

        mutations = []
        invented = copy.deepcopy(result)
        row = next(row for row in invented["rows"] if row["case_id"] == "ambiguous_alternatives")
        row["suggestion"] = {"checkpoint_id": "hidden_winner", "source_ids": ["source-1"]}
        mutations.append(invented)

        stale = copy.deepcopy(result)
        row = next(row for row in stale["rows"] if row["case_id"] == "stale_state")
        row["suggestion"] = {"checkpoint_id": "open", "source_ids": ["source-1"]}
        mutations.append(stale)

        wrong_source = copy.deepcopy(result)
        row = next(row for row in wrong_source["rows"] if row["case_id"] == "unique_initial")
        row["suggestion"]["source_ids"] = ["unrelated-source"]
        mutations.append(wrong_source)

        authority = copy.deepcopy(result)
        authority["rows"][0]["authority"] = "continue_task"
        mutations.append(authority)

        freshness_promise = copy.deepcopy(result)
        freshness_promise["rows"][0]["freshness"] = "guaranteed_current"
        mutations.append(freshness_promise)

        hidden_label_leak = copy.deepcopy(result)
        hidden_label_leak["rows"][0]["hidden_label"] = truth["rows"][0]["hidden_label"]
        mutations.append(hidden_label_leak)

        for mutated in mutations:
            with self.assertRaises(ValueError):
                auditor.audit(fixture, mutated, truth)


if __name__ == "__main__":
    unittest.main()
