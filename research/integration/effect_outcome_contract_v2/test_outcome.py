import unittest

from outcome import (
    ContractError,
    Event,
    EventKind,
    InvariantEvidence,
    InvariantRequirement,
    OperationKind,
    OutcomeKind,
    TerminalPhase,
    evaluate_required_invariants,
    reduce_outcome,
)

EFFECT = EventKind.EFFECT
COMP = EventKind.COMPENSATION
REQS = [
    InvariantRequirement("primary", "old"),
    InvariantRequirement("collateral", "preserve"),
]
GOOD = [
    InvariantEvidence("primary", "old", True),
    InvariantEvidence("collateral", "preserve", True),
]


def compensated(evidence=GOOD, requirements=REQS, current="old"):
    return reduce_outcome(
        operation_kind=OperationKind.DIRECT,
        initial_state="old",
        intended_state="target",
        current_state=current,
        terminal_phase=TerminalPhase.EFFECT_COMMITTED,
        events=[Event(1, EFFECT, "wrong"), Event(2, COMP, current)],
        compensation_requirements=requirements,
        compensation_evidence=evidence,
    )


class V1RegressionTests(unittest.TestCase):
    def test_stageable_publication_verified(self):
        out = reduce_outcome(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old", intended_state="target", current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target")],
        )
        self.assertEqual(out.kind, OutcomeKind.PUBLISHED_VERIFIED)
        self.assertTrue(out.effect_occurred)

    def test_pre_effect_refusal(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
        )
        self.assertEqual(out.kind, OutcomeKind.REJECTED_PRE_EFFECT)
        self.assertFalse(out.effect_occurred)

    def test_direct_effect_verified(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target")],
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_VERIFIED)

    def test_wrong_effect_uncompensated(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong")],
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED)
        self.assertTrue(out.effect_occurred)
        self.assertTrue(out.contradiction_observed)


class RequiredInvariantTests(unittest.TestCase):
    def test_clean_two_invariant_compensation(self):
        out = compensated()
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED)
        self.assertTrue(out.effect_occurred)
        self.assertTrue(out.compensation_attempted)
        self.assertTrue(out.compensation_verified)
        self.assertTrue(out.invariant_status.complete)
        self.assertEqual(len(out.history), 2)

    def test_collateral_contradiction_is_incomplete(self):
        out = compensated([
            InvariantEvidence("primary", "old", True),
            InvariantEvidence("collateral", "damaged", True),
        ])
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertFalse(out.compensation_verified)
        self.assertEqual(out.invariant_status.contradicted, ("collateral",))
        self.assertTrue(out.effect_occurred)

    def test_missing_collateral_is_incomplete(self):
        out = compensated([InvariantEvidence("primary", "old", True)])
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertEqual(out.invariant_status.missing, ("collateral",))

    def test_unverified_collateral_is_incomplete(self):
        out = compensated([
            InvariantEvidence("primary", "old", True),
            InvariantEvidence("collateral", "preserve", False),
        ])
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertEqual(out.invariant_status.unverified, ("collateral",))

    def test_extra_evidence_does_not_substitute_missing_required(self):
        out = compensated([
            InvariantEvidence("primary", "old", True),
            InvariantEvidence("other", "ok", True),
        ])
        self.assertEqual(out.invariant_status.missing, ("collateral",))
        self.assertEqual(out.invariant_status.extra_evidence, ("other",))
        self.assertFalse(out.compensation_verified)

    def test_all_missing_is_incomplete_not_success(self):
        out = compensated([])
        self.assertFalse(out.invariant_status.complete)
        self.assertEqual(out.invariant_status.missing, ("collateral", "primary"))
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)

    def test_effect_history_preserved_when_incomplete(self):
        out = compensated([InvariantEvidence("primary", "old", True)])
        self.assertEqual(out.history[0].value, "wrong")
        self.assertTrue(out.effect_occurred)
        self.assertTrue(out.contradiction_observed)

    def test_extra_verified_evidence_allowed_when_required_complete(self):
        out = compensated(GOOD + [InvariantEvidence("diagnostic", "ok", True)])
        self.assertTrue(out.compensation_verified)
        self.assertEqual(out.invariant_status.extra_evidence, ("diagnostic",))

    def test_evaluator_directly_reports_status(self):
        status = evaluate_required_invariants(
            REQS,
            [InvariantEvidence("primary", "old", True), InvariantEvidence("collateral", "bad", True)],
        )
        self.assertFalse(status.complete)
        self.assertEqual(status.contradicted, ("collateral",))


class FailClosedInputTests(unittest.TestCase):
    def assert_contract_error(self, **kwargs):
        with self.assertRaises(ContractError):
            reduce_outcome(**kwargs)

    def test_empty_required_set_rejects_compensation(self):
        with self.assertRaises(ContractError):
            compensated(GOOD, [])

    def test_duplicate_requirement_names_reject(self):
        with self.assertRaises(ContractError):
            compensated(GOOD, [InvariantRequirement("x", "1"), InvariantRequirement("x", "2")])

    def test_duplicate_evidence_names_reject(self):
        with self.assertRaises(ContractError):
            compensated([
                InvariantEvidence("primary", "old", True),
                InvariantEvidence("primary", "old", True),
            ])

    def test_invariant_inputs_without_compensation_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong")],
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_pre_effect_with_invariant_inputs_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_compensation_without_primary_effect_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, COMP, "old")],
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_nonmonotone_event_sequence_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(2, EFFECT, "wrong"), Event(2, COMP, "old")],
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_duplicate_primary_effect_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong2",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong1"), Event(2, EFFECT, "wrong2")],
        )

    def test_current_state_history_mismatch_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="other",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong"), Event(2, COMP, "old")],
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_wrong_stageable_publication_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "wrong")],
        )

    def test_compensation_after_verified_effect_reject(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=[Event(1, EFFECT, "target"), Event(2, COMP, "old")],
            compensation_requirements=REQS,
            compensation_evidence=GOOD,
        )

    def test_requirement_requires_nonempty_name(self):
        with self.assertRaises(ContractError):
            InvariantRequirement("", "old")

    def test_evidence_requires_real_bool(self):
        with self.assertRaises(ContractError):
            InvariantEvidence("primary", "old", 1)

    def test_initial_and_intended_must_differ(self):
        self.assert_contract_error(
            operation_kind=OperationKind.DIRECT,
            initial_state="same", intended_state="same", current_state="same",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
        )


if __name__ == "__main__":
    unittest.main()
