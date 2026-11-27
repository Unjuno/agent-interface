"""One-shot characterization of duplicate cancel retention in the standard caller."""
import argparse
import asyncio
import hashlib
import json
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_owned_process import _fake_owner_factory, metadata


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


async def run_trial():
    source_paths = (
        "runtime/cli_v1/mcp_server.py",
        "runtime/cli_v1/mcp_guarded.py",
        "runtime/cli_v1/owned_guarded_session.py",
    )
    source_rev = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
    source_hashes = {path: sha256(path) for path in source_paths}
    trial = {"source_revision": source_rev, "source_sha256": source_hashes}

    with TemporaryDirectory(prefix="duplicate-cancel-retention-") as temp_dir:
        root = Path(temp_dir)
        server = create_server(
            {"app": 20}, root,
            session_mode="guarded-x11",
            guarded_process_identity=True,
            guarded_query_worker=True,
            guarded_owned_process=True,
            _guarded_owner_factory=_fake_owner_factory,
        )
        try:
            observed = metadata(await server.call_tool(
                "interface_guarded_observe", {}))
            minted = metadata(await server.call_tool(
                "interface_guarded_mint", {
                    "alias": "field",
                    "source_sequence": observed["source"]["sequence"],
                    "point": [8, 8],
                    "region_size": [12, 12],
                }))

            (root / "block-owner-io").write_text("block", encoding="utf-8")
            pending = metadata(await server.call_tool(
                "interface_guarded_input", {
                    "alias": "field",
                    "offset": minted["offset"],
                    "interaction": "keyboard",
                    "observe_after": False,
                    "wait_for_result_ms": 0,
                    "tail": [{"op": "key_chord", "keys": ["CTRL", "a"]}],
                }))
            if pending.get("status") != "pending":
                raise RuntimeError(f"expected pending input, got {pending!r}")

            entered_deadline = time.monotonic() + 3
            while (not (root / "owner-io-entered.json").exists()
                   and time.monotonic() < entered_deadline):
                await asyncio.sleep(0.005)
            if not (root / "owner-io-entered.json").exists():
                raise RuntimeError("Fake X owner did not enter blocked sync")
            held_state = json.loads(
                (root / "owner-io-entered.json").read_text(encoding="utf-8"))

            fence_receipt = {
                "status": "disconnected", "worker_retired": True,
                "elapsed_ms": 2.5,
            }
            release_receipt = {
                "status": "readback_verified",
                "release": {
                    "verified": True, "keys_down": [], "buttons_down": [],
                    "monotonic_ns": 12,
                },
            }
            with (
                patch(
                    "runtime.cli_v1.owned_guarded_session."
                    "wait_for_client_disconnect_supervised",
                    return_value=fence_receipt,
                ),
                patch(
                    "runtime.cli_v1.owned_guarded_session."
                    "OwnedGuardedSessionOwner._release_retired_owner_inputs",
                    return_value=release_receipt,
                ) as release_inputs,
            ):
                first_started_ns = time.monotonic_ns()
                first = metadata(await server.call_tool(
                    "interface_guarded_cancel", {"call_id": pending["call_id"]}))
                first_finished_ns = time.monotonic_ns()
                second_started_ns = time.monotonic_ns()
                second = metadata(await server.call_tool(
                    "interface_guarded_cancel", {"call_id": pending["call_id"]}))
                second_finished_ns = time.monotonic_ns()
                release_attempt_count = release_inputs.call_count

            terminal = None
            result_deadline = time.monotonic() + 3
            while time.monotonic() < result_deadline:
                terminal = metadata(await server.call_tool(
                    "interface_results", {
                        "call_id": pending["call_id"],
                        "include_image": False,
                    }))
                if terminal.get("status") != "pending":
                    break
                await asyncio.sleep(0.005)

            trial.update({
                "status": "trial_complete",
                "call_id": pending["call_id"],
                "initial_owner_keys_down": held_state,
                "first_cancel": first,
                "first_cancel_started_ns": first_started_ns,
                "first_cancel_finished_ns": first_finished_ns,
                "second_cancel": second,
                "second_cancel_started_ns": second_started_ns,
                "second_cancel_finished_ns": second_finished_ns,
                "release_attempt_count": release_attempt_count,
                "terminal_interface_results": terminal,
                "interpretation": {
                    "one_release_attempt": release_attempt_count == 1,
                    "stable_cancel_operation_id": (
                        first.get("cancellation_operation_id") is not None
                        and first.get("cancellation_operation_id")
                        == second.get("cancellation_operation_id")),
                    "separate_retained_cancellation": (
                        isinstance(terminal, dict)
                        and isinstance(terminal.get("cancellation"), dict)),
                },
            })
            return trial, root
        finally:
            (root / "resume-owner-io").write_text("resume", encoding="utf-8")
            await server.call_tool("interface_close", {})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    trial, _root = asyncio.run(run_trial())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trial, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "status": trial["status"],
        "release_attempt_count": trial["release_attempt_count"],
        "first_cancel_status": trial["first_cancel"].get("status"),
        "second_cancel_status": trial["second_cancel"].get("status"),
        "terminal_status": trial["terminal_interface_results"].get("status"),
        "interpretation": trial["interpretation"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
