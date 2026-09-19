import sqlite3
import tempfile
import unittest
from pathlib import Path

from bridge import classify_from_owner, dependency_identity, load_v3
from owner import (
    OwnerConflict,
    OwnerIntegrityError,
    apply_compensation,
    apply_effect,
    effect_count,
    read_execution_receipt,
)

v3 = load_v3()
REQ_PRIMARY = v3.InvariantRequirement("primary", "old")
REQ_COLLATERAL = v3.InvariantRequirement("collateral", "preserve")


def full_manifest(scope="task-1"):
    return v3.bind_invariant_manifest(scope, (REQ_PRIMARY, REQ_COLLATERAL))


def clean_evidence():
    return (
        v3.InvariantEvidence("primary", "old", True),
        v3.InvariantEvidence("collateral", "preserve", True),
    )


def damaged_evidence():
    return (
        v3.InvariantEvidence("primary", "old", True),
        v3.InvariantEvidence("collateral", "damaged", True),
    )


class DependencyIdentityTests(unittest.TestCase):
    def test_exact_merged_v3_identity(self):
        self.assertEqual(dependency_identity(), {
            "bytes": 15466,
            "sha256": "4fd5a6001407b9e91ab3265aeca491643e035641f7926316ebf8835ba7b79449",
            "git_blob": "680b104b28ba37633ec1031eac41c1945eb3aed9",
        })


class OwnerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "owner.sqlite"
        self.m = full_manifest()

    def tearDown(self):
        self.td.cleanup()

    def apply(self, *, command="cmd-1", intended="target", actual="target", manifest=None):
        m = manifest or self.m
        return apply_effect(
            self.db,
            command_id=command,
            invariant_manifest_id=m.manifest_id,
            intended_value=intended,
            actual_value=actual,
        )

    def classify(self, *, command="cmd-1", manifest=None, evidence=()):
        return classify_from_owner(
            db_path=self.db,
            command_id=command,
            invariant_manifest=manifest or self.m,
            initial_state="old",
            intended_state="target",
            verification_evidence=evidence,
        )

    def test_correct_effect_uses_owner_receipt_binding(self):
        r = self.apply()
        out = self.classify()
        self.assertEqual(out.kind, v3.OutcomeKind.EFFECT_VERIFIED)
        self.assertEqual(out.invariant_manifest_id, r.invariant_manifest_id)
        self.assertEqual(effect_count(self.db), 1)

    def test_clean_compensation(self):
        r = self.apply(actual="wrong")
        apply_compensation(self.db, command_id="cmd-1", value="old")
        out = self.classify(evidence=clean_evidence())
        self.assertEqual(out.kind, v3.OutcomeKind.EFFECT_CONTRADICTED_COMPENSATED)
        self.assertTrue(out.compensation_verified)
        self.assertEqual(out.invariant_manifest_id, r.invariant_manifest_id)

    def test_collateral_damage_is_incomplete(self):
        self.apply(actual="wrong")
        apply_compensation(self.db, command_id="cmd-1", value="old")
        out = self.classify(evidence=damaged_evidence())
        self.assertEqual(out.kind, v3.OutcomeKind.EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE)
        self.assertEqual(out.invariant_status.contradicted, ("collateral",))

    def test_adapter_post_effect_shrink_cannot_replace_owner_receipt_binding(self):
        self.apply(actual="wrong")
        apply_compensation(self.db, command_id="cmd-1", value="old")
        shrunk = v3.bind_invariant_manifest("task-1", (REQ_PRIMARY,))
        with self.assertRaisesRegex(v3.ContractError, "executed command is bound"):
            self.classify(
                manifest=shrunk,
                evidence=(v3.InvariantEvidence("primary", "old", True),),
            )

    def test_exact_receipt_replay_is_read_only(self):
        first = self.apply(actual="wrong")
        second = self.apply(actual="wrong")
        self.assertFalse(first.replay)
        self.assertTrue(second.replay)
        self.assertEqual(first.effect_seq, second.effect_seq)
        self.assertEqual(effect_count(self.db), 1)

    def test_same_command_different_content_conflicts(self):
        self.apply(actual="wrong")
        with self.assertRaises(OwnerConflict):
            self.apply(actual="target")
        self.assertEqual(effect_count(self.db), 1)

    def test_unknown_command_fails_closed(self):
        with self.assertRaises(OwnerIntegrityError):
            read_execution_receipt(self.db, "missing")

    def test_tampered_receipt_manifest_disagrees_with_command_record(self):
        self.apply(actual="wrong")
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("UPDATE receipts SET invariant_manifest_id=? WHERE command_id='cmd-1'", ("0" * 64,))
            conn.commit()
        finally:
            conn.close()
        with self.assertRaisesRegex(OwnerIntegrityError, "receipt manifest disagrees"):
            self.classify()

    def test_tampered_effect_receipt_disagrees_with_event(self):
        self.apply(actual="wrong")
        conn = sqlite3.connect(self.db)
        try:
            conn.execute("UPDATE receipts SET effect_value='target' WHERE command_id='cmd-1'")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaisesRegex(OwnerIntegrityError, "authoritative effect event"):
            self.classify()

    def test_compensation_requires_existing_command(self):
        with self.assertRaises(OwnerIntegrityError):
            apply_compensation(self.db, command_id="missing", value="old")

    def test_second_compensation_rejected(self):
        self.apply(actual="wrong")
        apply_compensation(self.db, command_id="cmd-1", value="old")
        with self.assertRaises(OwnerConflict):
            apply_compensation(self.db, command_id="cmd-1", value="old")


if __name__ == "__main__":
    unittest.main()
