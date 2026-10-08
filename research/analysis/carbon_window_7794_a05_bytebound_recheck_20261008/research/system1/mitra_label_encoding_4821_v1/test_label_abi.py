import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from label_abi import encode_labels, restore_probability_columns
from autogluon.tabular.models.mitra._internal.data.dataset_split import make_stratified_dataset_split


class LabelAbiTests(unittest.TestCase):
    def test_frozen_support_labels_split_as_contiguous_int64(self):
        support_path = Path("/inputs/support.csv")
        digest = hashlib.sha256(support_path.read_bytes()).hexdigest()
        self.assertEqual(digest, "bf4d64cf826ea2d727990bd799d7e6d0f813a97a64119751e05d22a819fdf785")
        support = pd.read_csv(support_path)
        labels = support["label"].astype(str).to_numpy()
        expected = ("C0", "C1", "C2", "C3", "C4", "C5")
        encoded, vocabulary = encode_labels(labels, expected)
        self.assertEqual(vocabulary, expected)
        self.assertEqual(encoded.dtype, np.dtype("int64"))
        self.assertEqual(sorted(np.unique(encoded).tolist()), list(range(6)))
        split = make_stratified_dataset_split(
            support[[f"f{i}" for i in range(8)]].to_numpy(dtype=np.float32), encoded, seed=853
        )
        self.assertEqual([len(part) for part in split], [204, 52, 204, 52])
        self.assertEqual(sorted(np.unique(np.concatenate((split[2], split[3]))).tolist()), list(range(6)))
        Path("/out/DIAGNOSTIC_RESULT.json").write_text(json.dumps({
            "schema": "issue-4821-label-abi-construction-v1",
            "support_sha256": digest,
            "support_rows": len(support), "vocabulary": list(vocabulary),
            "encoded_dtype": str(encoded.dtype), "encoded_ids": sorted(np.unique(encoded).tolist()),
            "split_sizes": [len(part) for part in split], "split_ids": sorted(np.unique(np.concatenate((split[2], split[3]))).tolist()),
            "model_loaded": False, "gpu_requested": False,
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    def test_encoding_is_deterministic_and_rejects_vocabulary_drift(self):
        labels = ["C5", "C1", "C5", "C1"]
        a, vocab_a = encode_labels(labels)
        b, vocab_b = encode_labels(labels)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(vocab_a, vocab_b)
        with self.assertRaises(ValueError):
            encode_labels(labels, ("C1", "C2", "C5"))

    def test_probability_columns_are_explicitly_reordered(self):
        vocabulary = ("C0", "C1", "C2")
        model_columns = np.array([[0.2, 0.5, 0.3]])  # ordered by class IDs [2, 0, 1]
        restored = restore_probability_columns(model_columns, [2, 0, 1], vocabulary)
        np.testing.assert_allclose(restored, [[0.5, 0.3, 0.2]])

    def test_probability_column_binding_rejects_missing_duplicate_or_bad_rows(self):
        with self.assertRaises(ValueError):
            restore_probability_columns(np.array([[1.0, 0.0]]), [0, 0], ("C0", "C1"))
        with self.assertRaises(ValueError):
            restore_probability_columns(np.array([[0.3, 0.3]]), [0, 1], ("C0", "C1"))
        with self.assertRaises(ValueError):
            restore_probability_columns(np.array([[np.nan, 0.0]]), [0, 1], ("C0", "C1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
