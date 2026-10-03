"""Real copied-file regressions for post-run custody review; no formal replay."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "exogenous_opportunity_5694_matched_phase_a04_20261002"


def module(name):
    spec = importlib.util.spec_from_file_location("review_" + name, ROOT / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class ReviewTests(unittest.TestCase):
    def rejection(self, filename, change):
        # Actual copies: only module's data-root pointer is substituted, no fake oracle.
        with tempfile.TemporaryDirectory(prefix=".phase-review-", dir=ROOT.parent) as temporary:
            parent = Path(temporary)
            data = parent / ROOT.name
            shutil.copytree(ROOT, data, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(OLD, parent / OLD.name, ignore=shutil.ignore_patterns("__pycache__"))
            path = data / filename
            value = json.loads(path.read_text())
            change(value)
            path.write_text(json.dumps(value))
            verifier = module("verify_evidence")
            with patch.object(verifier, "ROOT", data), self.assertRaises(ValueError):
                verifier.verify(check_manifest=False)

    def test_unchanged_evidence_still_passes(self):
        self.assertEqual(module("verify_evidence").verify(check_manifest=False)["metrics"]["rows_checked"], 147)

    def test_rehashed_post_freeze_amendment_is_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix=".phase-review-", dir=ROOT.parent) as temporary:
            parent = Path(temporary)
            data = parent / ROOT.name
            shutil.copytree(ROOT, data, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(OLD, parent / OLD.name, ignore=shutil.ignore_patterns("__pycache__"))
            text = (data / "PREREGISTRATION_02.md").read_text().replace("512MiB", "1GiB")
            (data / "PREREGISTRATION_02.md").write_text(text)
            frozen = json.loads((data / "FREEZE_02.json").read_text())
            frozen["source_sha256"]["PREREGISTRATION_02.md"] = hashlib.sha256(text.encode()).hexdigest()
            (data / "FREEZE_02.json").write_text(json.dumps(frozen))
            verifier = module("verify_evidence")
            with patch.object(verifier, "ROOT", data), self.assertRaises(ValueError):
                verifier.verify(check_manifest=False)

    def test_extra_candidate_source_is_rejected(self):
        self.rejection("STAGING_02.json", lambda r: r["custody"]["candidate"]["contains_only"].append("audit.py"))

    def test_wrong_staged_digest_is_rejected(self):
        def change(r):
            r["custody"]["candidate"]["sha256sum"] = "0" * 64 + r["custody"]["candidate"]["sha256sum"][64:]
        self.rejection("STAGING_02.json", change)

    def test_forged_run_summary_is_rejected(self):
        def change(r):
            r["metrics"]["rows_checked"] = 999
            r["live_effect_events"] = 1
        self.rejection("RUN.json", change)

    def test_wrong_consumed_allocation_is_rejected(self):
        self.rejection("formal_02/CONSUMED.json", lambda r: r.__setitem__("allocation", "unrelated-allocation"))

    def test_receipt_finish_before_start_is_rejected(self):
        self.rejection("formal_02/candidate.receipt.json", lambda r: r.__setitem__("finished_at_utc", "2026-10-03T09:00:00Z"))

    def test_genuine_integer_boolean_equality_alias_is_rejected(self):
        fixture = json.loads((ROOT / "fixture.json").read_text())
        raw = json.loads((ROOT / "formal_02/candidate/raw.json").read_text())
        altered = copy.deepcopy(raw)
        self.assertEqual(altered["rows"][1]["opportunity"]["onset_ms"], 1)
        altered["rows"][1]["opportunity"]["onset_ms"] = True
        self.assertEqual(raw, altered)  # Ordinary equality cannot detect this exact alias.
        self.assertTrue(module("audit").errors(fixture, altered))


if __name__ == "__main__":
    unittest.main()
