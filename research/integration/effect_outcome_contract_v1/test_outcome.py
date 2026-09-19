import unittest

from outcome import (
    ContractError,
    Event,
    EventKind,
    OperationKind,
    OutcomeKind,
    TerminalPhase,
    reduce_outcome,
)


EFFECT = EventKind.EFFECT
COMP = EventKind.COMPENSATION


class SupportedOutcomeTests(unittest.TestCase):
    def test_stageable_publication_verified(self):
        result = reduce_outcome(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old",
            intended_state="target",
            current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target")],
        )
        self.assertEqual(result.kind, OutcomeKind.PUBLISHED_VERIFIED)
        self.assertTrue(result.effect_occurred)
        self.assertTrue(result.intended_effect_verified)
        self.assertFalse(result.contradiction_observed)

    def test_pre_effect_refusal_has_no_effect(self):
        result = reduce_outcome(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old",
            intended_state="target",
            current_state="old",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
        )
        self.assertEqual(result.kind, OutcomeKind.REJECTED_PRE_EFFECT)
        self.assertFalse(result.effect_occurred)
        self.assertFalse(result.intended_effect_verified)

    def test_direct_effect_verified(self):
        result = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old",
            intended_state="target",
            current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target")],
        )
        self.assertEqual(result.kind, OutcomeKind.EFFECT_VERIFIED)
        self.assertTrue(result.effect_occurred)
        self.assertTrue(result.intended_effect_verified)

    def test_direct_wrong_effect_uncompensated(self):
        result = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old",
            intended_state="target",
            current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong")],
        )
        self.assertEqual(result.kind, OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED)
        self.assertTrue(result.effect_occurred)
        self.assertTrue(result.contradiction_observed)
        self.assertFalse(result.compensation_attempted)

    def test_direct_wrong_effect_compensated_preserves_history(self):
        history = [Event(1, EFFECT, "wrong"), Event(2, COMP, "old")]
        result = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old",
            intended_state="target",
            current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=history,
        )
        self.assertEqual(result.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED)
        self.assertTrue(result.effect_occurred)
        self.assertFalse(result.intended_effect_verified)
        self.assertTrue(result.contradiction_observed)
        self.assertTrue(result.compensation_attempted)
        self.assertTrue(result.compensation_verified)
        self.assertEqual(result.history, tuple(history))
        self.assertEqual(result.current_state, "old")


class FailClosedTests(unittest.TestCase):
    def assertContractError(self, **kwargs):
        with self.assertRaises(ContractError):
            reduce_outcome(**kwargs)

    def test_reject_pre_effect_with_history(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
            events=[Event(1, EFFECT, "wrong")],
        )

    def test_reject_compensation_without_prior_effect(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, COMP, "old")],
        )

    def test_reject_nonmonotone_sequence(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(2, EFFECT, "wrong"), Event(2, COMP, "old")],
        )

    def test_reject_current_state_mismatch_with_history_tail(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong"), Event(2, COMP, "old")],
        )

    def test_reject_duplicate_primary_effect(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong2",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong1"), Event(2, EFFECT, "wrong2")],
        )

    def test_reject_failed_or_partial_compensation(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="partial",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong"), Event(2, COMP, "partial")],
        )

    def test_reject_wrong_stageable_publication(self):
        self.assertContractError(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong")],
        )

    def test_reject_no_history_after_effect_committed(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[],
        )

    def test_reject_compensation_after_verified_effect(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target"), Event(2, COMP, "old")],
        )

    def test_reject_wrong_direct_effect_collapsed_to_initial_without_compensation(self):
        self.assertContractError(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "old")],
        )


class InputValidationTests(unittest.TestCase):
    def test_event_requires_positive_integer_sequence(self):
        with self.assertRaises(ContractError):
            Event(0, EFFECT, "x")

    def test_event_requires_nonempty_value(self):
        with self.assertRaises(ContractError):
            Event(1, EFFECT, "")

    def test_initial_and_intended_must_differ(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="same", intended_state="same", current_state="same",
                terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
            )


if __name__ == "__main__":
    unittest.main()
