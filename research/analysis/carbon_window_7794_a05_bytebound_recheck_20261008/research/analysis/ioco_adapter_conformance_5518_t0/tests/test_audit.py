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
            freeze = {"frozen_sources": {"source.py": digest}}
            self.assertEqual(verify_source_manifest(freeze, {"source.py": digest}, root), [])
            path.write_bytes(b"changed bytes")
            errors = verify_source_manifest(freeze, {"source.py": digest}, root)
            self.assertEqual(errors, ["source_hash:source.py"])

    def test_audit_uses_supplied_root_for_freeze_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "FREEZE.json").write_text("{}", encoding="utf-8")
            freeze = {"allocation_id": "test", "base_main_sha": "b" * 40,
                      "frozen_sources": {}}
            raw = {"results": [], "source_sha256": {}, "allocation_id": "test",
                   "source_base_main_sha": "b" * 40, "source_commit_sha": "a" * 40,
                   "frozen_sources_verified": True,
                   "freeze_sha256": hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest()}
            spec = json.loads((Path(__file__).resolve().parents[1] / "spec.json").read_text())
            corpus = json.loads((Path(__file__).resolve().parents[1] / "cases.json").read_text())
            from audit import EXPECTED
            rows = []
            for case in corpus["cases"]:
                decision = evaluate_independently(spec, case["trace"])
                self.assertEqual(decision["status"], EXPECTED[case["case_id"]])
                rows.append({"case_id": case["case_id"], "implementation": case["implementation"],
                             "result": decision})
            direct = corpus["cases"][0]["trace"]
            hidden = corpus["cases"][1]["trace"]
            project = lambda trace: [{"input": x["input"], "outputs": x["outputs"]} for x in trace]
            raw.update(results=rows, baseline={
                "compared": ["reference-direct", "reference-hidden-batch-retry"],
                "exact_raw_trace_equal": direct == hidden,
                "agent_visible_io_equal": project(direct) == project(hidden),
            })
            result = audit_document(spec, corpus, raw, freeze, root=root)
            self.assertNotIn("freeze_sha256", result["errors"])


if __name__ == "__main__":
    unittest.main()
