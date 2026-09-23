import copy
import unittest

from runtime.cli_v1.lineage import (
    dispatch_with_lineage, receipt_digest, program_digest, sidecar_digest,
)


def fixture():
    program = {"program_id": "public-lineage-1",
               "source": {"observation_seq": 7, "binding_revision": 3},
               "ops": [{"op": "pointer_move", "x": 120, "y": 80},
                       {"op": "release_all"}]}
    receipt = {"receipt_id": "r1", "role": "ADMISSION_DEPENDENCY",
               "currentness": "CURRENT", "point": [120, 80],
               "observation_seq": 7, "binding_revision": 3,
               "source_receipt_id": None}
    receipt["digest"] = receipt_digest(receipt)
    sidecar = {"program_digest": program_digest(program),
               "evidence_receipt_digest": receipt["digest"],
               "role": receipt["role"], "currentness": receipt["currentness"],
               "point": receipt["point"], "observation_seq": 7,
               "binding_revision": 3}
    sidecar["digest"] = sidecar_digest(sidecar)
    return program, receipt, sidecar


def invoke(program, receipt, sidecar, calls):
    return dispatch_with_lineage(
        program, {"fixture": 1}, receipt, sidecar,
        current_observation_seq=7, current_binding_revision=3,
        dispatch_fn=lambda *a, **k: calls.append((a, k)) or {"status": "returned"},
    )


class PublicLineageFreshnessTests(unittest.TestCase):
    def test_stale_observation_precedes_dispatch(self):
        program, receipt, sidecar = fixture()
        calls = []
        stale = copy.deepcopy(receipt)
        stale["observation_seq"] = 6
        stale["digest"] = receipt_digest(stale)
        sidecar["observation_seq"] = 6
        sidecar["digest"] = sidecar_digest(sidecar)
        row = invoke(program, stale, sidecar, calls)
        self.assertEqual(row["error"], "STALE_OBSERVATION")
        self.assertEqual(calls, [])

    def test_stale_binding_precedes_dispatch(self):
        program, receipt, sidecar = fixture()
        calls = []
        stale = copy.deepcopy(receipt)
        stale["binding_revision"] = 2
        stale["digest"] = receipt_digest(stale)
        sidecar["binding_revision"] = 2
        sidecar["digest"] = sidecar_digest(sidecar)
        row = invoke(program, stale, sidecar, calls)
        self.assertEqual(row["error"], "STALE_BINDING")
        self.assertEqual(calls, [])

    def test_valid_current_lineage_delegates_once(self):
        program, receipt, sidecar = fixture()
        calls = []
        row = invoke(program, receipt, sidecar, calls)
        self.assertEqual(row["status"], "delegated")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
