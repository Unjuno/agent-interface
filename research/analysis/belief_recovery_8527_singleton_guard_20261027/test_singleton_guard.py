import copy
import json
import hashlib
import importlib.util
from pathlib import Path
import unittest

from singleton_guard import audit_with_guard, validate_singleton_controls

DIAGNOSTIC = Path(__file__).resolve().parent.parent / "belief_recovery_8527_singleton_diagnostic_20261027"
FIXTURE = json.loads((DIAGNOSTIC / "fixture.json").read_text(encoding="utf-8"))
ORIGINAL = json.loads((DIAGNOSTIC / "original_construction.json").read_text(encoding="utf-8"))
DUPLICATE = json.loads((DIAGNOSTIC / "duplicate_singleton.json").read_text(encoding="utf-8"))


class SingletonCoverageTests(unittest.TestCase):
    def test_original_and_reordered_controls_are_accepted(self):
        self.assertIsNone(validate_singleton_controls(FIXTURE, ORIGINAL))
        reordered = copy.deepcopy(ORIGINAL)
        reordered["singleton_controls"].reverse()
        self.assertIsNone(validate_singleton_controls(FIXTURE, reordered))

    def test_recorded_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_singleton_controls(FIXTURE, DUPLICATE)

    def test_omitted_extra_and_undeclared_controls_are_rejected(self):
        for change in ("omitted", "extra", "substituted", "malformed"):
            raw = copy.deepcopy(ORIGINAL)
            controls = raw["singleton_controls"]
            if change == "omitted":
                controls.pop()
            elif change == "extra":
                controls.append(copy.deepcopy(controls[0]))
            elif change == "substituted":
                controls[1]["belief"] = ["unseen"]
            else:
                controls[1]["belief"] = "R"
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_singleton_controls(FIXTURE, raw)

    def test_guard_composes_with_frozen_auditor_without_changing_it(self):
        source = DIAGNOSTIC.parent / "belief_recovery_margin_8527_t0_a02_20261008"
        spec = importlib.util.spec_from_file_location("frozen_belief_audit", source / "audit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        truth = json.loads((source / "truth.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(json.dumps(FIXTURE, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        result = audit_with_guard(FIXTURE, ORIGINAL, digest, truth, module.audit)
        self.assertEqual(result["status"], "PASS_BELIEF_RECOVERY_MARGIN_SCOPED")
        with self.assertRaises(ValueError):
            audit_with_guard(FIXTURE, DUPLICATE, digest, truth, module.audit)

    def test_duplicate_control_declaration_is_rejected(self):
        fixture = copy.deepcopy(FIXTURE)
        case = next(c for c in fixture["cases"] if c["id"] == "aliased-opposite-actions")
        case["singleton_controls"][1] = copy.deepcopy(case["singleton_controls"][0])
        with self.assertRaises(ValueError):
            validate_singleton_controls(fixture, ORIGINAL)


if __name__ == "__main__":
    unittest.main()
