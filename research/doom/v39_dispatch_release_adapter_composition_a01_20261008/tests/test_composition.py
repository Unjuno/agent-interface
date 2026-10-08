import copy
import json
import unittest
from pathlib import Path

from audit import validate_result


HERE = Path(__file__).resolve().parents[1]


class CompositionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        cls.result_path = HERE / "outputs/official-a02/normal/result.json"
        cls.manifest_path = HERE / "outputs/official-a02/normal/sources.json"
        cls.result = json.loads(cls.result_path.read_text(encoding="utf-8"))
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))
        cls.snapshot = HERE / "outputs/official-a02/normal/source_snapshot"

    def test_every_candidate_input_is_vendored_and_hash_pinned(self):
        import hashlib
        for relpath, expected in self.freeze["candidate_inputs"].items():
            path = HERE / "candidate_inputs" / relpath
            self.assertTrue(path.is_file(), relpath)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relpath)

    def test_mutated_candidate_input_identity_is_rejected(self):
        result = copy.deepcopy(self.result)
        candidate_path = next(iter(self.freeze["candidate_inputs"]))
        result["source_identities"][candidate_path] = "0" * 64
        with self.assertRaisesRegex(ValueError, "candidate input identity mismatch"):
            validate_result(result, self.manifest, self.freeze, self.snapshot)

    def test_full_dispatch_manifest_producer_adapter_composition(self):
        receipt = validate_result(self.result, self.manifest, self.freeze, self.snapshot)
        self.assertEqual(receipt["status"], "PASS_SOURCE_BOUND_COMPOSITION")

    def test_selected_route_mutation_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["selected_command"]["report_label"] = "v12_default"
        with self.assertRaisesRegex(ValueError, "measurement dispatch"):
            validate_result(result, self.manifest, self.freeze, self.snapshot)

    def test_manifest_source_mutation_is_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        key = self.freeze["per_key_source_manifest_keys"][0].replace("/", "\\")
        manifest[key] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source manifest hash mismatch"):
            validate_result(self.result, manifest, self.freeze, self.snapshot)

    def test_missing_row_cannot_be_promoted(self):
        result = copy.deepcopy(self.result)
        result["release_to_feedback_adapter"]["before_accept_failure"]["visible_rows"] = 2
        with self.assertRaisesRegex(ValueError, "pre-accept"):
            validate_result(result, self.manifest, self.freeze, self.snapshot)

    def test_ambiguous_ack_cannot_become_causal(self):
        result = copy.deepcopy(self.result)
        result["release_to_feedback_adapter"]["after_accept_failure"]["causal_attribution"] = "ESTABLISHED"
        with self.assertRaisesRegex(ValueError, "post-accept"):
            validate_result(result, self.manifest, self.freeze, self.snapshot)


if __name__ == "__main__":
    unittest.main()
