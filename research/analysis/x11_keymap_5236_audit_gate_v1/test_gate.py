"""Only synthetic in-memory data and pure functions; no CLI or runner tests."""
from copy import deepcopy
import unittest

from research.x11_midprogram_keymap_5236_formal06_20261001.audit import audit as legacy_audit
from .fixtures import EXPECTED_EFFECT, PROVENANCE_CASES, WRONG_EFFECT, evidence, mutate, refuse
from .gate import audit_gate


STOP = "STOP_PROVENANCE_OR_RUNNER"
FAIL = "FAIL_STALE_MAP_EFFECT"
EXACT = "NO_STALE_EFFECT_OBSERVED"
REFUSED = "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"


class AuditGateTests(unittest.TestCase):
    def check(self, raw, wrapper, decision, reason=None):
        before = deepcopy((raw, wrapper))
        predecessor = legacy_audit(raw, wrapper)
        actual = audit_gate(raw, wrapper)
        self.assertEqual(actual["decision"], decision)
        self.assertEqual(actual["legacy_result"], predecessor)
        self.assertEqual((raw, wrapper), before)
        expected_reasons = [] if reason is None else ([reason] if isinstance(reason, str) else reason)
        self.assertEqual(actual["legacy_result"]["reasons"], expected_reasons)
        return actual

    def test_all_exact_is_not_blanket_stop(self):
        self.check(*evidence(), EXACT)

    def test_valid_wrong_effect_in_either_remap_is_fail(self):
        for index in (1, 2):
            with self.subTest(row=index):
                raw, wrapper = evidence()
                raw["rows"][index]["saved_effect_hex"] = WRONG_EFFECT
                self.check(raw, wrapper, FAIL)

    def test_both_wrong_remaps_are_fail(self):
        raw, wrapper = evidence()
        for row in raw["rows"][1:]:
            row["saved_effect_hex"] = WRONG_EFFECT
        self.check(raw, wrapper, FAIL)

    def test_two_valid_refusals_pass(self):
        raw, wrapper = evidence()
        for row in raw["rows"][1:]:
            refuse(row)
        self.check(raw, wrapper, REFUSED)

    def test_mixed_exact_and_refused_stops(self):
        raw, wrapper = evidence()
        refuse(raw["rows"][2])
        self.check(raw, wrapper, STOP, "mixed remap outcomes")

    def test_valid_wrong_effect_and_refused_is_fail(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        refuse(raw["rows"][2])
        self.check(raw, wrapper, FAIL)

    def test_five_provenance_faults_on_exact_and_wrong_seeds_stop(self):
        for stale in (False, True):
            for name, reason in PROVENANCE_CASES:
                with self.subTest(stale=stale, mutation=name):
                    raw, wrapper = evidence()
                    if stale:
                        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
                    before = deepcopy(raw)
                    changed = mutate(raw, name)
                    self.assertNotEqual(changed, raw, "mutation must be effective")
                    self.assertEqual(raw, before, "mutation must preserve seed")
                    expected_reasons = (
                        ["row order/id: jp_to_us", "row order/id: us_to_jp"]
                        if name == "swapped_direction" else [reason]
                    )
                    self.check(changed, wrapper, STOP, expected_reasons)

    def test_provenance_fault_in_other_row_overrides_wrong_effect(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        raw["rows"][2]["actor_receipt"] = None
        self.check(raw, wrapper, STOP, "missing actor receipt: us_to_jp")

    def test_missing_effect_in_other_row_overrides_wrong_effect(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        raw["rows"][2]["saved_effect_hex"] = None
        self.check(raw, wrapper, STOP, "missing completed effect: us_to_jp")

    def test_control_effect_fault_overrides_wrong_remap_effect(self):
        raw, wrapper = evidence()
        raw["rows"][0]["saved_effect_hex"] = WRONG_EFFECT
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        self.check(raw, wrapper, STOP, "control row effect/status")

    def test_source_binding_fault_overrides_wrong_effect(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        raw["source_blobs"]["synthetic-fixture.py"] = "2" * 40
        self.check(raw, wrapper, STOP, "source manifest binding")

    def test_wrapper_command_fault_overrides_wrong_effect(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        wrapper["command"] = []
        self.check(raw, wrapper, STOP, "namespace wrapper command")

    def test_invalid_release_with_wrong_other_row_stops(self):
        raw, wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        refuse(raw["rows"][2])
        raw["rows"][2]["dispatch"]["execution"]["releases"][0]["verified"] = False
        self.check(raw, wrapper, STOP, "neutral release: us_to_jp")

    def test_existing_early_stop_is_preserved(self):
        raw, wrapper = evidence()
        wrapper["timeout"] = True
        self.check(raw, wrapper, STOP, "wrapper status")

    def test_named_mutations_change_only_the_intended_data(self):
        raw, _ = evidence()
        for name, _ in PROVENANCE_CASES:
            with self.subTest(mutation=name):
                changed = mutate(raw, name)
                if name == "omitted_row":
                    self.assertEqual(changed["rows"], raw["rows"][:2])
                    changed["rows"] = deepcopy(raw["rows"])
                elif name == "swapped_direction":
                    self.assertEqual([row["row"] for row in changed["rows"]], ["control_us", "us_to_jp", "jp_to_us"])
                    changed["rows"] = deepcopy(raw["rows"])
                else:
                    field, value = {
                        "wrong_expected_bytes": ("expected_effect_hex", "00"),
                        "missing_actor_receipt": ("actor_receipt", None),
                        "missing_post_save_wait": ("post_save_wait", None),
                    }[name]
                    self.assertEqual(changed["rows"][1][field], value)
                    changed["rows"][1][field] = deepcopy(raw["rows"][1][field])
                self.assertEqual(changed, raw)

    def test_synthetic_builders_return_independent_objects(self):
        raw, wrapper = evidence()
        other_raw, other_wrapper = evidence()
        raw["rows"][1]["saved_effect_hex"] = WRONG_EFFECT
        wrapper["source_manifest"]["files"].clear()
        self.assertEqual(other_raw["rows"][1]["saved_effect_hex"], EXPECTED_EFFECT)
        self.assertTrue(other_wrapper["source_manifest"]["files"])
        self.assertTrue(raw["source_manifest"]["files"])

    def test_unknown_mutation_name_cannot_silently_noop(self):
        raw, _ = evidence()
        with self.assertRaisesRegex(ValueError, "Unknown synthetic mutation"):
            mutate(raw, "misspelled")
