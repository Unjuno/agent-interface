import unittest
from tempfile import TemporaryDirectory

import runtime.cli_v1.test_mcp_supervised_win32 as fixtures
from runtime.cli_v1.supervised_win32_compiled import _terminal


class SupervisedIdentityTests(unittest.TestCase):
    def row(self):
        call, operation, generation = "a" * 32, "c" * 32, "b" * 64
        return {
            "status": "returned", "call_id": call, "operation_id": operation,
            "target_generation": generation, "input_dispatched": True,
            "operation_invoked": True, "result": {"status": "completed"},
            "supervision": {"call_id": call, "action": {
                "status": "completed", "operation_id": operation,
                "target_generation": generation, "release_confirmed": True,
                "completion_custody": {"release_confirmed": True,
                    "completion_readback_outcome": "verified"}}}}

    def terminal(self, row):
        return _terminal(row, "move", expected_call_id="a" * 32,
                         expected_generation="b" * 64)

    def test_matching_supervised_receipt_completes(self):
        result = self.terminal(self.row())
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["release"]["verified"])

    def test_recovered_action_does_not_complete_conflicting_result(self):
        row = self.row()
        row["supervision"]["action"]["status"] = "recovered"
        result = self.terminal(row)
        self.assertEqual(result["status"], "uncertain")
        self.assertTrue(result["release"]["verified"])

    def test_mismatch_or_missing_identity_cannot_confirm_release(self):
        mutations = ("call", "operation", "generation", "missing_call",
                     "missing_operation", "missing_generation", "action_status")
        for mutation in mutations:
            row = self.row()
            action = row["supervision"]["action"]
            if mutation == "call":
                row["supervision"]["call_id"] = "f" * 32
            elif mutation == "operation":
                action["operation_id"] = "f" * 32
            elif mutation == "generation":
                action["target_generation"] = "f" * 64
            elif mutation == "missing_call":
                del row["supervision"]["call_id"]
            elif mutation == "missing_operation":
                del action["operation_id"]
            elif mutation == "missing_generation":
                del action["target_generation"]
            else:
                action["status"] = "unknown"
            with self.subTest(mutation=mutation):
                result = self.terminal(row)
                self.assertEqual(result["status"], "uncertain")
                self.assertFalse(result["release"]["verified"])


class PublicSupervisedEnvelopeTests(unittest.IsolatedAsyncioTestCase):
    async def test_fake_public_dispatch_is_accepted(self):
        fixture = fixtures.SupervisedWin32MCPTests()
        owner, producer, _ = fixture.make_components()
        with TemporaryDirectory() as root:
            server = fixture.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": fixture.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1, "wait_for_result_ms": 5000})
            row = fixture.row(reply)
            result = _terminal(row, "move", expected_call_id=row["call_id"],
                               expected_generation=row["target_generation"])
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["release"]["verified"])
            await server.call_tool("interface_close", {})
