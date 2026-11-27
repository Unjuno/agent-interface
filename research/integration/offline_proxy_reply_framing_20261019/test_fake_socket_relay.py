"""Socket-level tests for the offline-only fake X11 relay."""

from __future__ import annotations

import json
import select
import socket
import threading
import time
import unittest

from .proxy_candidate import X11ProxyConnection
from .fake_socket_relay import FakeSocketRelay


def setup_tracker():
    tracker = X11ProxyConnection("input-connection", 77, owner_pid=77,
                                 action_id="action-1")
    tracker.feed_client(b"l\0\x0b\0\0\0\0\0\0\0\0\0")
    tracker.feed_server(b"\x01\0\x0b\0\0\0\0\0")
    name = b"XTEST"
    padded = name + b"\0" * ((-len(name)) % 4)
    tracker.feed_client(b"\x62\0\x04\0\x05\0\0\0" + padded)
    tracker.feed_server(b"\x01\0\x01\0\0\0\0\0\x01\xc8\0\0" + bytes(20))
    return tracker


def target_requests():
    press = b"\xc8\x02\x09\0\x02\x26" + bytes(30)
    sync = b"\x6a\0\x01\0"
    return press + sync, 3


def reply(sequence: int) -> bytes:
    return b"\x01\0" + sequence.to_bytes(2, "little") + bytes(28)


class FakeSocketRelayTests(unittest.TestCase):
    def setUp(self):
        self.client, self.relay_client = socket.socketpair()
        self.relay_upstream, self.upstream = socket.socketpair()
        self.event_sender, self.relay_events = socket.socketpair()
        self.relay = FakeSocketRelay(
            setup_tracker(), self.relay_client, self.relay_upstream,
            self.relay_events, owner_pid=77, action_id="action-1", keycode=38,
            reply_timeout=0.15, max_pending_bytes=1024)
        self.thread = threading.Thread(target=self.relay.run, daemon=True)
        self.thread.start()

    def tearDown(self):
        for sock in (self.client, self.relay_client, self.relay_upstream,
                     self.upstream, self.event_sender, self.relay_events):
            try:
                sock.close()
            except OSError:
                pass
        self.thread.join(timeout=1)

    def receive_exact(self, sock, expected):
        sock.settimeout(1)
        received = bytearray()
        while len(received) < len(expected):
            part = sock.recv(len(expected) - len(received))
            if not part:
                break
            received.extend(part)
        self.assertEqual(bytes(received), expected)

    def test_unmatched_sync_reply_is_forwarded_without_event_receipt(self):
        request = b"\x6a\0\x01\0"
        self.client.sendall(request)
        self.receive_exact(self.upstream, request)
        response = reply(2)
        self.upstream.sendall(response)
        self.receive_exact(self.client, response)
        self.assertFalse(self.relay.terminal_report)

    def test_event_gated_reply_retires_bounded_as_unknown_without_success(self):
        requests, target_sequence = target_requests()
        self.client.sendall(requests)
        self.receive_exact(self.upstream, requests)
        self.event_sender.sendall(json.dumps({
            "action_id": "action-1", "event": "KeyPress", "keycode": 38
        }).encode() + b"\n")
        deadline = time.monotonic() + 1
        while not self.relay._independent_event and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertTrue(self.relay._independent_event)
        response = reply(target_sequence)
        self.upstream.sendall(response)
        started = time.monotonic()
        self.thread.join(timeout=1)
        elapsed = time.monotonic() - started
        self.assertFalse(self.thread.is_alive(), "held reply did not retire by deadline")
        report = self.relay.terminal_report
        self.assertEqual(report.retirement_reason, "held_reply_deadline")
        self.assertEqual(report.release_state, "UNKNOWN")
        self.assertIsNone(report.task_success)
        self.assertFalse(report.replay_enabled)
        self.assertLess(elapsed, 1)
        readable, _, _ = select.select([self.client], [], [], 0)
        self.assertTrue(readable, "relay should close the client stream on retirement")
        self.assertEqual(self.client.recv(1), b"", "held reply must not be delivered")

    def test_parser_error_fails_open_without_changing_bytes(self):
        malformed = b"\xff\0\0\0"
        self.client.sendall(malformed)
        self.receive_exact(self.upstream, malformed)
        self.assertFalse(self.relay.terminal_report)

    def test_upstream_disconnect_retires_held_reply_as_unknown(self):
        requests, target_sequence = target_requests()
        self.client.sendall(requests)
        self.receive_exact(self.upstream, requests)
        self.event_sender.sendall(json.dumps({
            "action_id": "action-1", "event": "KeyPress", "keycode": 38
        }).encode() + b"\n")
        deadline = time.monotonic() + 1
        while not self.relay._independent_event and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertTrue(self.relay._independent_event)
        self.upstream.sendall(reply(target_sequence))
        time.sleep(0.02)
        self.upstream.close()
        self.thread.join(timeout=1)
        self.assertFalse(self.thread.is_alive(), "upstream EOF did not retire the relay")
        report = self.relay.terminal_report
        self.assertEqual(report.retirement_reason, "upstream_eof")
        self.assertEqual(report.release_state, "UNKNOWN")
        self.assertEqual(report.held_reply_bytes, 32)
        self.assertIsNone(report.task_success)

    def test_later_server_frames_do_not_overtake_held_reply(self):
        requests, target_sequence = target_requests()
        self.client.sendall(requests)
        self.receive_exact(self.upstream, requests)
        self.event_sender.sendall(json.dumps({
            "action_id": "action-1", "event": "KeyPress", "keycode": 38
        }).encode() + b"\n")
        deadline = time.monotonic() + 1
        while not self.relay._independent_event and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertTrue(self.relay._independent_event)
        later_event = b"\x02\0\x03\0" + bytes(28)
        self.upstream.sendall(reply(target_sequence) + later_event)
        self.thread.join(timeout=1)
        self.assertFalse(self.thread.is_alive())
        self.assertEqual(self.relay.terminal_report.retirement_reason,
                         "held_reply_deadline")
        self.assertEqual(self.relay.terminal_report.held_reply_bytes, 64)
        self.assertEqual(self.client.recv(1), b"",
                         "later server bytes must not pass a withheld reply")

    def test_server_parser_error_cannot_overtake_held_reply(self):
        requests, target_sequence = target_requests()
        self.client.sendall(requests)
        self.receive_exact(self.upstream, requests)
        self.event_sender.sendall(json.dumps({
            "action_id": "action-1", "event": "KeyPress", "keycode": 38
        }).encode() + b"\n")
        deadline = time.monotonic() + 1
        while not self.relay._independent_event and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertTrue(self.relay._independent_event)
        malformed = b"\x01\0\x04\0\xff\xff\xff\xff" + bytes(24)
        self.upstream.sendall(reply(target_sequence))
        deadline = time.monotonic() + 1
        while self.relay._held_deadline is None and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertIsNotNone(self.relay._held_deadline)
        self.upstream.sendall(malformed)
        self.thread.join(timeout=1)
        self.assertFalse(self.thread.is_alive())
        self.assertEqual(self.relay.terminal_report.retirement_reason,
                         "held_reply_deadline")
        self.assertEqual(self.relay.terminal_report.held_reply_bytes, 64)
        self.assertEqual(self.client.recv(1), b"",
                         "parser fallback must not violate stream order")

    def test_downstream_backpressure_retires_at_bounded_queue(self):
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
        frame = b"\x02\0\0\0" + bytes(28)
        payload = frame * 65536
        self.upstream.settimeout(1)
        try:
            self.upstream.sendall(payload)
        except (BrokenPipeError, ConnectionResetError, OSError, socket.timeout):
            pass
        self.thread.join(timeout=1)
        self.assertFalse(self.thread.is_alive(), "relay did not retire under backpressure")
        self.assertEqual(self.relay.terminal_report.retirement_reason,
                         "backpressure_limit")
        self.assertEqual(self.relay.terminal_report.release_state, "UNKNOWN")
        self.assertIsNone(self.relay.terminal_report.task_success)

    def test_large_valid_stream_is_not_misclassified_when_client_drains(self):
        frame = b"\x02\0\0\0" + bytes(28)
        payload = frame * 2048
        self.client.settimeout(1)
        received = bytearray()

        def drain_client():
            while len(received) < len(payload):
                part = self.client.recv(min(4096, len(payload) - len(received)))
                if not part:
                    return
                received.extend(part)

        drainer = threading.Thread(target=drain_client, daemon=True)
        drainer.start()
        self.upstream.sendall(payload)
        drainer.join(timeout=1)
        self.assertFalse(drainer.is_alive(), "client did not receive the full stream")
        self.assertEqual(bytes(received), payload)
        self.assertIsNone(self.relay.terminal_report)


if __name__ == "__main__":
    unittest.main()
