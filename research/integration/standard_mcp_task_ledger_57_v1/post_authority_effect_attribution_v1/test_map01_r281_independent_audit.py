"""Audit the retained R281 expiry/release/recovery/effect event ordering."""
import hashlib
import json
import unittest
from pathlib import Path

from effect_attribution_v1 import adjudicate_effect


PACKET = (Path(__file__).resolve().parents[4] / "outputs"
          / "r281-audit-20261121" / "extracted" / "trial")
RAW_SHA256 = {
    "events.jsonl": "0dee2dcb92fb5d427c6d25f9aacaf641eacf60291e1312fbf7d6f5d23de52a9a",
    "owner-events.json": "81df708b74daca2d7386931f68afd659556b5ca565c854426bf74d486cfe9b4f",
}


def events():
    with (PACKET / "events.jsonl").open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def owner_events():
    return json.loads((PACKET / "owner-events.json").read_text(encoding="utf-8"))


def first_event(rows, kind, *, event_id=None, reason=None):
    return next(row for row in rows if row.get("event") == kind
                and (event_id is None or row.get("id") == event_id)
                and (reason is None or row.get("reason") == reason))


class R281IndependentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PACKET.is_dir():
            raise unittest.SkipTest(
                "R281 raw packet is local-only; run the recorded audit where retained")
        for name, expected in RAW_SHA256.items():
            actual = hashlib.sha256((PACKET / name).read_bytes()).hexdigest()
            if actual != expected:
                raise AssertionError(f"R281 raw digest mismatch: {name}")
        cls.rows = events()
        cls.owners = owner_events()

    def test_expiry_release_then_distinct_authorized_effect_is_reconstructable(self):
        accepted = first_event(self.rows, "accepted", event_id="R281-one-shot")
        expired_release = first_event(self.owners, "owner_release", reason="expired")
        recovery = first_event(self.rows, "terminal", event_id="R281-recovery")
        fresh = first_event(self.rows, "accepted", event_id="R281-live-effect")
        effect_observations = [row for row in self.rows
                               if row.get("event") == "typed_observation"
                               and row.get("id") == "R281-live-effect"]
        fresh_terminal = first_event(self.rows, "terminal", event_id="R281-live-effect")

        expiry_ns = accepted["valid_until_ns"]
        self.assertLessEqual(expiry_ns, expired_release["verified_ns"])
        self.assertTrue(expired_release["verified"])
        self.assertEqual(expired_release["keys_down"], [])
        self.assertEqual(expired_release["buttons_down"], [])
        self.assertEqual(recovery["status"], "completed")
        self.assertTrue(recovery["release"]["verified"])
        self.assertGreater(fresh["accepted_ns"], expiry_ns)
        self.assertEqual(fresh["id"], "R281-live-effect")
        self.assertEqual([row["signals"]["ammo"]["value"]
                          for row in effect_observations], [50, 50, 49])
        self.assertEqual(fresh_terminal["status"], "completed")
        self.assertTrue(fresh_terminal["release"]["verified"])

        attribution = adjudicate_effect(
            task_success=True,
            effect_observed_ns=None,
            authority_expiry_ns=expiry_ns,
            release_received_ns=expired_release["verified_ns"],
            horizon_end_ns=expired_release["verified_ns"],
        )
        self.assertEqual(attribution["effect_timing"], "unknown")
        self.assertIsNone(attribution["eligible_task_success"])

    def test_first_attempt_does_not_publish_a_task_effect_or_input_released_event(self):
        rows = [row for row in self.rows if row.get("id") == "R281-one-shot"]
        self.assertFalse(any(row.get("event") == "input_released" for row in rows))
        disposition = json.loads((PACKET.parent / "provisional-disposition.json")
                                 .read_text(encoding="utf-8"))
        self.assertEqual(disposition["input_released_events"], [])
        self.assertEqual(disposition["terminal_status"], "completed")
        self.assertTrue(disposition["terminal_release_verified"])
        self.assertNotEqual(
            first_event(self.rows, "accepted", event_id="R281-one-shot")["id"],
            first_event(self.rows, "accepted", event_id="R281-live-effect")["id"],
        )


if __name__ == "__main__":
    unittest.main()
