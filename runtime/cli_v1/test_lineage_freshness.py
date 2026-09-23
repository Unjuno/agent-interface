"""Direct freshness coverage for public lineage dispatch."""
import unittest

from runtime.cli_v1.lineage import (
    dispatch_with_lineage,
    program_digest,
    receipt_digest,
    sidecar_digest,
)


def case():
    program = {
        "source": {"observation_seq": 7, "binding_revision": 3},
        "ops": [{"op": "pointer_move", "x": 10, "y": 20}],
    }
    receipt = {
        "receipt_id": "r1",
        "role": "ADMISSION_DEPENDENCY",
        "currentness": "CURRENT",
        "point": [10, 20],
        "observation_seq": 7,
        "binding_revision": 3,
        "source_receipt_id": "s1",
    }
    receipt["digest"] = receipt_digest(receipt)
    sidecar = {
        "program_digest": program_digest(program),
        "evidence_receipt_digest": receipt["digest"],
        "role": receipt["role"],
        "currentness": receipt["currentness"],
        "point": receipt["point"],
        "observation_seq": 7,
        "binding_revision": 3,
    }
    sidecar["digest"] = sidecar_digest(sidecar)
    return program, receipt, sidecar


class DirectLineageFreshnessTests(unittest.TestCase):
    def test_stale_observation_rejected_before_dispatch(self):
        program, receipt, sidecar = case()
        calls = []
        result = dispatch_with_lineage(
            program, {}, receipt, sidecar,
            current_observation_seq=8,
            current_binding_revision=3,
            dispatch_fn=lambda *args, **kwargs: calls.append(1),
        )
        self.assertEqual(result["status"], "lineage_rejected")
        self.assertEqual(result["error"], "STALE_OBSERVATION")
        self.assertEqual(calls, [])

    def test_stale_binding_rejected_before_dispatch(self):
        program, receipt, sidecar = case()
        calls = []
        result = dispatch_with_lineage(
            program, {}, receipt, sidecar,
            current_observation_seq=7,
            current_binding_revision=4,
            dispatch_fn=lambda *args, **kwargs: calls.append(1),
        )
        self.assertEqual(result["status"], "lineage_rejected")
        self.assertEqual(result["error"], "STALE_BINDING")
        self.assertEqual(calls, [])

    def test_current_lineage_delegates_once(self):
        program, receipt, sidecar = case()
        calls = []
        result = dispatch_with_lineage(
            program, {}, receipt, sidecar,
            current_observation_seq=7,
            current_binding_revision=3,
            dispatch_fn=lambda *args, **kwargs: calls.append(1) or {"ok": True},
        )
        self.assertEqual(result["status"], "delegated")
        self.assertEqual(result["cli_result"], {"ok": True})
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
