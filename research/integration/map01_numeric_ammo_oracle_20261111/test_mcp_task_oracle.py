import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
import asyncio

from PIL import Image

from mcp_task_oracle import CapturedFrame, make_map01_task_oracle
from runtime.cli_v1.supervised_win32_compiled import _task_oracle_evidence
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.cli_v1.test_mcp_supervised_win32 import (
    FakeProcess, HeldProducerFactory, RecoveringFakeSupervisor,
)
from runtime.guarded_win32_v1.operation_owner import OperationOwner


HERE = Path(__file__).resolve().parent
CALL = "b94be097d11f4034a02d08fd161683a8"
OPERATION = "88565e72a7fa48d5be98d176e2771705"
GENERATION = "fd4f50fc7f3a0a65ae2f8194725441484a20125e6c17ce8feb7faa53ac753666"
ORACLE = "d4dda6530c47322b6f1d5feccfce4489"


class PublicHarness:
    @staticmethod
    def valid_program() -> dict:
        generation = "a" * 64
        return {
            "schema": "agent-interface/program-v1",
            "program_id": "numeric-ammo-recovered-oracle",
            "source": {"observation_seq": 1, "binding_revision": 1,
                       "target_generations": {"fixture": generation}},
            "authority": {"lease_id": "numeric-ammo-oracle-lease",
                          "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                    {"op": "key_chord", "keys": ["CTRL", "S"]},
                    {"op": "release_all"}],
        }

    @staticmethod
    def row(reply) -> dict:
        row = json.loads(reply.content[0].text)
        receipt = row.get("receipt")
        if isinstance(receipt, dict):
            source = receipt.get("source")
            if isinstance(source, dict) and isinstance(source.get("raw_report"), dict):
                return source["raw_report"]
        return row


def full_frame(patch_path: Path) -> bytes:
    image = Image.new("RGB", (1520, 825), (0, 0, 0))
    with Image.open(patch_path) as patch:
        image.paste(patch.convert("RGB"), (470, 778))
    from io import BytesIO
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def public_verify_task_reply(receipt: dict, task_success: bool) -> dict:
    return {
        "status": "verified",
        "call_id": CALL,
        "task_success": task_success,
        "operation_invoked": False,
        "input_dispatched": False,
        "replay_allowed": False,
        "scope": "supervised_win32",
        "task_effect": {
            "status": "verified",
            "task_success": task_success,
            "receipt": receipt,
            "requested_monotonic_ns": 1_000_000_000,
            "receipt_received_monotonic_ns": 1_000_000_040,
        },
    }


class Map01McpTaskOracleTests(unittest.TestCase):
    def run_oracle(self, after_patch: Path, *, action_generation=GENERATION,
                   readback_generation=GENERATION,
                   release=True, action_operation=OPERATION,
                   capture_times=(1_000_000_010, 1_000_000_020)):
        with tempfile.TemporaryDirectory() as temp:
            trial = Path(temp)
            before_path = trial / "before.png"
            before_path.write_bytes(full_frame(HERE / "ammo_50_template.png"))
            evidence = {
                "call_id": CALL,
                "operation_id": OPERATION,
                "target_generation": GENERATION,
                "target": "map01",
                "before_png": str(before_path),
                "before_png_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
                "release_readback": {
                    "same_generation": True,
                    "target_generation_before": readback_generation,
                    "target_generation_after": readback_generation,
                    "mouse_left_high_bit_down": False,
                },
                "screen_region": [0, 0, 1520, 825],
                "frame": "screen_physical_px",
            }
            (trial / "oracle-input.json").write_text(json.dumps(evidence), encoding="utf-8")
            png_bytes = full_frame(after_patch)
            capture_calls = []

            def capture(target, hwnd, received):
                capture_calls.append((target, hwnd, received["call_id"]))
                return CapturedFrame(
                    png_bytes=png_bytes,
                    generation_before=GENERATION,
                    generation_after=GENERATION,
                    geometry={"x": 0, "y": 0, "width": 1520, "height": 825},
                    started_ns=capture_times[0],
                    ended_ns=capture_times[1],
                )

            oracle = make_map01_task_oracle(
                trial_dir=trial, template_dir=HERE,
                target_windows={"map01": 1234}, oracle_id=ORACLE,
                capture=capture, clock_ns=iter((1_000_000_000, 1_000_000_025,
                                              1_000_000_030)).__next__)
            action = {"call_id": CALL, "operation_id": action_operation,
                      "target_generation": action_generation, "status": "recovered",
                      "release_confirmed": release}
            receipt = oracle(action)
            output = json.loads((trial / "oracle-receipt.json").read_text())
            transition_path = trial / "ammo-transition.json"
            transition = json.loads(transition_path.read_text()) if transition_path.exists() else None
            return receipt, capture_calls, transition, output["reason"]

    def test_mcp_callback_returns_success_only_for_ammo_50_to_49(self):
        receipt, calls, transition, reason = self.run_oracle(HERE / "ammo_49_template.png")
        self.assertEqual(receipt["outcome"], "success", reason)
        self.assertEqual(reason, "ammo_50_to_49")
        self.assertEqual(receipt["call_id"], CALL)
        self.assertEqual(receipt["operation_id"], OPERATION)
        self.assertEqual(receipt["target_generation"], GENERATION)
        self.assertEqual(len(calls), 1)
        self.assertEqual(transition["before"]["value"], "50")
        self.assertEqual(transition["after"]["value"], "49")
        caller_view = _task_oracle_evidence(public_verify_task_reply(receipt, True),
            CALL, GENERATION, OPERATION, 1_000_000_000, 2_000_000_000)
        self.assertTrue(caller_view["valid"], caller_view)
        self.assertTrue(caller_view["task_success"])

    def test_capture_time_must_be_inside_verification_window(self):
        for times in ((1, 2), (9_000_000_000, 9_000_000_001),
                      (1_000_000_020, 1_000_000_010), (True, 1_000_000_020),
                      (None, 1_000_000_020), (1_000_000_010, 'invalid'),
                      (1_000_000_010.0, 1_000_000_020)):
            with self.subTest(times=times):
                receipt, _, _, reason = self.run_oracle(
                    HERE / 'ammo_49_template.png', capture_times=times)
                self.assertEqual(receipt['outcome'], 'unknown')
                self.assertEqual(reason, 'capture_outside_verification_window')

    def test_mcp_callback_returns_failure_for_r96_palette_only_change(self):
        receipt, calls, transition, reason = self.run_oracle(HERE / "r96_ammo_after_50_palette.png")
        self.assertEqual(receipt["outcome"], "failure", reason)
        self.assertEqual(reason, "ammo_remained_50")
        self.assertEqual(len(calls), 1)
        self.assertEqual(transition["after"]["value"], "50")
        caller_view = _task_oracle_evidence(public_verify_task_reply(receipt, False),
            CALL, GENERATION, OPERATION, 1_000_000_000, 2_000_000_000)
        self.assertTrue(caller_view["valid"], caller_view)
        self.assertFalse(caller_view["task_success"])

    def test_mcp_callback_refuses_unjoined_generation_without_capture(self):
        receipt, calls, _, reason = self.run_oracle(HERE / "ammo_49_template.png",
                                                    action_generation="f" * 64)
        self.assertEqual(receipt["outcome"], "unknown")
        self.assertEqual(reason, "action_identity_or_terminal_state_mismatch")
        self.assertEqual(calls, [])

    def test_mcp_callback_refuses_unverified_release_without_capture(self):
        receipt, calls, _, reason = self.run_oracle(HERE / "ammo_49_template.png", release=False)
        self.assertEqual(receipt["outcome"], "unknown")
        self.assertEqual(reason, "action_release_unverified")
        self.assertEqual(calls, [])

    def test_mcp_callback_refuses_wrong_operation_without_capture(self):
        receipt, calls, _, reason = self.run_oracle(HERE / "ammo_49_template.png",
                                                    action_operation="e" * 32)
        self.assertEqual(receipt["outcome"], "unknown")
        self.assertEqual(reason, "action_identity_or_terminal_state_mismatch")
        self.assertEqual(calls, [])

    def test_mcp_callback_refuses_release_readback_from_other_generation(self):
        receipt, calls, _, reason = self.run_oracle(
            HERE / "ammo_49_template.png", readback_generation="f" * 64)
        self.assertEqual(receipt["outcome"], "unknown")
        self.assertEqual(reason, "independent_release_readback_unverified")
        self.assertEqual(calls, [])


class RecoveredPublicMcpOracleTests(unittest.IsolatedAsyncioTestCase):
    async def run_recovered_oracle(self, after_patch: Path) -> dict:
        generation = "a" * 64
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: generation)
        producer = HeldProducerFactory(process, identity)
        helper = PublicHarness()

        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            trial = root_path / "trial"
            trial.mkdir()
            before_path = trial / "before.png"
            before_path.write_bytes(full_frame(HERE / "ammo_50_template.png"))
            capture_png = full_frame(after_patch)

            def capture(_target, _hwnd, _evidence):
                return CapturedFrame(capture_png, generation, generation,
                    {"x": 0, "y": 0, "width": 1520, "height": 825},
                    time.monotonic_ns(), time.monotonic_ns())

            callback = make_map01_task_oracle(
                trial_dir=trial, template_dir=HERE, target_windows={"fixture": 123},
                oracle_id="f" * 32, capture=capture)
            server = create_server({"fixture": 123}, root_path / "mcp-output",
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=callback)
            try:
                program = helper.valid_program()
                program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
                pending = helper.row(await server.call_tool("interface_dispatch", {
                    "program": program, "current_observation_seq": 1,
                    "current_binding_revision": 1, "wait_for_result_ms": 0}))
                self.assertEqual(pending["status"], "pending", pending)
                self.assertTrue(await asyncio.wait_for(
                    asyncio.to_thread(producer.started.wait, 1), 1))
                recovered = helper.row(await server.call_tool("interface_cancel", {
                    "call_id": pending["call_id"]}))
                self.assertEqual(recovered["status"], "recovered", recovered)
                deadline = time.monotonic() + 2
                while True:
                    retained = helper.row(await server.call_tool("interface_results", {
                        "call_id": pending["call_id"]}))
                    action = retained["action"]
                    if action["status"] != "running" and "program_actions_lower_bound" in action:
                        break
                    self.assertLess(time.monotonic(), deadline, retained)
                    await asyncio.sleep(0.01)
                self.assertEqual(action["status"], "recovered")
                evidence = {
                    "call_id": pending["call_id"],
                    "operation_id": action["operation_id"],
                    "target_generation": generation,
                    "target": "fixture",
                    "before_png": str(before_path),
                    "before_png_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
                    "release_readback": {"same_generation": True,
                                          "target_generation_before": generation,
                                          "target_generation_after": generation,
                                          "mouse_left_high_bit_down": False},
                    "screen_region": [0, 0, 1520, 825],
                    "frame": "screen_physical_px",
                }
                (trial / "oracle-input.json").write_text(json.dumps(evidence), encoding="utf-8")
                result = json.loads((await server.call_tool("interface_verify_task", {
                    "call_id": pending["call_id"], "wait_for_result_ms": 1000
                })).content[0].text)
                return result
            finally:
                await server.call_tool("interface_close", {})
                output_root = root_path / "mcp-output"
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    pending_writes = list(output_root.rglob("*.tmp"))
                    if not pending_writes:
                        break
                    await asyncio.sleep(0.01)
                self.assertEqual(list(output_root.rglob("*.tmp")), [],
                                 "MCP report writer did not reach a file-close boundary")

    async def test_recovered_public_action_accepts_numeric_positive_control(self):
        result = await self.run_recovered_oracle(HERE / "ammo_49_template.png")
        self.assertEqual(result["status"], "verified", result)
        self.assertTrue(result["task_success"], result)
        self.assertEqual(result["task_effect"]["receipt"]["outcome"], "success")
        self.assertFalse(result["replay_allowed"])

    async def test_recovered_public_action_rejects_palette_only_change(self):
        result = await self.run_recovered_oracle(HERE / "r96_ammo_after_50_palette.png")
        self.assertEqual(result["status"], "verified", result)
        self.assertFalse(result["task_success"], result)
        self.assertEqual(result["task_effect"]["receipt"]["outcome"], "failure")
        self.assertFalse(result["replay_allowed"])

if __name__ == "__main__":
    unittest.main()
