"""Exercise public MCP lifespan shutdown with a deliberately held cancel worker."""

import asyncio
import ctypes
import json
import platform
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory, metadata


async def run_probe():
    with tempfile.TemporaryDirectory(prefix="cancel-shutdown-probe-") as temp:
        root = Path(temp)
        server = create_server(
            {"app": 20}, root, session_mode="guarded-x11",
            guarded_process_identity=True, guarded_query_worker=True,
            guarded_owned_process=True, _guarded_owner_factory=_fake_owner_factory,
        )
        lifecycle = server._mcp_server.lifespan(server._mcp_server)
        await lifecycle.__aenter__()
        cancel_entered = threading.Event()
        release_cancel = threading.Event()
        owner_close_returned = threading.Event()
        shutdown_task = None
        result = {"python": platform.python_version(), "platform": platform.platform()}

        original_close = OwnedGuardedSessionOwner.close

        def observed_close(owner):
            value = original_close(owner)
            owner_close_returned.set()
            return value

        def held_cancel(_owner, call_id):
            cancel_entered.set()
            if not release_cancel.wait(30):
                raise TimeoutError("probe cancel gate was not released")
            return {
                "status": "cancel_unconfirmed", "call_id": call_id,
                "release_confirmed": False, "cleanup_status": "UNKNOWN",
                "task_success": None, "replay_allowed": False,
            }

        try:
            with (patch.object(OwnedGuardedSessionOwner, "close", observed_close),
                  patch.object(OwnedGuardedSessionOwner, "cancel_guarded", held_cancel)):
                observed = metadata(await server.call_tool("interface_guarded_observe", {}))
                minted = metadata(await server.call_tool("interface_guarded_mint", {
                    "alias": "field", "source_sequence": observed["source"]["sequence"],
                    "point": [8, 8], "region_size": [12, 12],
                }))
                (root / "block-owner-io").write_text("block", encoding="utf-8")
                action = metadata(await server.call_tool("interface_guarded_input", {
                    "alias": "field", "offset": minted["offset"],
                    "interaction": "keyboard", "observe_after": False,
                    "wait_for_result_ms": 0,
                    "tail": [{"op": "key_chord", "keys": ["CTRL", "a"]}],
                }))
                result["action_status"] = action["status"]
                deadline = time.monotonic() + 4
                while not (root / "owner-io-entered.json").exists() and time.monotonic() < deadline:
                    await asyncio.sleep(0.005)
                result["blocked_owner_entered"] = (root / "owner-io-entered.json").exists()

                cancel_started = time.monotonic()
                cancel = metadata(await server.call_tool("interface_guarded_cancel", {
                    "call_id": action["call_id"],
                }))
                result["cancel_status"] = cancel.get("status")
                result["cancel_operation_id"] = cancel.get("operation_id")
                result["cancel_worker_entered"] = cancel_entered.is_set()
                result["cancel_return_elapsed_ms"] = round(
                    (time.monotonic() - cancel_started) * 1000, 3
                )

                shutdown_started = time.monotonic()
                shutdown_task = asyncio.create_task(lifecycle.__aexit__(None, None, None))
                close_seen = await asyncio.to_thread(owner_close_returned.wait, 10)
                result["owner_close_returned"] = close_seen
                if close_seen:
                    await asyncio.sleep(0.5)
                result["shutdown_done_while_cancel_held"] = shutdown_task.done()
                result["shutdown_elapsed_until_observation_ms"] = round(
                    (time.monotonic() - shutdown_started) * 1000, 3
                )

                release_cancel.set()
                (root / "resume-owner-io").write_text("resume", encoding="utf-8")
                await asyncio.wait_for(shutdown_task, timeout=5)
                result["shutdown_done_after_cancel_release"] = shutdown_task.done()
                result["final_call_record"] = metadata(await server.call_tool(
                    "interface_results", {"call_id": action["call_id"], "include_image": False}
                ))
                result["initial_blocked_input_state"] = json.loads(
                    (root / "owner-io-entered.json").read_text(encoding="utf-8")
                )
                owner_pid = result["final_call_record"].get("session", {}).get(
                    "owner_process", {}).get("pid")
                result["owner_pid_after_shutdown"] = owner_pid
                if platform.system() == "Windows" and isinstance(owner_pid, int):
                    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                    process = kernel32.OpenProcess(0x1000, False, owner_pid)
                    if not process:
                        result["owner_pid_readback"] = {
                            "status": "not_openable", "winerror": ctypes.get_last_error()
                        }
                    else:
                        exit_code = ctypes.c_ulong()
                        ok = kernel32.GetExitCodeProcess(process, ctypes.byref(exit_code))
                        kernel32.CloseHandle(process)
                        result["owner_pid_readback"] = (
                            {"status": "alive", "exit_code": exit_code.value}
                            if ok and exit_code.value == 259 else
                            {"status": "exited", "exit_code": exit_code.value}
                            if ok else
                            {"status": "read_error", "winerror": ctypes.get_last_error()}
                        )
        finally:
            release_cancel.set()
            (root / "resume-owner-io").write_text("resume", encoding="utf-8")
            if shutdown_task is None:
                await lifecycle.__aexit__(None, None, None)

        print(json.dumps(result, sort_keys=True, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(run_probe())
