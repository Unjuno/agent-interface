from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


def dataset_fixture() -> dict:
    shared_positive = [1, 0, 1, 0, 1, 0, 1, 0]
    shared_zero = [0, 1, 0, 1, 0, 1, 0, 1]
    a_only = [1, 1, 1, 1, 0, 0, 0, 0]
    b_only = [0, 0, 0, 0, 1, 1, 1, 1]
    rows = lambda role, split, vectors: [
        {"id": f"{role}:{split}:{i}", "role": role,
         "split": split, "features": vector,
         "label": 0 if role == "A" else vector[0]}
        for i, vector in enumerate(vectors)
    ]
    return {
        "schema": "fixture",
        "seeds": [{
            "seed": 71,
            "splits": {
                "a_support": rows("A", "a_support", [shared_positive, shared_zero, a_only]),
                "b_arrival": rows("B", "b_arrival", [shared_positive, shared_zero, b_only]),
            },
        }],
    }


class ProbeContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dataset_path = self.root / "dataset.json"
        self.raw_path = self.root / "raw.json"
        self.dataset = dataset_fixture()
        self.dataset_bytes = (json.dumps(self.dataset, sort_keys=True,
                                         separators=(",", ":")) + "\n").encode()
        self.dataset_path.write_bytes(self.dataset_bytes)
        self.packet = candidate.build(
            self.dataset, hashlib.sha256(self.dataset_bytes).hexdigest())
        self.raw_path.write_bytes(candidate.canonical(self.packet))

    def tearDown(self):
        self.temp.cleanup()

    def test_builder_selects_shared_contradictory_vector(self):
        probe = self.packet["seeds"][0]
        self.assertEqual(probe["features"], [1, 0, 1, 0, 1, 0, 1, 0])
        self.assertEqual((probe["a_label"], probe["b_label"]), (0, 1))
        self.assertEqual(probe["cross_role_overlap_count"], 2)

    def test_frozen_issue_dataset_yields_corrected_contradictory_probes(self):
        package = Path(__file__).resolve().parents[2]
        source = (package / "system1" /
                  "needle_role_context_online_lora_6321_v1_20261002" /
                  "construction-01" / "dataset.json")
        frozen_data, digest = candidate.load(source)
        packet = candidate.build(frozen_data, digest)
        self.assertEqual(digest, candidate.EXPECTED_DATASET_SHA256)
        self.assertEqual(len(packet["seeds"]), 3)
        for probe in packet["seeds"]:
            self.assertEqual(probe["a_label"], 0)
            self.assertEqual(probe["b_label"], 1)
            self.assertEqual(probe["features"][0], 1)
            self.assertGreater(probe["cross_role_overlap_count"], 0)

    def test_independent_raw_auditor_accepts_valid_packet(self):
        result = audit.audit(
            self.dataset_path, self.raw_path,
            hashlib.sha256(self.dataset_bytes).hexdigest())
        self.assertEqual(result["status"], "PASS_PROBE_CONTRACT_SCOPED")
        self.assertEqual(result["errors"], [])

    def test_zero_vector_equal_label_probe_is_rejected(self):
        self.packet["seeds"][0].update({
            "features": [0, 1, 0, 1, 0, 1, 0, 1],
            "a_label": 0,
            "b_label": 0,
        })
        self.raw_path.write_bytes(candidate.canonical(self.packet))
        result = audit.audit(
            self.dataset_path, self.raw_path,
            hashlib.sha256(self.dataset_bytes).hexdigest())
        self.assertIn("71:probe_not_contradictory_input", result["errors"])
        self.assertIn("71:labels_not_contradictory", result["errors"])

    def test_nonshared_vector_is_rejected(self):
        self.packet["seeds"][0]["features"] = [1, 1, 1, 1, 0, 0, 0, 0]
        self.raw_path.write_bytes(candidate.canonical(self.packet))
        result = audit.audit(
            self.dataset_path, self.raw_path,
            hashlib.sha256(self.dataset_bytes).hexdigest())
        self.assertIn("71:probe_not_shared", result["errors"])

    def test_mutated_target_is_rejected(self):
        self.packet["seeds"][0]["b_label"] = 0
        self.raw_path.write_bytes(candidate.canonical(self.packet))
        result = audit.audit(
            self.dataset_path, self.raw_path,
            hashlib.sha256(self.dataset_bytes).hexdigest())
        self.assertIn("71:target_formula", result["errors"])

    def test_wrong_frozen_dataset_digest_is_rejected(self):
        result = audit.audit(self.dataset_path, self.raw_path, "0" * 64)
        self.assertIn("dataset_digest", result["errors"])

    def test_missing_seed_is_rejected(self):
        self.packet["seeds"] = []
        self.raw_path.write_bytes(candidate.canonical(self.packet))
        result = audit.audit(
            self.dataset_path, self.raw_path,
            hashlib.sha256(self.dataset_bytes).hexdigest())
        self.assertIn("seed_coverage_or_order", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
