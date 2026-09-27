from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

import run_probe


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))


class ProbeInputTests(unittest.TestCase):
    def test_exact_source_and_transport_identities(self):
        _, _, raw_bytes, raw, identities = run_probe.load_inputs(ROOT)
        self.assertEqual(identities["source_git_blob_expected"], "1a6cc0e46b32d4cd6989aed118d003cce4cfe399")
        self.assertEqual(identities["transport_git_blob_expected"], "c38dd2002f201d49b6fc261caff019550a4bf4bc")
        self.assertEqual(len(raw_bytes), 186739)
        self.assertEqual(identities["raw_sha256"], "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d")
        self.assertEqual((len(raw["distributions"]), sum(len(d["rows"]) for d in raw["distributions"])), (21, 336))

    def test_crlf_wrapped_base64_is_decoded_without_touching_input(self):
        original = (ROOT / run_probe.TRANSPORT_RELATIVE).read_bytes()
        encoded = b"".join(original.split())
        payload = base64.b64decode(encoded, validate=True)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(archive.namelist(), ["RAW.json", "AUDIT.json"])
            self.assertEqual(hashlib.sha256(archive.read("RAW.json")).hexdigest(), run_probe.RAW_SHA256)
        self.assertEqual((ROOT / run_probe.TRANSPORT_RELATIVE).read_bytes(), original)

    def test_mutations_are_independent_copies(self):
        _, _, _, original, _ = run_probe.load_inputs(ROOT)
        weight = copy.deepcopy(original)
        weight["distributions"][0]["rows"][0]["weight"] = float("nan")
        alpha = copy.deepcopy(original)
        alpha["development_alpha"] = 0.5
        count = copy.deepcopy(original)
        count["truth_state_count"] = 99
        self.assertTrue(original["distributions"][0]["rows"][0]["weight"] == 0.0)
        self.assertEqual(original["development_alpha"], 0.0)
        self.assertEqual(original["truth_state_count"], 16)
        self.assertTrue(weight["distributions"][0]["rows"][0]["weight"] != weight["distributions"][0]["rows"][0]["weight"])
        self.assertEqual(alpha["development_alpha"], 0.5)
        self.assertEqual(count["truth_state_count"], 99)


if __name__ == "__main__":
    unittest.main(verbosity=2)
