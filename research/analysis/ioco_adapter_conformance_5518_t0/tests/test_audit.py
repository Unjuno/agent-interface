import unittest
import json
import hashlib
import tempfile
from pathlib import Path

from audit import audit_document, evaluate_independently, verify_source_manifest
from tests.test_corpus import FrozenCorpusConstructionTests


class IndependentOracleTests(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "initial": "READY",
            "transitions": [
                {"from": "READY", "input": {"type": "OBSERVE"}, "to": "FRESH",
                 "allowed_outputs": [{"type": "OBSERVED", "generation": 1, "target": "A"}]},
                {"from": "FRESH", "input": {"type": "ADMIT", "target": "A"}, "to": "ADMITTED",
                 "allowed_outputs": [{"type": "ADMITTED", "target": "A"}]},
            ],
        }

    def test_independent_oracle_finds_first_forbidden_target(self):
        trace = [
            {"input": {"type": "OBSERVE"},
             "outputs": [{"type": "OBSERVED", "generation": 1, "target": "A"}],
             "internal": ["HIDDEN_CACHE"]},
            {"input": {"type": "ADMIT", "target": "A"},
             "outputs": [{"type": "ADMITTED", "target": "B"}], "internal": []},
        ]
        result = evaluate_independently(self.spec, trace)
        self.assertEqual(result["status"], "NONCONFORMANT")
        self.assertEqual(result["counterexample"]["prefix_length"], 2)

    def test_independent_oracle_does_not_promote_missing_output(self):
        trace = [{"input": {"type": "OBSERVE"}, "outputs": [], "internal": []}]
        result = evaluate_independently(self.spec, trace)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "MISSING_OUTPUT_NOT_QUIESCENCE")

    def test_independent_source_manifest_check_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.py"
            path.write_bytes(b"frozen bytes")
            digest = hashlib.sha256(b"frozen bytes").hexdigest()
            freeze = {"frozen_sources": {"source.py"