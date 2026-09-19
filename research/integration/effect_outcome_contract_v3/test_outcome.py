import unittest

from outcome import (
    ContractError,
    Event,
    EventKind,
    ExecutionBinding,
    InvariantEvidence,
    InvariantManifest,
    InvariantRequirement,
    OperationKind,
    OutcomeKind,
    TerminalPhase,
    VerificationReceipt,
    bind_invariant_manifest,
    evaluate_bound_invariants,
    reduce_outcome,
)

EFFECT = EventKind.EFFECT
COMP = EventKind.COMPENSATION
REQ_PRIMARY = InvariantRequirement("primary", "old")
REQ_COLLATERAL = InvariantRequirement("collateral", "preserve")


def manifest(scope="task-1", requirements=(REQ_PRIMARY, REQ_COLLATERAL)):
    return bind_invariant_manifest(scope, requirements)


def binding(m, command="cmd-1"):
    return ExecutionBinding(command, m.manifest_id)


def receipt(m, evidence):
    return VerificationReceipt(m.manifest_id, tuple(evidence))


def clean_evidence():
    return (
        InvariantEvidence("primary", "old", True),
        InvariantEvidence("collateral", "preserve", True),
    )


def damaged_evidence():
    return (
        InvariantEvidence("primary", "old", True),
        InvariantEvidence("collateral", "damaged", True),
    )


def compensated_history():
    return (Event(1, EFFECT, "wrong"), Event(2, COMP, "old"))


class ManifestIdentityTests(unittest.TestCase):
    def test_requirement_order_is_canonical(self):
        a = manifest(requirements=(REQ_PRIMARY, REQ_COLLATERAL))
        b = manifest(requirements=(REQ_COLLATERAL, REQ_PRIMARY))
        self.assertEqual(a.manifest_id, b.manifest_id)
        self.assertEqual(a.requirements, b.requirements)

    def test_requirement_content_changes_identity(self):
        a = manifest()
        b = manifest(requirements=(REQ_PRIMARY, InvariantRequirement("collateral", "other")))
        self.assertNotEqual(a.manifest_id, b.manifest_id)

    def test_scope_changes_identity(self):
        self.assertNotEqual(manifest("task-1").manifest_id, manifest("task-2").manifest_id)

    def test_empty_manifest_rejected(self):
        with self.assertRaises(ContractError):
            bind_invariant_manifest("task-1", ())

    def test_duplicate_requirement_rejected(self):
        with self.assertRaises(ContractError):
            bind_invariant_manifest("task-1", (REQ_PRIMARY, REQ_PRIMARY))

    def test_empty_scope_rejected(self):
        with self.assertRaises(ContractError):
            bind_invariant_manifest("", (REQ_PRIMARY,))

    def test_invalid_execution_digest_rejected(self):
        with self.assertRaises(ContractError):
            ExecutionBinding("cmd", "not-a-digest")

    def test_invalid_receipt_digest_rejected(self):
        with self.assertRaises(ContractError):
            VerificationReceipt("not-a-digest", ())


class V2RegressionTests(unittest.TestCase):
    def test_stageable_verified(self):
        out = reduce_outcome(
            operation_kind=OperationKind.STAGEABLE,
            initial_state="old", intended_state="target", current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=(Event(1, EFFECT, "target"),),
        )
        self.assertEqual(out.kind, OutcomeKind.PUBLISHED_VERIFIED)

    def test_pre_effect_refusal(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
        )
        self.assertEqual(out.kind, OutcomeKind.REJECTED_PRE_EFFECT)
        self.assertFalse(out.effect_occurred)

    def test_direct_verified(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="target",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=(Event(1, EFFECT, "target"),),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_VERIFIED)

    def test_direct_uncompensated(self):
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=(Event(1, EFFECT, "wrong"),),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED)
        self.assertTrue(out.effect_occurred)

    def test_prebound_manifest_allowed_without_later_compensation(self):
        m = manifest()
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="wrong",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=(Event(1, EFFECT, "wrong"),),
            invariant_manifest=m,
            execution_binding=binding(m),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_UNCOMPENSATED)
        self.assertEqual(out.invariant_manifest_id, m.manifest_id)


class BoundCompensationTests(unittest.TestCase):
    def test_clean_compensation_under_prebound_manifest(self):
        m = manifest()
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=compensated_history(),
            invariant_manifest=m,
            execution_binding=binding(m),
            verification_receipt=receipt(m, clean_evidence()),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED)
        self.assertTrue(out.effect_occurred)
        self.assertTrue(out.compensation_verified)
        self.assertEqual(out.history, compensated_history())
        self.assertEqual(out.invariant_manifest_id, m.manifest_id)

    def test_collateral_damage_remains_incomplete(self):
        m = manifest()
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=compensated_history(),
            invariant_manifest=m,
            execution_binding=binding(m),
            verification_receipt=receipt(m, damaged_evidence()),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertFalse(out.compensation_verified)
        self.assertEqual(out.invariant_status.contradicted, ("collateral",))
        self.assertTrue(out.effect_occurred)

    def test_missing_required_evidence_is_incomplete(self):
        m = manifest()
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=compensated_history(), invariant_manifest=m,
            execution_binding=binding(m),
            verification_receipt=receipt(m, (InvariantEvidence("primary", "old", True),)),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertEqual(out.invariant_status.missing, ("collateral",))

    def test_unverified_required_evidence_is_incomplete(self):
        m = manifest()
        out = reduce_outcome(
            operation_kind=OperationKind.DIRECT,
            initial_state="old", intended_state="target", current_state="old",
            terminal_phase=TerminalPhase.EFFECT_COMMITTED,
            events=compensated_history(), invariant_manifest=m,
            execution_binding=binding(m),
            verification_receipt=receipt(m, (
                InvariantEvidence("primary", "old", True),
                InvariantEvidence("collateral", "preserve", False),
            )),
        )
        self.assertEqual(out.kind, OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertEqual(out.invariant_status.unverified, ("collateral",))

    def test_extra_evidence_does_not_change_complete_status(self):
        m = manifest()
        r = receipt(m, clean_evidence() + (InvariantEvidence("diagnostic", "ok", True),))
        status = evaluate_bound_invariants(m, binding(m), r)
        self.assertTrue(status.complete)
        self.assertEqual(status.extra_evidence, ("diagnostic",))


class AntiRewriteBindingTests(unittest.TestCase):
    def test_post_effect_requirement_shrink_cannot_authorize_executed_command(self):
        original = manifest()
        executed = binding(original)
        shrunk = manifest(requirements=(REQ_PRIMARY,))
        shrunk_receipt = receipt(shrunk, (InvariantEvidence("primary", "old", True),))
        with self.assertRaisesRegex(ContractError, "executed command is bound"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(),
                invariant_manifest=shrunk,
                execution_binding=executed,
                verification_receipt=shrunk_receipt,
            )

    def test_cross_scope_manifest_cannot_authorize_executed_command(self):
        original = manifest("task-A")
        other = manifest("task-B")
        with self.assertRaisesRegex(ContractError, "executed command is bound"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(), invariant_manifest=other,
                execution_binding=binding(original),
                verification_receipt=receipt(other, clean_evidence()),
            )

    def test_receipt_for_other_manifest_rejected(self):
        m = manifest("task-A")
        other = manifest("task-B")
        with self.assertRaisesRegex(ContractError, "verification receipt is bound"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(), invariant_manifest=m,
                execution_binding=binding(m),
                verification_receipt=receipt(other, clean_evidence()),
            )

    def test_tampered_manifest_id_rejected(self):
        m = manifest()
        tampered = InvariantManifest(m.scope_id, m.requirements, "0" * 64)
        with self.assertRaisesRegex(ContractError, "manifest_id does not match"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "wrong"),),
                invariant_manifest=tampered,
                execution_binding=ExecutionBinding("cmd-1", "0" * 64),
            )

    def test_duplicate_receipt_evidence_rejected(self):
        m = manifest()
        r = receipt(m, (
            InvariantEvidence("primary", "old", True),
            InvariantEvidence("primary", "old", True),
        ))
        with self.assertRaisesRegex(ContractError, "duplicate evidence"):
            evaluate_bound_invariants(m, binding(m), r)

    def test_manifest_without_binding_rejected(self):
        with self.assertRaisesRegex(ContractError, "supplied together"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "wrong"),),
                invariant_manifest=manifest(),
            )

    def test_binding_without_manifest_rejected(self):
        m = manifest()
        with self.assertRaisesRegex(ContractError, "supplied together"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "wrong"),),
                execution_binding=binding(m),
            )

    def test_compensation_without_prebound_manifest_rejected(self):
        with self.assertRaisesRegex(ContractError, "pre-effect invariant"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(),
            )

    def test_compensation_without_receipt_rejected(self):
        m = manifest()
        with self.assertRaisesRegex(ContractError, "verification receipt"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(), invariant_manifest=m,
                execution_binding=binding(m),
            )

    def test_receipt_without_compensation_event_rejected(self):
        m = manifest()
        with self.assertRaisesRegex(ContractError, "verification receipt requires"):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="target",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "target"),), invariant_manifest=m,
                execution_binding=binding(m), verification_receipt=receipt(m, clean_evidence()),
            )


class GenericFailClosedTests(unittest.TestCase):
    def test_pre_effect_with_history_rejected(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.REJECTED_PRE_EFFECT,
                events=(Event(1, EFFECT, "wrong"),),
            )

    def test_nonmonotone_history_rejected(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="old",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(2, EFFECT, "wrong"), Event(2, COMP, "old")),
            )

    def test_state_history_tail_mismatch_rejected(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=compensated_history(),
            )

    def test_duplicate_primary_effect_rejected(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.DIRECT,
                initial_state="old", intended_state="target", current_state="wrong2",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "wrong1"), Event(2, EFFECT, "wrong2")),
            )

    def test_wrong_stageable_publication_rejected(self):
        with self.assertRaises(ContractError):
            reduce_outcome(
                operation_kind=OperationKind.STAGEABLE,
                initial_state="old", intended_state="target", current_state="wrong",
                terminal_phase=TerminalPhase.EFFECT_COMMITTED,
                events=(Event(1, EFFECT, "wrong"),),
            )


if __name__ == "__main__":
    unittest.main()
