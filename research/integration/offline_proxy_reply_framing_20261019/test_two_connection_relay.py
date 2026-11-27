"""Two-connection FakeSocketRelay composition; synthetic sockets only."""

import json
import select
import socket
import threading
import time
import unittest

from .fake_socket_relay import FakeSocketRelay
from .proxy_candidate import X11ProxyConnection
from .test_fake_socket_relay import reply, target_requests
from .test_proxy_candidate import query_extension, query_extension_reply, setup_request, setup_success


def connected_tracker(connection_id):
    tracker = X11ProxyConnection(connection_id, 77, owner_pid=77,
                                 action_id="action-1")
    tracker.feed_client(setup_request())
    tracker.feed_server(setup_success())
    tracker.feed_client(query_extension())
    tracker.feed_server(query_extension_reply(1, 200))
    return tracker


def identity_tracker():
    tracker = connected_tracker("identity-connection")
    tracker.feed_client(b"\x7f\0\x01\0")
    record = tracker.feed_client(b"\x6a\0\x01\0")[0]
    return tracker, record


class TwoConnectionRelayTests(unittest.TestCase):
    def test_identity_reply_forwarded_while_same_pid_input_reply_is_held(self):
        input_client, input_relay_client = socket.socketpair()
        input_relay_upstream, input_upstream = socket.socketpair()
        input_event_sender, input_relay_events = socket.socketpair()
        input_relay = FakeSocketRelay(
            connected_tracker("input-connection"), input_relay_client,
            input_relay_upstream, input_relay_events, owner_pid=77,
            action_id="action-1", keycode=38, reply_timeout=0.15,
            max_pending_bytes=1024)
        input_thread = threading.Thread(target=input_relay.run, daemon=True)
        input_thread.start()

        identity_client, identity_relay_client = socket.socketpair()
        identity_relay_upstream, identity_upstream = socket.socketpair()
        identity_event_sender, identity_relay_events = socket.socketpair()
        tracker, identity_record = identity_tracker()
        identity_relay = FakeSocketRelay(
            tracker, identity_relay_client, identity_relay_upstream,
            identity_relay_events, owner_pid=77, action_id="action-1",
            keycode=38, reply_timeout=0.15, max_pending_bytes=1024)
        identity_thread = threading.Thread(target=identity_relay.run, daemon=True)
        identity_thread.start()
        sockets = (input_client, input_relay_client, input_relay_upstream,
                   input_upstream, input_event_sender, input_relay_events,
                   identity_client, identity_relay_client,
                   identity_relay_upstream, identity_upstream,
                   identity_event_sender, identity_relay_events)
        try:
            self.assertEqual(identity_record.sequence, 3)
            requests, input_sequence = target_requests()
            self.assertEqual(input_sequence, identity_record.sequence)

            # This same-PID pre-press identity-channel reply uses the same
            # connection-local serial as the eventual input-channel target.
            identity_request = b"\x7f\0\x01\0\x6a\0\x01\0"
            identity_client.sendall(identity_request)
            identity_upstream.settimeout(1)
            self.assertEqual(identity_upstream.recv(len(identity_request)), identity_request)
            identity_response = reply(identity_record.sequence)
            identity_upstream.sendall(identity_response)
            identity_client.settimeout(1)
            self.assertEqual(identity_client.recv(32), identity_response)
            self.assertIsNone(identity_relay.terminal_report)

            input_client.sendall(requests)
            input_upstream.settimeout(1)
            self.assertEqual(input_upstream.recv(len(requests)), requests)
            input_event_sender.sendall(json.dumps({
                "action_id": "action-1", "event": "KeyPress", "keycode": 38
            }).encode() + b"\n")
            deadline = time.monotonic() + 1
            while not input_relay._independent_event and time.monotonic() < deadline:
                time.sleep(0.001)
            self.assertTrue(input_relay._independent_event)
            input_upstream.sendall(reply(input_sequence))
            input_thread.join(timeout=1)
            self.assertFalse(input_thread.is_alive())
            report = input_relay.terminal_report
            self.assertEqual(report.retirement_reason, "held_reply_deadline")
            self.assertEqual(report.held_reply_bytes, 32)
            self.assertEqual(report.release_state, "UNKNOWN")
            self.assertIsNone(report.task_success)
            self.assertFalse(report.replay_enabled)
            readable, _, _ = select.select([input_client], [], [], 0)
            self.assertTrue(readable)
            self.assertEqual(input_client.recv(1), b"")
        finally:
            for sock in sockets:
                try:
                    sock.close()
                except OSError:
                    pass
            input_thread.join(timeout=1)
            identity_thread.join(timeout=1)


if __name__ == "__main__":
    unittest.main()
