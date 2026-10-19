"""Exercise real python-xlib XRes wire frames through a Fake X socket relay."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import struct
import threading
import unittest

from Xlib.ext import res

from research.integration.offline_proxy_reply_framing_20261019.fake_socket_relay import (
    FakeSocketRelay,
)
from research.integration.offline_proxy_reply_framing_20261019.proxy_candidate import (
    X11ProxyConnection,
)


OWNER_PID = 77
ACTION_ID = "xres-query-wire-r02"
WINDOW_XID = 20
OWNER_BASE = 0x01200000
OBSERVER_BASE = 0x03400000
SERVER_PID = 123


def _receive_exact(stream: socket.socket, count: int) -> bytes:
    received = bytearray()
    while len(received) < count:
        part = stream.recv(count - len(received))
        if not part:
            raise EOFError("Fake X socket closed before a full XRes frame")
        received.extend(part)
    return bytes(received)


def _tracker() -> X11ProxyConnection:
    tracker = X11ProxyConnection(
        "identity-connection", OWNER_PID, owner_pid=OWNER_PID,
        action_id=ACTION_ID)
    tracker.feed_client(b"l\0\x0b\0\0\0\0\0\0\0\0\0")
    tracker.feed_server(b"\x01\0\x0b\0\0\0\0\0")
    name = b"XTEST"
    padded = name + b"\0" * ((-len(name)) % 4)
    tracker.feed_client(b"\x62\0\x04\0\x05\0\0\0" + padded)
    tracker.feed_server(b"\x01\0\x01\0\0\0\0\0\x01\xc8\0\0" + bytes(20))
    return tracker


def _xres_reply(sequence: int, identities: list[tuple[int, int]]) -> bytes:
    values = b"".join(
        struct.pack("<IIII", client, res.LocalClientPIDMask, 4, pid)
        for client, pid in identities)
    header = struct.pack("<BBHII", 1, 0, sequence, len(values) // 4,
                         len(identities)) + bytes(20)
    return header + values


class XResQuerySocketTests(unittest.TestCase):
    def test_query_client_ids_wire_round_trip_through_fake_relay(self):
        request = res.QueryClientIds._request.to_binary(
            opcode=201,
            specs=[{"client": WINDOW_XID, "mask": res.LocalClientPIDMask}],
        )
        self.assertEqual(request, bytes((
            201, res.ResQueryClientIds, 4, 0,
            1, 0, 0, 0,
            WINDOW_XID, 0, 0, 0,
            res.LocalClientPIDMask, 0, 0, 0,
        )))

        app, relay_client = socket.socketpair()
        relay_upstream, fake_server = socket.socketpair()
        event_sender, relay_events = socket.socketpair()
        for stream in (app, fake_server):
            stream.settimeout(2)
        relay = FakeSocketRelay(
            _tracker(), relay_client, relay_upstream, relay_events,
            owner_pid=OWNER_PID, action_id=ACTION_ID, keycode=2,
            reply_timeout=0.15, max_pending_bytes=4096)
        relay_thread = threading.Thread(target=relay.run, daemon=True)
        relay_thread.start()
        server_errors: list[str] = []

        def answer_query() -> None:
            try:
                received = _receive_exact(fake_server, len(request))
                if received != request:
                    raise AssertionError("relay changed the QueryClientIds request")
                fake_server.sendall(_xres_reply(2, [(OWNER_BASE, SERVER_PID)]))
            except Exception as error:  # captured and reported on the test thread
                server_errors.append(f"{type(error).__name__}: {error}")

        server_thread = threading.Thread(target=answer_query, daemon=True)
        server_thread.start()
        receipt = None
        try:
            app.sendall(request)
            reply = _receive_exact(app, 48)
            server_thread.join(2)
            self.assertFalse(server_thread.is_alive(), "Fake X responder did not finish")
            self.assertEqual(server_errors, [])
            self.assertEqual(len(reply), 48)
            self.assertEqual(reply[:8], struct.pack("<BBHI", 1, 0, 2, 4))
            self.assertEqual(struct.unpack("<I", reply[8:12])[0], 1)
            parsed, remainder = res.ClientIdValue.parse_binary(reply[32:], None)
            self.assertEqual(remainder, b"")
            self.assertEqual(parsed.spec.client, OWNER_BASE)
            self.assertEqual(parsed.spec.mask, res.LocalClientPIDMask)
            self.assertEqual(parsed.value, [SERVER_PID])

            receipt = {
                "connection": "identity-connection",
                "owner_pid_model": OWNER_PID,
                "query_hex": request.hex(),
                "reply_hex": reply.hex(),
                "reply_sequence": 2,
                "requested_window_xid": WINDOW_XID,
                "returned_canonical_owner_base": parsed.spec.client,
                "server_pid_model": parsed.value[0],
                "task_success": None,
                "physical_release": False,
            }
        finally:
            for stream in (app, event_sender, fake_server):
                stream.close()
            relay_thread.join(2)
            self.assertFalse(relay_thread.is_alive(), "Fake X relay did not retire")
        terminal = relay.terminal_report
        self.assertIsNotNone(terminal, "Fake X relay has no terminal receipt")
        self.assertEqual(terminal.release_state, "UNKNOWN")
        self.assertIsNone(terminal.task_success)
        self.assertFalse(terminal.replay_enabled)
        self.assertEqual(terminal.held_reply_bytes, 0)
        receipt["relay_terminal"] = {
            "retirement_reason": terminal.retirement_reason,
            "release_state": terminal.release_state,
            "task_success": terminal.task_success,
            "replay_enabled": terminal.replay_enabled,
            "held_reply_bytes": terminal.held_reply_bytes,
        }
        raw_dir = os.environ.get("AGENT_INTERFACE_XRES_WIRE_RAW_DIR")
        if raw_dir:
            root = Path(raw_dir)
            root.mkdir(parents=True, exist_ok=True)
            (root / "wire-exchange.json").write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
