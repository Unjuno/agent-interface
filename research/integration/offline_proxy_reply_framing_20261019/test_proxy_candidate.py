"""Offline tests for X11 setup, request framing and XTEST reply correlation."""

from __future__ import annotations

import unittest

from .proxy_candidate import FrameError, X11ProxyConnection


def setup_request(byte_order: str = "little", auth_name: bytes = b"MIT-MAGIC-COOKIE-1",
                  auth_data: bytes = b"cookie") -> bytes:
    marker = b"l" if byte_order == "little" else b"B"
    pad = lambda value: value + bytes((-len(value)) % 4)
    return (marker + b"\0" + (11).to_bytes(2, byte_order)
            + (0).to_bytes(2, byte_order)
            + len(auth_name).to_bytes(2, byte_order)
            + len(auth_data).to_bytes(2, byte_order) + b"\0\0"
            + pad(auth_name) + pad(auth_data))


def setup_success(byte_order: str = "little") -> bytes:
    return b"\x01\0\x0b\0\x00\0\0\0"


def request(opcode: int, minor: int = 0, payload: bytes = b"",
            byte_order: str = "little") -> bytes:
    length = 4 + len(payload)
    if length % 4:
        payload += bytes((-length) % 4)
        length = 4 + len(payload)
    return bytes((opcode, minor)) + (length // 4).to_bytes(2, byte_order) + payload


def query_extension(name: bytes = b"XTEST", byte_order: str = "little") -> bytes:
    padded = name + bytes((-len(name)) % 4)
    return request(98, payload=(len(name).to_bytes(2, byte_order) + b"\0\0" + padded),
                   byte_order=byte_order)


def query_extension_reply(sequence: int, major_opcode: int,
                          byte_order: str = "little", *, present: bool = True) -> bytes:
    return (bytes((1, 0)) + sequence.to_bytes(2, byte_order) + bytes(4)
            + bytes((int(present), major_opcode, 0, 0)) + bytes(20))


def fake_input(major_opcode: int, event_type: int, keycode: int,
               byte_order: str = "little") -> bytes:
    payload = bytes((event_type, keycode)) + bytes(30)
    return request(major_opcode, 2, payload, byte_order)


def get_pointer_control(byte_order: str = "little") -> bytes:
    return request(106, byte_order=byte_order)


def reply(sequence: int, byte_order: str = "little") -> bytes:
    return bytes((1, 0)) + sequence.to_bytes(2, byte_order) + bytes(28)


class ProxyCandidateTests(unittest.TestCase):
    def connected(self, connection_id: str = "input", peer_pid: int = 24,
                  byte_order: str = "little") -> X11ProxyConnection:
        tracker = X11ProxyConnection(connection_id, peer_pid, owner_pid=24,
                                     action_id="action-1")
        self.assertEqual(tracker.feed_client(setup_request(byte_order)), ())
        self.assertEqual(tracker.feed_server(setup_success(byte_order)), ())
        return tracker

    def test_setup_and_query_extension_can_be_fragmented(self):
        tracker = X11ProxyConnection("input", 24, owner_pid=24, action_id="action-1")
        setup = setup_request("big")
        self.assertEqual(tracker.feed_client(setup[:7]), ())
        self.assertEqual(tracker.feed_client(setup[7:]), ())
        tracker.feed_server(setup_success("big"))
        query = query_extension(byte_order="big")
        records = tracker.feed_client(query[:3])
        self.assertEqual(records, ())
        records = tracker.feed_client(query[3:])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].sequence, 1)
        tracker.feed_server(query_extension_reply(1, 201, "big"))
        self.assertEqual(tracker.xtest_major_opcode, 201)

    def test_only_negotiated_xtest_press_binds_following_sync_reply(self):
        tracker = self.connected()
        tracker.feed_client(query_extension())
        tracker.feed_server(query_extension_reply(1, 200))
        press = tracker.feed_client(fake_input(200, 2, 38))[0]
        target = tracker.feed_client(get_pointer_control())[0]
        self.assertEqual(press.role, "xtest_key_press")
        self.assertEqual(target.role, "get_pointer_control")
        self.assertEqual(target.keycode, 38)
        self.assertEqual(target.action_id, "action-1")
        tracker.feed_server(reply(target.sequence))
        self.assertTrue(tracker.should_withhold(
            reply(target.sequence), action_id="action-1", keycode=38,
            peer_pid=24, independently_observed=True))

    def test_matching_key_release_does_not_clear_pending_press_before_sync(self):
        tracker = self.connected()
        tracker.feed_client(query_extension())
        tracker.feed_server(query_extension_reply(1, 200))
        press = tracker.feed_client(fake_input(200, 2, 38))[0]
        release = tracker.feed_client(fake_input(200, 3, 38))[0]
        target = tracker.feed_client(get_pointer_control())[0]
        self.assertEqual(press.role, "xtest_key_press")
        self.assertEqual(release.role, "xtest_key_release")
        self.assertEqual(target.action_id, "action-1")
        self.assertEqual(target.keycode, 38)

    def test_same_pid_second_connection_and_colliding_sequence_are_not_selected(self):
        identity = self.connected("identity")
        input_conn = self.connected("input")
        for tracker in (identity, input_conn):
            tracker.feed_client(query_extension())
            tracker.feed_server(query_extension_reply(1, 200))
        identity.feed_client(request(127))
        identity_req = identity.feed_client(get_pointer_control())[0]
        input_conn.feed_client(fake_input(200, 2, 38))
        input_req = input_conn.feed_client(get_pointer_control())[0]
        self.assertEqual(identity_req.sequence, input_req.sequence)
        identity.feed_server(reply(identity_req.sequence))
        self.assertFalse(identity.should_withhold(
            reply(identity_req.sequence), action_id="action-1", keycode=38,
            peer_pid=24, independently_observed=True))

    def test_wrong_opcode_wrong_event_or_intervening_request_cannot_bind(self):
        tracker = self.connected()
        tracker.feed_client(query_extension())
        tracker.feed_server(query_extension_reply(1, 200))
        wrong_opcode = tracker.feed_client(fake_input(201, 2, 38))[0]
        self.assertEqual(wrong_opcode.role, "other")
        tracker.feed_client(get_pointer_control())
        non_press = tracker.feed_client(fake_input(200, 3, 38))[0]
        self.assertEqual(non_press.role, "xtest_key_release")
        tracker.feed_client(get_pointer_control())
        tracker.feed_client(fake_input(200, 2, 38))
        tracker.feed_client(request(127))
        sync = tracker.feed_client(get_pointer_control())[0]
        self.assertIsNone(sync.action_id)
        self.assertFalse(tracker.should_withhold(
            reply(sync.sequence), action_id="action-1", keycode=38,
            peer_pid=24, independently_observed=True))

    def test_missing_or_mismatched_receipt_and_wrong_peer_forward(self):
        tracker = self.connected()
        tracker.feed_client(query_extension())
        tracker.feed_server(query_extension_reply(1, 200))
        tracker.feed_client(fake_input(200, 2, 38))
        target = tracker.feed_client(get_pointer_control())[0]
        exact = reply(target.sequence)
        self.assertFalse(tracker.should_withhold(
            exact, action_id="action-1", keycode=38, peer_pid=24,
            independently_observed=False))
        self.assertFalse(tracker.should_withhold(
            exact, action_id="action-2", keycode=38, peer_pid=24,
            independently_observed=True))
        self.assertFalse(tracker.should_withhold(
            exact, action_id="action-1", keycode=38, peer_pid=25,
            independently_observed=True))
        self.assertFalse(tracker.should_withhold(
            reply(target.sequence + 1), action_id="action-1", keycode=38,
            peer_pid=24, independently_observed=True))

    def test_unknown_extension_and_failed_negotiation_fail_open(self):
        tracker = self.connected()
        tracker.feed_client(query_extension())
        tracker.feed_server(query_extension_reply(1, 0, present=False))
        press = tracker.feed_client(fake_input(200, 2, 38))[0]
        self.assertEqual(press.role, "other")
        self.assertIsNone(tracker.xtest_major_opcode)

    def test_malformed_setup_or_frame_is_rejected(self):
        tracker = X11ProxyConnection("bad", 24, owner_pid=24, action_id="action-1")
        with self.assertRaises(FrameError):
            tracker.feed_client(b"x" + bytes(20))
        tracker = self.connected()
        with self.assertRaises(FrameError):
            tracker.feed_client(b"\x62\0\0\0\0\0\0\0")

    def test_server_reply_sequence_is_scoped_to_connection_and_query_type(self):
        tracker = self.connected()
        tracker.feed_client(query_extension(b"OTHER"))
        tracker.feed_server(query_extension_reply(1, 200))
        self.assertIsNone(tracker.xtest_major_opcode)

    def test_wrapped_action_sequence_fails_open(self):
        tracker = self.connected()
        tracker.xtest_major_opcode = 200
        tracker._next_sequence = 0xFFFE
        tracker.feed_client(fake_input(200, 2, 38))
        target = tracker.feed_client(get_pointer_control())[0]
        self.assertEqual(target.sequence, 0x10000)
        self.assertFalse(tracker.should_withhold(
            reply(0), action_id="action-1", keycode=38, peer_pid=24,
            independently_observed=True))

    def test_previous_epoch_target_is_invalidated_at_wrap(self):
        tracker = self.connected()
        tracker.xtest_major_opcode = 200
        tracker._next_sequence = 0xFFFD
        tracker.feed_client(fake_input(200, 2, 38))
        target = tracker.feed_client(get_pointer_control())[0]
        self.assertEqual(target.sequence, 0xFFFF)
        tracker.feed_client(request(127))
        self.assertIsNone(tracker.target)
        self.assertFalse(tracker.should_withhold(
            reply(0xFFFF), action_id="action-1", keycode=38, peer_pid=24,
            independently_observed=True))

    def test_excess_pending_extension_queries_disables_selection(self):
        tracker = self.connected()
        for _ in range(65):
            tracker.feed_client(query_extension())
        self.assertTrue(tracker._query_mapping_ambiguous)
        self.assertEqual(tracker._xtest_query_sequences, {})
        tracker.feed_server(query_extension_reply(1, 200))
        self.assertIsNone(tracker.xtest_major_opcode)


if __name__ == "__main__":
    unittest.main()
