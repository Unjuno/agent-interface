import copy
import unittest

from research.integration.cli_v1_lineage_sidecar_gate_v1.sidecar import (
    dispatch_with_gate,
    seal_receipt,
    seal_sidecar,
)


class FakeAPI:
    def __init__(self):
        self.calls = 0

    def dispatch(self, *args, **kwargs):
        self.calls += 1
        return {"schema": "agent-interface/runtime-dispatch-result-v1", "status": "returned"}


def fixture():
    program = {
        "program_id": "lineage-audit-1",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "ops": [
            {"op": "pointer_move", "x": 120, "y": 80},
            {"op": "release_all"},
        ],
    }
    receipt = seal_receipt({
        "receipt_id": "r1",
        "role": "ADMISSION_DEPENDENCY",
        "currentness": "CURRENT",
        "point": [120, 80],
        "observation_seq": 7,
        "binding_revision": 3,
        "source_receipt_id": None,
    })
    return program, receipt, seal_sidecar(program, receipt)


class LineageGateTests(unittest.TestCase):
    def test_valid_lineage_delegates_once(self):
        program, receipt, sidecar = fixture()
        api = FakeAPI()
        row = dispatch_with_gate(api, program, receipt, sidecar, {"fixture": 1},
                                 current_observation_seq=7,
                                 current_binding_revision=3)
        self.assertEqual(row["status"], "delegated")
        self.assertEqual(api.calls, 1)

    def test_tampered_sidecar_refuses_before_dispatch(self):
        program, receipt, sidecar = fixture()
        api = FakeAPI()
        tampered = copy.deepcopy(sidecar)
        tampered["program_digest"] = "0" * 64
        row = dispatch_with_gate(api, program, receipt, tampered, {"fixture": 1},
                                 current_observation_seq=7,
                                 current_binding_revision=3)
        self.assertEqual(row["status"], "lineage_rejected")
        self.assertEqual(row["error"], "SIDECAR_DIGEST_MISMATCH")
        self.assertEqual(api.calls, 0)

    def test_program_source_mismatch_refuses_before_dispatch(self):
        program, receipt, sidecar = fixture()
        api = FakeAPI()
        changed = copy.deepcopy(program)
        changed["source"]["binding_revision"] = 4
        row = dispatch_with_gate(api, changed, receipt, sidecar, {"fixture": 1},
                                 current_observation_seq=7,
                                 current_binding_revision=3)
        self.assertEqual(row["status"], "lineage_rejected")
        self.assertEqual(row["error"], "PROGRAM_DIGEST_MISMATCH")
        self.assertEqual(api.calls, 0)


if __name__ == "__main__":
    unittest.main()
