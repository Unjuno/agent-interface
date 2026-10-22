"""Tests for the independent RPC gate adjudicator."""

import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    "a04_audit_result", Path(__file__).with_name("audit_result.py")
)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(AUDIT)


class RpcGateTests(unittest.TestCase):
    def test_structured_error_is_rejection(self):
        self.assertEqual(
            AUDIT._rpc_gate_label([{"result": {}}, {"error": {"code": -1}}], False, []),
            "RPC_REJECTED",
        )

    def test_missing_or_malformed_reply_is_unverifiable(self):
        self.assertEqual(AUDIT._rpc_gate_label([{"result": {}}], True, ["inProgress"]), "UNVERIFIABLE")
        self.assertEqual(AUDIT._rpc_gate_label([{}, {"result": {}}], True, ["inProgress"]*2), "UNVERIFIABLE")

    def test_wrong_turn_identity_or_status_is_unverifiable(self):
        replies = [{"result": {}}, {"result": {}}]
        self.assertEqual(AUDIT._rpc_gate_label(replies, False, ["inProgress"]*2), "UNVERIFIABLE")
        self.assertEqual(AUDIT._rpc_gate_label(replies, True, ["complete", "inProgress"]), "UNVERIFIABLE")

    def test_valid_acknowledgements_leave_content_label_to_raw_reconstruction(self):
        self.assertIsNone(
            AUDIT._rpc_gate_label([{"result": {}}, {"result": {}}], True, ["inProgress"]*2)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
