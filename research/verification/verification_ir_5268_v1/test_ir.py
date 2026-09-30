import unittest

from candidate import lower_action, validate_ir


class VerificationIRTests(unittest.TestCase):
    def test_lowering_preserves_frozen_required_checks_and_evidence_roles(self):
        action = {
            "action_id": "case-permission-change",
            "target_ref": "window:save-dialog",
            "expected_target_ref": "window:save-dialog",
            "intent_ref": "intent:save-as-v1",
            "target_ambiguous": False,
            "scope_changed": False,
            "deadline_expired": False,
            "permission_current": False,
            "external_side_effect": False,
            "effect_already_satisfied": False,
            "evidence_unknown": False,
            "diagnostic_requested": False,
        }
        ir = lower_action(action)
        self.assertEqual(ir["schema"], "verification_ir.v0.1")
        self.assertEqual(
            [(c["primitive"], c["subject_ref"], c["required_evidence_role"])
             for c in ir["checks"]],
            [
                ("TARGET.IDENTITY_CURRENT", "window:save-dialog", "CURRENT_OBSERVATION"),
                ("SEMANTIC.INTENT_MATCH", "intent:save-as-v1", "CURRENT_INTENT"),
                ("AUTHORITY.PERMISSION_CURRENT", "window:save-dialog", "CURRENT_PERMISSION"),
            ],
        )
        self.assertNotIn("authority", ir)

    def test_unknown_evidence_is_explicit_and_cannot_become_pass(self):
        action = {
            "action_id": "case-unknown-evidence",
            "target_ref": "document:7",
            "expected_target_ref": "document:7",
            "intent_ref": "intent:replace-text-v2",
            "target_ambiguous": False,
            "scope_changed": False,
            "deadline_expired": False,
            "permission_current": True,
            "external_side_effect": True,
            "effect_already_satisfied": False,
            "evidence_unknown": True,
            "diagnostic_requested": False,
        }
        ir = lower_action(action)
        self.assertTrue(ir["unknown_check_required"])
        self.assertIn("META.UNKNOWN_REQUIRED", [c["primitive"] for c in ir["checks"]])
        self.assertNotEqual(ir.get("verdict"), "PASS")

    def test_strict_decoder_rejects_authority_injection_and_unknown_primitives(self):
        valid = {
            "schema": "verification_ir.v0.1",
            "unknown_check_required": False,
            "checks": [{
                "check_id": "c1",
                "primitive": "TARGET.IDENTITY_CURRENT",
                "subject_ref": "window:1",
                "criticality": "MANDATORY",
                "required_evidence_role": "CURRENT_OBSERVATION",
                "verifier_class": "deterministic",
                "dependencies": [],
                "deadline": None,
                "budget_class": "bounded",
                "fallback": "YIELD",
            }],
        }
        injected = dict(valid, authority="GRANTED")
        with self.assertRaises(ValueError):
            validate_ir(injected)
        unknown = {**valid, "checks": [{**valid["checks"][0], "primitive": "TARGET.NOVEL"}]}
        with self.assertRaises(ValueError):
            validate_ir(unknown)

    def test_malformed_unhashable_primitive_is_a_controlled_rejection(self):
        malformed = {
            "schema": "verification_ir.v0.1",
            "unknown_check_required": False,
            "checks": [{
                "check_id": "c1",
                "primitive": ["TARGET.IDENTITY_CURRENT"],
                "subject_ref": "window:1",
                "criticality": "MANDATORY",
                "required_evidence_role": "CURRENT_OBSERVATION",
                "verifier_class": "deterministic",
                "dependencies": [],
                "deadline": None,
                "budget_class": "bounded",
                "fallback": "YIELD_NO_INPUT",
            }],
        }
        with self.assertRaises(ValueError):
            validate_ir(malformed)

    def test_schema_round_trip_preserves_dependency_role_and_criticality(self):
        target = {
            "check_id": "target-1",
            "primitive": "TARGET.IDENTITY_CURRENT",
            "subject_ref": "document:7",
            "criticality": "MANDATORY",
            "required_evidence_role": "CURRENT_OBSERVATION",
            "verifier_class": "fresh_target_observer",
            "dependencies": [],
            "deadline": None,
            "budget_class": "bounded",
            "fallback": "YIELD_NO_INPUT",
        }
        effect = {
            "check_id": "effect-1",
            "primitive": "EFFECT.POSTCONDITION",
            "subject_ref": "document:7",
            "criticality": "CONDITIONAL_MANDATORY",
            "required_evidence_role": "VERIFIED_EFFECT",
            "verifier_class": "independent_observer",
            "dependencies": ["target-1"],
            "deadline": None,
            "budget_class": "bounded",
            "fallback": "YIELD_NO_INPUT",
        }
        sample = {
            "schema": "verification_ir.v0.1",
            "unknown_check_required": False,
            "checks": [target, effect],
        }
        self.assertEqual(validate_ir(sample), sample)


if __name__ == "__main__":
    unittest.main()
