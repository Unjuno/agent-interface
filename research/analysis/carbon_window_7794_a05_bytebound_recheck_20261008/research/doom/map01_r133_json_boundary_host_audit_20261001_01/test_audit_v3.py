from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

import audit_v2
import audit_v3

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "construction-01"


class AuditV3PreflightTests(unittest.TestCase):
    def test_full_audit_orchestration_on_immutable_raw(self):
        result = audit_v3.run_audit()
        self.assertEqual(result["status"], "PASS_HOST_JSON_BOUNDARY_AUDIT_V3")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["case_count"], 9)
        self.assertTrue(all(x["rejected"] for x in result["mutation_results"].values()))

    def test_v1_acceptance_of_resealed_collateral_edit_is_reproduced(self):
        spec = importlib.util.spec_from_file_location("audit_v1_preflight", HERE / "audit.py")
        legacy = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(legacy)
        raw = json.loads((OUT / "RAW.json").read_text(encoding="utf-8"))
        run = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
        freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
        item = raw["cases"][1]
        item["parsed_rows"][0]["health_loss"] = 1
        item["wire_json"] = audit_v2.canonical(item["parsed_rows"])
        raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
        run["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
        self.assertEqual(legacy.audit_payload(raw, run, freeze, raw_bytes), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
