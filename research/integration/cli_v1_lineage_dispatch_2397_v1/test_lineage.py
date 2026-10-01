import copy
import unittest

from runtime.cli_v1.lineage import (
    dispatch_with_lineage, program_digest, receipt_digest, sidecar_digest,
)


def fixture():
    program = {
        "program_id": "public-lineage-1",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "ops": [{"op": "pointer_move", "x": 120, "y": 80}, {"op": "release_all"}],
    }
    receipt = {
        "receipt_id": "r1", "role": "ADMISSION_DEPENDENCY",
        "currentness": "CURRENT", "point": [120, 80],
        "observation_seq": 7, "binding_revision": 3, "source_receipt_id": None,
    }
    receipt["digest"] = receipt_digest(receipt)
    sidecar = {
        "program_digest": program_digest(program),
        "evidence_receipt_digest": receipt["digest"],
        "role": receipt["role"], "currentness": receipt["currentness"],
        "point": receipt["point"], "observation_seq": 7, "binding_revision": 3,
    }
    sidecar["digest"] = sidecar_digest(sidecar)
    return program, receipt, sidecar


class PublicLineageTests(unittest.TestCase):
    def test_rejection_precedes_dispatch(self):
        program, receipt, sidecar = fixture()
        calls = []
        changed = copy.deepcopy(program)
        changed["source"]["binding_revision"] = 4
        row = dispatch_with_lineage(
            changed, {"fixture": 1}, receipt, sidecar,
            current_observation_seq=7, current_binding_revision=3,
            dispatch_fn=lambda *a, **k: calls.append((a, k)),
        )
        self.assertEqual(row["status"], "lineage_rejected")
        self.assertEqual(row["error"], "PROGRAM_DIGEST_MISMATCH")
        self.assertEqual(calls, [])

    def test_valid_lineage_delegates_to_cli(self):
        program, receipt, sidecar = fixture()
        calls = []
        row = dispatch_with_lineage(
            program, {"fixture": 1}, receipt, sidecar,
            current_observation_seq=7, current_binding_revision=3,
            dispatch_fn=lambda *a, **k: calls.append((a, k)) or {"status": "returned"},
        )
        self.assertEqual(row["status"], "delegated")
        self.assertEqual(row["cli_result"], {"status": "returned"})
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
