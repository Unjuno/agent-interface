from __future__ import annotations

import unittest

from audit import audit_row


def key(keysym: str, state: int, stamp: int) -> dict[str, object]:
    return {"type": "2", "keysym": keysym, "state": state, "monotonic_ns": stamp}


def effect(stamp: int = 30, count: int = 1) -> list[dict[str, object]]:
    return [{
        "saved": True,
        "text": "marker-123",
        "save_callback_count": count,
        "save_callback_monotonic_ns": stamp,
    }]


class AuditRowTests(unittest.TestCase):
    def test_ordered_chord_and_effect_pass(self) -> None:
        result = audit_row([key("Control_L", 0, 10), key("s", 4, 20)], effect(), "marker-123")
        self.assertTrue(result["pass"])

    def test_missing_s_is_rejected_even_if_effect_exists(self) -> None:
        result = audit_row([key("Control_L", 0, 10)], effect(), "marker-123")
        self.assertFalse(result["pass"])

    def test_duplicate_chord_is_rejected(self) -> None:
        result = audit_row(
            [key("Control_L", 0, 10), key("s", 4, 20), key("Control_L", 0, 21), key("s", 4, 22)],
            effect(30),
            "marker-123",
        )
        self.assertFalse(result["pass"])

    def test_reversed_or_unmodified_s_is_rejected(self) -> None:
        reversed_events = [key("s", 4, 10), key("Control_L", 0, 20)]
        unmodified_events = [key("Control_L", 0, 10), key("s", 0, 20)]
        self.assertFalse(audit_row(reversed_events, effect(), "marker-123")["pass"])
        self.assertFalse(audit_row(unmodified_events, effect(), "marker-123")["pass"])

    def test_intervening_keypress_breaks_the_chord_sequence(self) -> None:
        events = [key("Control_L", 0, 10), key("x", 4, 15), key("s", 4, 20)]
        self.assertFalse(audit_row(events, effect(), "marker-123")["pass"])

    def test_wrong_marker_or_missing_effect_is_rejected(self) -> None:
        chord = [key("Control_L", 0, 10), key("s", 4, 20)]
        self.assertFalse(audit_row(chord, effect(), "different-marker")["pass"])
        self.assertFalse(audit_row(chord, [], "marker-123")["pass"])

    def test_effect_must_follow_key_witness(self) -> None:
        result = audit_row([key("Control_L", 0, 10), key("s", 4, 20)], effect(19), "marker-123")
        self.assertFalse(result["pass"])

    def test_duplicate_effect_receipts_are_rejected(self) -> None:
        events = [key("Control_L", 0, 10), key("s", 4, 20)]
        self.assertFalse(audit_row(events, effect(30) + effect(31, count=2), "marker-123")["pass"])

    def test_duplicate_callback_count_is_rejected(self) -> None:
        events = [key("Control_L", 0, 10), key("s", 4, 20)]
        self.assertFalse(audit_row(events, effect(30, count=2), "marker-123")["pass"])

    def test_boolean_values_do_not_substitute_for_integer_receipts(self) -> None:
        events = [key("Control_L", 0, 10), key("s", 4, 20)]
        events[1]["state"] = True
        self.assertFalse(audit_row(events, effect(), "marker-123")["pass"])
        self.assertFalse(audit_row([key("Control_L", 0, 10), key("s", 4, 20)], effect(30, count=True), "marker-123")["pass"])


if __name__ == "__main__":
    unittest.main()
