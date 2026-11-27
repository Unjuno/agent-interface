"""Specification tests for the A03 offline proxy reply-framing discriminator."""

import unittest

from .reply_gate import (
    ExactReplyGate,
    FrameError,
    KeyPressReceipt,
    RequestLedger,
    classify_request_role,
    decode_reply_frame,
)


def request_frame(opcode: int = 43, byte_order: str = "little") -> bytes:
    return bytes((opcode, 0)) + (1).to_bytes(2, byte_order)


def reply_frame(sequence: int, byte_order: str = "little") -> bytes:
    return bytes((1, 0)) + sequence.to_bytes(2, byte_order) + bytes(28)


def fake_input_keypress_frame(major_opcode: int = 200, keycode: int = 38) -> bytes:
    """Python-Xlib 0.33 XTEST FakeInput request (9 four-byte units)."""
    frame = bytearray(36)
    frame[0:2] = bytes((major_opcode, 2))
    frame[2:4] = (9).to_bytes(2, "little")
    frame[4] = 2  # X.KeyPress
    frame[5] = keycode
    return bytes(frame)


class ReplyGateSpecification(unittest.TestCase):
    def test_prepress_identity_reply_is_forwarded_even_after_input_started(self):
        ledger = RequestLedger()
        ledger.record("identity-xconn", 24, request_frame(98),
                      byte_order="little", role="query_extension")
        identity = ledger.record("identity-xconn", 24, request_frame(),
                                 byte_order="little", role="process_identity")
        ledger.record("input-xconn", 24, fake_input_keypress_frame(),
                      byte_order="little", action_id="action-1",
                      xtest_major_opcode=200)
        target = ledger.record("input-xconn", 24, request_frame(106),
                               byte_order="little")
        gate = ExactReplyGate(owner_pid=24, target_request=target)
        reply, matched = ledger.lookup_reply(
            "identity-xconn", 24, reply_frame(identity.sequence), "little")
        self.assertFalse(gate.should_withhold(reply, matched, None))

    def test_only_exact_post_keypress_get_pointer_control_reply_is_withheld(self):
        ledger = RequestLedger()
        press = ledger.record("input-xconn", 24, fake_input_keypress_frame(),
                              byte_order="little", action_id="action-1",
                              xtest_major_opcode=200)
        target = ledger.record("input-xconn", 24, request_frame(106),
                               byte_order="little")
        gate = ExactReplyGate(owner_pid=24, target_request=target)
        exact, matched = ledger.lookup_reply(
            "input-xconn", 24, reply_frame(target.sequence), "little")
        other_reply, other = ledger.lookup_reply(
            "input-xconn", 24, reply_frame(target.sequence + 1), "little")
        self.assertFalse(gate.should_withhold(exact, matched, None))
        self.assertTrue(gate.should_withhold(
            exact, matched, KeyPressReceipt("action-1", press.keycode)))
        self.assertFalse(gate.should_withhold(
            exact, matched, KeyPressReceipt("action-1", press.keycode + 1)))
        self.assertFalse(gate.should_withhold(
            other_reply, other, KeyPressReceipt("action-1", press.keycode)))

    def test_duplicate_sequence_on_same_peer_different_connection_is_not_a_match(self):
        ledger = RequestLedger()
        ledger.record("identity-xconn", 24, request_frame(98),
                      byte_order="little", role="query_extension")
        identity = ledger.record("identity-xconn", 24, request_frame(),
                                 byte_order="little", role="process_identity")
        ledger.record("input-xconn", 24, fake_input_keypress_frame(),
                      byte_order="little", action_id="action-1",
                      xtest_major_opcode=200)
        target = ledger.record("input-xconn", 24, request_frame(106),
                               byte_order="little")
        self.assertEqual(identity.sequence, target.sequence)
        gate = ExactReplyGate(owner_pid=24, target_request=target)
        duplicate_sequence, matched = ledger.lookup_reply(
            "identity-xconn", 24, reply_frame(target.sequence), "little")
        self.assertFalse(gate.should_withhold(
            duplicate_sequence, matched, KeyPressReceipt("action-1", 38)))

    def test_wrong_peer_or_wrong_action_fails_open_to_forward(self):
        ledger = RequestLedger()
        ledger.record("input-xconn", 24, fake_input_keypress_frame(),
                      byte_order="little", action_id="action-1",
                      xtest_major_opcode=200)
        target = ledger.record("input-xconn", 24, request_frame(106),
                               byte_order="little")
        gate = ExactReplyGate(owner_pid=24, target_request=target)
        wrong_peer, matched = ledger.lookup_reply(
            "input-xconn", 25, reply_frame(target.sequence), "little")
        correct, matched_correct = ledger.lookup_reply(
            "input-xconn", 24, reply_frame(target.sequence), "little")
        self.assertFalse(gate.should_withhold(
            wrong_peer, matched, KeyPressReceipt("action-1", 38)))
        self.assertFalse(gate.should_withhold(
            correct, matched_correct, KeyPressReceipt("action-2", 38)))

    def test_malformed_reply_frame_is_rejected(self):
        ledger = RequestLedger()
        with self.assertRaises(FrameError):
            ledger.lookup_reply("input-xconn", 24, bytes(31), "little")

    def test_big_endian_reply_sequence_is_decoded(self):
        self.assertEqual(decode_reply_frame(reply_frame(258, "big"), "big"),
                         (1, 258))

    def test_non_input_request_cannot_be_selected_as_the_withheld_reply(self):
        ledger = RequestLedger()
        identity = ledger.record("identity-xconn", 24, request_frame(),
                                 byte_order="little", role="process_identity")
        with self.assertRaises(ValueError):
            ExactReplyGate(owner_pid=24, target_request=identity)

    def test_xlib_sync_reply_is_connection_scoped_get_pointer_control(self):
        ledger = RequestLedger()
        fake_input = ledger.record(
            "input-xconn", 24, fake_input_keypress_frame(),
            byte_order="little", action_id="action-1", xtest_major_opcode=200)
        self.assertEqual(fake_input.sequence, 1)
        sync_request = ledger.record(
            "input-xconn", 24, request_frame(106), byte_order="little")
        self.assertEqual(sync_request.sequence, 2)
        self.assertEqual(sync_request.role, "get_pointer_control")

        ledger.record("identity-xconn", 24, request_frame(98),
                      byte_order="little", role="query_extension")
        identity = ledger.record("identity-xconn", 24, request_frame(200),
                                 byte_order="little", role="process_identity")
        self.assertEqual(identity.sequence, sync_request.sequence)

        try:
            gate = ExactReplyGate(owner_pid=24, target_request=sync_request)
        except ValueError as error:
            self.fail(f"the actual Xlib sync reply role must be gateable: {error}")
        input_reply, input_request = ledger.lookup_reply(
            "input-xconn", 24, reply_frame(sync_request.sequence), "little")
        identity_reply, identity_request = ledger.lookup_reply(
            "identity-xconn", 24, reply_frame(identity.sequence), "little")
        receipt = KeyPressReceipt("action-1", fake_input.keycode)
        self.assertTrue(gate.should_withhold(input_reply, input_request, receipt))
        self.assertFalse(gate.should_withhold(identity_reply, identity_request, receipt))
        self.assertEqual(classify_request_role(
            request_frame(106), "little"), "get_pointer_control")


if __name__ == "__main__":
    unittest.main()
