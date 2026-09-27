from __future__ import annotations

import json
import unittest
from pathlib import Path

import audit


class RawAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = Path(__file__).parent
        cls.repo = cls.package
        cls.rows = [json.loads(x) for x in (cls.package / "events.jsonl").read_text().splitlines()]
        cls.manifest = json.loads((cls.package / "SOURCE_MANIFEST.json").read_text())
        cls.runner_sources = json.loads((cls.package / "sources.json").read_text())

    def test_retained_result_passes_audit(self):
        self.assertEqual([], audit.audit(self.repo, package_override=self.package))

    def test_ready_identity_mutation_is_rejected(self):
        rows = [dict(x) for x in self.rows]
        rows[0]["app"] = "xterm"
        self.assertIn("ready identity", " ".join(audit.audit(self.repo, package_override=self.package, rows_override=rows)))

    def test_public_endpoint_mutation_is_rejected(self):
        rows = [dict(x) for x in self.rows]
        rows[0]["goal"] = dict(rows[0]["goal"])
        rows[0]["goal"]["url"] = "https://example.invalid/"
        self.assertIn("ready identity", " ".join(audit.audit(self.repo, package_override=self.package, rows_override=rows)))

    def test_submit_mutation_is_rejected(self):
        rows = [dict(x) for x in self.rows]
        rows[2]["command"] = {"op": "submit", "steps": [{"op": "text", "text": "x"}]}
        self.assertIn("non-finish command", " ".join(audit.audit(self.repo, package_override=self.package, rows_override=rows)))

    def test_source_digest_mutation_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        first = next(iter(manifest["files"].values()))
        first["sha256"] = "0" * 64
        self.assertIn("source sha256 mismatch", " ".join(
            audit.audit(self.repo, package_override=self.package, manifest_override=manifest)))

    def test_input_event_mutation_is_rejected(self):
        rows = [dict(x) for x in self.rows]
        rows.append({"event": "input_admission", "key": "Return"})
        errors = audit.audit(self.repo, package_override=self.package, rows_override=rows)
        self.assertIn("event sequence/cardinality mismatch", " ".join(errors))
        self.assertIn("input/action event present", " ".join(errors))

    def test_no_gui_import_only_record_passes(self):
        self.assertEqual([], audit.audit(self.repo, package_override=self.package))

    def test_no_gui_nonzero_exit_mutation_is_rejected(self):
        result = json.loads((self.package / "NO_GUI_IMPORT_RESULT.json").read_text())
        result["exit_code"] = 1
        errors = audit.audit(self.repo, package_override=self.package,
                             no_gui_result_override=result)
        self.assertIn("no-GUI import-only result contract mismatch", " ".join(errors))

    def test_direct_xvfb_ready_bundle_passes(self):
        self.assertEqual([], audit.audit(self.repo, package_override=self.package))

    def test_direct_xvfb_intervention_mutation_is_rejected(self):
        path = self.package / "READY_GATE_03_RESULT.json"
        result = json.loads(path.read_text())
        result["manual_ready_signal_interventions"] = 1
        errors = audit.audit(self.repo, package_override=self.package,
                             ready_result_override=result)
        self.assertIn("direct-Xvfb result contract mismatch", " ".join(errors))

    def test_host_get_component_result_passes(self):
        self.assertEqual([], audit.audit(self.repo, package_override=self.package))

    def test_host_get_post_mutation_claim_is_rejected(self):
        path = self.package / "FIXTURE_GET_HOST_RESULT.json"
        result = json.loads(path.read_text())
        result["output_path_exists_after"] = True
        errors = audit.audit(self.repo, package_override=self.package,
                             fixture_result_override=result)
        self.assertIn("host GET component result scope mismatch", " ".join(errors))


if __name__ == "__main__":
    unittest.main()
