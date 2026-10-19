"""Compose the standard guarded MCP owner with the offline Fake-X relay."""

import asyncio
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from Xlib import X

from research.integration.offline_proxy_reply_framing_20261019.fake_socket_relay import (
    FakeSocketRelay,
)
from research.integration.offline_proxy_reply_framing_20261019.proxy_candidate import (
    X11ProxyConnection,
)
from runtime.cli_v1.mcp_guarded import GuardedSessionOwner
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_process_identity import FakeX, metadata


ACTION_ID = "standard-mcp-fake-x-action"
KEYCODE = 2
REPLY_TIMEOUT_S = 8.0


class _Cleanup:
    def __init__(self):
        self.callbacks = []

    def addCleanup(self, callback, *args, **kwargs):
        self.callbacks.append((callback, args, kwargs))

    def doCleanups(self):
        while self.callbacks:
            callback, args, kwargs = self.callbacks.pop()
            callback(*args, **kwargs)


def _receive_exact(stream, count):
    received = bytearray()
    while len(received) < count:
        part = stream.recv(count - len(received))
        if not part:
            raise EOFError("Fake X upstream closed before a complete request")
        received.extend(part)
    return bytes(received)


def _setup_tracker(owner_pid):
    tracker = X11ProxyConnection("standard-mcp-input", owner_pid,
                                 owner_pid=owner_pid, action_id=ACTION_ID)
    tracker.feed_client(b"l\0\x0b\0\0\0\0\0\0\0\0\0")
    tracker.feed_server(b"\x01\0\x0b\0\0\0\0\0")
    name = b"XTEST"
    padded = name + b"\0" * ((-len(name)) % 4)
    tracker.feed_client(b"\x62\0\x04\0\x05\0\0\0" + padded)
    tracker.feed_server(b"\x01\0\x01\0\0\0\0\0\x01\xc8\0\0" + bytes(20))
    return tracker


def _fake_input_request(kind, code):
    event_type = 2 if kind == X.KeyPress else 3
    return bytes((0xC8, 2, 9, 0, event_type, code)) + bytes(30)


def _pointer_reply(sequence):
    return b"\x01\0" + sequence.to_bytes(2, "little") + bytes(28)


def _socket_owner_factory(targets, directory, display_name, options):
    """Use real MCP/bridge/owner code with Fake X bytes carried by the relay."""
    cleanup = _Cleanup()
    fake = FakeX(cleanup)
    root = Path(directory)
    backend = fake.backend
    backend.d.get_display_name = lambda: "fake-display"
    backend.d.display = SimpleNamespace(
        info=SimpleNamespace(resource_id_base=0x1200000))

    class FakeQueries:
        def read(self, operation, _xid):
            if operation == "focus":
                return True
            if operation == "process_identity":
                marker = root / "fake-process-generation"
                return marker.read_text(encoding="utf-8") if marker.exists() else "a" * 64
            raise ValueError(operation)

        def close(self):
            return None

    query_patcher = patch(
        "runtime.guarded_x11_v1.target_queries.X11TargetQueries",
        return_value=FakeQueries())
    query_patcher.start()
    cleanup.addCleanup(query_patcher.stop)

    client, relay_client = socket.socketpair()
    relay_upstream, upstream_socket = socket.socketpair()
    event_sender, relay_events = socket.socketpair()
    tracker = _setup_tracker(os.getpid())
    relay = FakeSocketRelay(
        tracker, relay_client, relay_upstream, relay_events,
        owner_pid=os.getpid(), action_id=ACTION_ID, keycode=KEYCODE,
        reply_timeout=REPLY_TIMEOUT_S, max_pending_bytes=4096)
    relay_thread = threading.Thread(target=relay.run, daemon=True)
    relay_thread.start()

    def write_record(name, value):
        temporary = root / (name + ".tmp")
        temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        temporary.replace(root / name)

    def serve_fake_upstream():
        try:
            press = _receive_exact(upstream_socket, 36)
            write_record("fake-x-accepted-press.json", {
                "action_id": ACTION_ID, "event": "KeyPress", "keycode": KEYCODE,
                "request_hex": press.hex(), "classification": "synthetic_fake_x_only"})
            write_record("fake-x-server-queue.json", {
                "connection": "retired_owner_connection",
                "event": "KeyPress", "keycode": KEYCODE,
                "state": "accepted_and_held_in_synthetic_queue",
                "protocol_order_is_modeled_not_observed": True})
            sync = _receive_exact(upstream_socket, 4)
            if sync != b"\x6a\0\x01\0":
                write_record("fake-x-upstream-error.json", {"sync_hex": sync.hex()})
                return
            deadline = time.monotonic() + 2.0
            while not relay._independent_event and time.monotonic() < deadline:
                time.sleep(0.001)
            if not relay._independent_event:
                write_record("fake-x-upstream-error.json", {"reason": "event_receipt_not_seen"})
                return
            upstream_socket.sendall(_pointer_reply(3))
        except (EOFError, OSError) as error:
            write_record("fake-x-upstream-error.json", {"error": type(error).__name__})

    upstream_thread = threading.Thread(target=serve_fake_upstream, daemon=True)
    upstream_thread.start()

    def synthetic_effect_observer():
        receipt_path = root / "fake-x-accepted-press.json"
        deadline = time.monotonic() + 3.0
        while not receipt_path.exists() and time.monotonic() < deadline:
            time.sleep(0.001)
        if not receipt_path.exists():
            return
        accepted = json.loads(receipt_path.read_text(encoding="utf-8"))
        write_record("synthetic-effect-receipt.json", {
            "source": "independent_fake_effect_observer",
            "action_id": accepted["action_id"], "event": accepted["event"],
            "keycode": accepted["keycode"], "task_success": None})
        event_sender.sendall(json.dumps({
            "action_id": ACTION_ID, "event": "KeyPress", "keycode": KEYCODE,
        }).encode("utf-8") + b"\n")

    observer_thread = threading.Thread(target=synthetic_effect_observer, daemon=True)
    observer_thread.start()

    def relay_monitor():
        deadline = time.monotonic() + REPLY_TIMEOUT_S - 0.25
        while relay._held_deadline is None and time.monotonic() < deadline:
            time.sleep(0.001)
        if relay._held_deadline is not None:
            write_record("held-reply.json", {
                "independently_observed": relay._independent_event,
                "held_reply_bytes": len(relay._held_reply),
                "release_state": "UNKNOWN", "task_success": None,
                "replay_enabled": False})

    monitor_thread = threading.Thread(target=relay_monitor, daemon=True)
    monitor_thread.start()

    def emit(_display, kind, code, **_kwargs):
        client.sendall(_fake_input_request(kind, code))
        fake.emissions.append((kind, code))
        if kind == X.KeyPress:
            fake.down.add(code)
        elif kind == X.KeyRelease:
            fake.down.discard(code)

    # FakeX installed this mock while patching _GuardedBackend. Keep its caller
    # interception, but route the request bytes through the local relay sockets.
    from runtime.backends.x11_v1 import backend as x11_backend_module
    x11_backend_module.xtest.fake_input.side_effect = emit

    def sync():
        if not (root / "block-owner-io").exists():
            return
        client.sendall(b"\x6a\0\x01\0")
        write_record("sync-wait.json", {"request": "GetPointerControl", "sequence": 3})
        response = client.recv(32)
        if len(response) != 32:
            raise OSError("Fake X relay retired before the held reply was delivered")

    backend.d.sync = sync
    owner = GuardedSessionOwner(targets, directory, display_name, **options)
    owner._owned_process_test_cleanup = cleanup
    owner._relay_test_handles = (client, upstream_socket)
    owner._relay_test_threads = (relay_thread, upstream_thread, observer_thread, monitor_thread)
    return owner


class StandardMCPRelayCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)

    async def _wait_for_file(self, path, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not path.exists():
            await asyncio.sleep(0.005)
        self.assertTrue(path.exists(), f"timed out waiting for {path.name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _preserve_records(self, destination, records):
        raw_root = os.environ.get("AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR")
        if not raw_root:
            return
        out = Path(raw_root)
        out.mkdir(parents=True, exist_ok=True)
        for source_name in ("fake-x-accepted-press.json", "fake-x-server-queue.json",
                            "fake-x-release-readback.json", "fake-x-late-down.json",
                            "synthetic-effect-receipt.json", "held-reply.json",
                            "sync-wait.json"):
            source = destination / source_name
            if source.exists():
                (out / source_name).write_bytes(source.read_bytes())
        safe = {
            "observation": {
                "status": records["observed"].get("status"),
                "process_generation": records["observed"]["source"]["pointer_binding"].get(
                    "process_generation"),
                "sequence": records["observed"]["source"].get("sequence"),
            },
            "mint": {"status": records["minted"].get("status")},
            "pending": {"status": records["pending"].get("status")},
            "cancel": {key: records["cancelled"].get(key) for key in (
                "owner_process_retired", "owner_client_disconnect",
                "owner_input_obligations", "owner_release_attempt", "release_confirmed",
                "cleanup_status", "task_success", "replay_allowed",
                "late_server_request_possible")},
            "timing": {
                "cancel_elapsed_ms": records["cancel_elapsed_ms"],
                "terminal_elapsed_ms": records["terminal_elapsed_ms"],
            },
            "synthetic_late_down": {
                "queue": json.loads((destination / "fake-x-server-queue.json").read_text(
                    encoding="utf-8")) if (destination / "fake-x-server-queue.json").exists()
                    else None,
                "release_readback": json.loads((destination / "fake-x-release-readback.json").read_text(
                    encoding="utf-8")) if (destination / "fake-x-release-readback.json").exists()
                    else None,
                "late_down": json.loads((destination / "fake-x-late-down.json").read_text(
                    encoding="utf-8")) if (destination / "fake-x-late-down.json").exists()
                    else None,
            },
            "terminal": {key: records["terminal"].get(key) for key in (
                "status", "release_confirmed", "cleanup_status", "task_success",
                "replay_allowed")},
        }
        (out / "standard-caller-result.json").write_text(
            json.dumps(safe, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    async def test_standard_owned_caller_holds_fake_x_reply_and_cancels_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {"app": 20}, root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_socket_owner_factory)
            try:
                observed = metadata(await server.call_tool("interface_guarded_observe", {}))
                self.assertEqual(observed["status"], "observed", observed)
                self.assertEqual(observed["source"]["pointer_binding"]["process_generation"], "a" * 64)
                minted = metadata(await server.call_tool("interface_guarded_mint", {
                    "alias": "field", "source_sequence": observed["source"]["sequence"],
                    "point": [8, 8], "region_size": [12, 12]}))
                self.assertEqual(minted["status"], "minted", minted)

                (root / "block-owner-io").write_text("arm", encoding="utf-8")
                pending = metadata(await server.call_tool("interface_guarded_input", {
                    "alias": "field", "offset": minted["offset"],
                    "interaction": "keyboard", "observe_after": False,
                    "wait_for_result_ms": 0, "tail": [{"op": "key_chord", "keys": ["a"]}]}))
                self.assertEqual(pending["status"], "pending", pending)

                accepted = await self._wait_for_file(root / "fake-x-accepted-press.json")
                effect = await self._wait_for_file(root / "synthetic-effect-receipt.json")
                held = await self._wait_for_file(root / "held-reply.json")
                self.assertEqual(accepted["classification"], "synthetic_fake_x_only")
                self.assertEqual(effect["source"], "independent_fake_effect_observer")
                self.assertEqual(effect["action_id"], ACTION_ID)
                self.assertEqual(effect["keycode"], KEYCODE)
                self.assertIsNone(effect["task_success"])
                self.assertTrue(held["independently_observed"], held)
                self.assertEqual(held["held_reply_bytes"], 32)
                self.assertEqual(held["release_state"], "UNKNOWN")
                self.assertFalse(held["replay_enabled"])

                fence = {"status": "unknown", "reason": "fake_x_only_no_server_disconnect_claim",
                         "worker_retired": True, "elapsed_ms": 1.0}
                cancel_started = time.monotonic()
                with patch(
                    "runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised",
                    return_value=fence):
                    cancelled = metadata(await server.call_tool("interface_guarded_cancel", {
                        "call_id": pending["call_id"]}))
                cancel_elapsed_ms = (time.monotonic() - cancel_started) * 1000

                self.assertLess(cancel_elapsed_ms, 3000, cancelled)
                self.assertTrue(cancelled["owner_process_retired"], cancelled)
                self.assertEqual(cancelled["owner_client_disconnect"], fence)
                self.assertEqual(cancelled["owner_input_obligations"], {
                    "keys": {"a": KEYCODE}, "buttons": []})
                self.assertEqual(cancelled["owner_release_attempt"]["status"], "not_attempted")
                self.assertFalse(cancelled["release_confirmed"])
                self.assertEqual(cancelled["cleanup_status"], "UNKNOWN")
                self.assertIsNone(cancelled["task_success"])
                self.assertFalse(cancelled["replay_allowed"])
                self.assertTrue(cancelled["late_server_request_possible"])

                deadline = time.monotonic() + 5.0
                terminal_started = time.monotonic()
                terminal = None
                while time.monotonic() < deadline:
                    terminal = metadata(await server.call_tool("interface_results", {
                        "call_id": pending["call_id"], "include_image": False}))
                    if terminal["status"] != "pending":
                        break
                    await asyncio.sleep(0.01)
                self.assertEqual(terminal["status"], "runtime_failed", terminal)
                terminal_elapsed_ms = (time.monotonic() - terminal_started) * 1000
                self.assertLess(terminal_elapsed_ms, 5000, terminal)
                self.assertFalse(terminal["release_confirmed"])
                self.assertEqual(terminal["cleanup_status"], "UNKNOWN")
                self.assertIsNone(terminal["task_success"])
                self.assertFalse(terminal["replay_allowed"])
                self._preserve_records(root, {
                    "observed": observed, "minted": minted, "pending": pending,
                    "cancelled": cancelled, "terminal": terminal,
                    "cancel_elapsed_ms": round(cancel_elapsed_ms, 3),
                    "terminal_elapsed_ms": round(terminal_elapsed_ms, 3)})
            finally:
                await server.call_tool("interface_close", {})

    async def test_standard_owned_caller_keeps_unknown_after_fake_late_down(self):
        """A modeled late old-connection press cannot become verified success."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {"app": 20}, root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_socket_owner_factory)
            try:
                observed = metadata(await server.call_tool("interface_guarded_observe", {}))
                self.assertEqual(observed["status"], "observed", observed)
                minted = metadata(await server.call_tool("interface_guarded_mint", {
                    "alias": "field", "source_sequence": observed["source"]["sequence"],
                    "point": [8, 8], "region_size": [12, 12]}))
                self.assertEqual(minted["status"], "minted", minted)

                (root / "block-owner-io").write_text("arm", encoding="utf-8")
                pending = metadata(await server.call_tool("interface_guarded_input", {
                    "alias": "field", "offset": minted["offset"],
                    "interaction": "keyboard", "observe_after": False,
                    "wait_for_result_ms": 0,
                    "tail": [{"op": "key_chord", "keys": ["a"]}]}))
                self.assertEqual(pending["status"], "pending", pending)
                await self._wait_for_file(root / "fake-x-accepted-press.json")
                effect = await self._wait_for_file(root / "synthetic-effect-receipt.json")
                held = await self._wait_for_file(root / "held-reply.json")
                queue = await self._wait_for_file(root / "fake-x-server-queue.json")
                self.assertIsNone(effect["task_success"])
                self.assertTrue(held["independently_observed"], held)
                self.assertEqual(held["held_reply_bytes"], 32)
                self.assertEqual(queue["state"], "accepted_and_held_in_synthetic_queue")

                fence = {"status": "disconnected", "reason": "injected_fake_transport_eof",
                         "worker_retired": True, "elapsed_ms": 1.0}
                release_state = {"down": [KEYCODE]}
                model_order = []
                release_result = {
                    "status": "readback_verified", "worker_retired": True,
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "monotonic_ns": 0},
                }

                def verified_fake_release(obligations):
                    self.assertEqual(obligations, {"keys": {"a": KEYCODE}, "buttons": []})
                    release_state["down"] = []
                    model_order.append("separate_release_readback")
                    release_receipt = {
                        "source": "injected_separate_fake_release_readback",
                        "keys_down": [], "buttons_down": [],
                        "event_index": len(model_order),
                        "monotonic_ns": time.monotonic_ns(),
                    }
                    (root / "fake-x-release-readback.json").write_text(
                        json.dumps(release_receipt, sort_keys=True), encoding="utf-8")
                    release_result["release"]["monotonic_ns"] = release_receipt["monotonic_ns"]
                    return release_result

                cancel_started = time.monotonic()
                with (patch(
                        "runtime.cli_v1.owned_guarded_session.wait_for_client_disconnect_supervised",
                        return_value=fence),
                      patch(
                        "runtime.cli_v1.owned_guarded_session.OwnedGuardedSessionOwner._release_retired_owner_inputs",
                        side_effect=verified_fake_release) as release_inputs):
                    cancelled = metadata(await server.call_tool("interface_guarded_cancel", {
                        "call_id": pending["call_id"]}))
                cancel_elapsed_ms = (time.monotonic() - cancel_started) * 1000
                release_inputs.assert_called_once()
                self.assertLess(cancel_elapsed_ms, 3000, cancelled)
                self.assertTrue(cancelled["owner_process_retired"], cancelled)
                self.assertEqual(cancelled["owner_client_disconnect"], fence)
                self.assertEqual(cancelled["owner_release_attempt"]["status"],
                                 "readback_verified")
                self.assertFalse(cancelled["release_confirmed"])
                self.assertEqual(cancelled["cleanup_status"], "UNKNOWN")
                self.assertIsNone(cancelled["task_success"])
                self.assertFalse(cancelled["replay_allowed"])
                self.assertTrue(cancelled["late_server_request_possible"])

                # This final delivery is deliberately injected into a synthetic
                # server queue after the separate readback. It is not a claim
                # about real X11 disconnect ordering.
                release_receipt = json.loads(
                    (root / "fake-x-release-readback.json").read_text(encoding="utf-8"))
                self.assertEqual(release_state["down"], [])
                model_order.append("late_old_request_delivery")
                release_state["down"].append(KEYCODE)
                late_down = {
                    "source": "synthetic_queued_old_connection_request",
                    "event": "KeyPress", "keycode": KEYCODE,
                    "modeled_after_release_readback": True,
                    "event_index": len(model_order),
                    "monotonic_ns": time.monotonic_ns(),
                    "keys_down_after_delivery": sorted(release_state["down"]),
                    "protocol_order_is_modeled_not_observed": True,
                }
                self.assertLess(release_receipt["event_index"], late_down["event_index"])
                self.assertEqual(model_order, [
                    "separate_release_readback", "late_old_request_delivery"])
                (root / "fake-x-late-down.json").write_text(
                    json.dumps(late_down, sort_keys=True), encoding="utf-8")
                self.assertEqual(release_state["down"], [KEYCODE])

                deadline = time.monotonic() + 5.0
                terminal_started = time.monotonic()
                terminal = None
                while time.monotonic() < deadline:
                    terminal = metadata(await server.call_tool("interface_results", {
                        "call_id": pending["call_id"], "include_image": False}))
                    if terminal["status"] != "pending":
                        break
                    await asyncio.sleep(0.01)
                self.assertEqual(terminal["status"], "runtime_failed", terminal)
                terminal_elapsed_ms = (time.monotonic() - terminal_started) * 1000
                self.assertLess(terminal_elapsed_ms, 5000, terminal)
                self.assertFalse(terminal["release_confirmed"])
                self.assertEqual(terminal["cleanup_status"], "UNKNOWN")
                self.assertIsNone(terminal["task_success"])
                self.assertFalse(terminal["replay_allowed"])
                self._preserve_records(root, {
                    "observed": observed, "minted": minted, "pending": pending,
                    "cancelled": cancelled, "terminal": terminal,
                    "cancel_elapsed_ms": round(cancel_elapsed_ms, 3),
                    "terminal_elapsed_ms": round(terminal_elapsed_ms, 3)})
            finally:
                await server.call_tool("interface_close", {})

    async def test_generation_change_refuses_before_any_relay_action(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            server = create_server(
                {"app": 20}, root, session_mode="guarded-x11",
                guarded_process_identity=True, guarded_query_worker=True,
                guarded_owned_process=True,
                _guarded_owner_factory=_socket_owner_factory)
            try:
                observed = metadata(await server.call_tool("interface_guarded_observe", {}))
                minted = metadata(await server.call_tool("interface_guarded_mint", {
                    "alias": "field", "source_sequence": observed["source"]["sequence"],
                    "point": [8, 8], "region_size": [12, 12]}))
                (root / "fake-process-generation").write_text("b" * 64, encoding="utf-8")
                refused = metadata(await server.call_tool("interface_guarded_input", {
                    "alias": "field", "offset": minted["offset"],
                    "interaction": "keyboard", "observe_after": False,
                    "tail": [{"op": "key_chord", "keys": ["a"]}]}))
                self.assertEqual(refused["status"], "refused", refused)
                self.assertFalse(refused["result"]["input_dispatched"])
                self.assertEqual(refused["result"]["guard_checks"][0]["reason"],
                                 "process_generation_changed_or_missing")
                self.assertIsNone(refused["task_success"])
                self.assertFalse(refused["replay_allowed"])
                self.assertFalse((root / "fake-x-accepted-press.json").exists())
                raw_root = os.environ.get("AGENT_INTERFACE_FAKE_X_COMPOSITION_RAW_DIR")
                if raw_root:
                    out = Path(raw_root)
                    out.mkdir(parents=True, exist_ok=True)
                    (out / "target-generation-refusal.json").write_text(
                        json.dumps({
                            "source_generation": observed["source"]["pointer_binding"].get(
                                "process_generation"),
                            "current_generation": "b" * 64,
                            "result": refused["result"],
                            "task_success": refused.get("task_success"),
                            "replay_allowed": refused.get("replay_allowed"),
                            "relay_press_seen": False,
                        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            finally:
                await server.call_tool("interface_close", {})


if __name__ == "__main__":
    unittest.main()
