"""Offline construction tests against the exact frozen #5156 raw auditor."""
import json
import unittest
from pathlib import Path

from frozen_auditor import audit
from serializer_successor import joined_release_envelope


HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "EXPECTED.json").read_text(encoding="utf-8"))


def owner_bracket(owner_id, intent, key, code, start):
    return {
        "event": "owner_key_release_bracket",
        "trigger_class": "explicit_up",
        "owner_id": owner_id,
        "intent_token": intent,
        "key": key,
        "keycode": code,
        "timing_valid": True,
        "grants_input_authority": False,
        "physical_key_up_claimed": False,
        "request_started_ns": start + 2,
        "request_returned_ns": start + 3,
        "shared_sync_returned_ns": start + 4,
    }


def complete_records():
    rows = [{"event": "fixture", "allocation": EXPECTED["allocation"]}]
    admitted = {}
    joined = []
    for case, spec in EXPECTED["cases"].items():
        owner_id, intent = "owner-1", "intent-" + case
        for key in spec["admit"]:
            code = ord(key)
            admitted[(case, key)] = (owner_id, intent, code)
            rows.append({"event": "admission", "case": case, "key": key,
                         "keycode": code, "owner_id": owner_id,
                         "intent_token": intent, "down_verified": True,
                         "grants_input_authority": False})
        for release in spec["release"]:
            key = release["key"]
            _, _, code = admitted[(case, key)]
            if release["class"] == "explicit_up":
                start = 1000 + len(joined) * 100
                caller = {"release_call_started_ns": start,
                          "release_call_returned_ns": start + 10,
                          "owner_id": owner_id, "intent_token": intent}
                joined.append(joined_release_envelope(
                    owner_bracket(owner_id, intent, key, code, start), case, caller))
            else:
                rows.append({"event": "owner_record", "record": {
                    "event": "owner_key_release_bracket",
                    "trigger_class": "owner_lease_cleanup", "owner_id": owner_id,
                    "intent_token": intent, "key": None, "keycode": code,
                    "timing_valid": True, "grants_input_authority": False,
                    "physical_key_up_claimed": False, "reason": "cancelled",
                    "request_started_ns": 3002, "request_returned_ns": 3003,
                    "shared_sync_returned_ns": 3004}})
                rows.append({"event": "owner_record", "record": {
                    "event": "owner_release", "reason": "cancelled",
                    "verified": True, "keys_down": [], "buttons_down": []}})
        rows.append({"event": "case_terminal", "case": case,
                     "all_up_verified": True,
                     **({"second_admission_rejected": True}
                        if case == "partial_cancel" else {})})
    rows.extend(joined)
    rows.extend([
        {"event": "process_cleanup", "owner_stopped": True},
        {"event": "terminal_state", "neutral": True,
         "grants_input_authority": False},
        {"event": "runner_complete", "exit_code": 0},
    ])
    return rows


class SerializerSuccessorTests(unittest.TestCase):
    def test_reproduces_original_python_merge_failure(self):
        row = owner_bracket("owner", "intent", "a", 38, 10)
        with self.assertRaisesRegex(TypeError, "multiple values for keyword argument 'event'"):
            dict(event="joined_release", **row)

    def test_envelope_preserves_owner_event_and_audits(self):
        row = owner_bracket("owner", "intent", "a", 38, 10)
        caller = {"release_call_started_ns": 9,
                  "release_call_returned_ns": 20,
                  "owner_id": "owner", "intent_token": "intent"}
        result = joined_release_envelope(row, "single_explicit", caller)
        self.assertEqual(result["event"], "joined_release")
        self.assertEqual(result["owner_event"], "owner_key_release_bracket")
        self.assertEqual(row["event"], "owner_key_release_bracket")
        self.assertEqual(result["shared_sync_returned_ns"], 14)

    def test_complete_synthetic_stream_passes_frozen_auditor(self):
        self.assertEqual(audit(complete_records(), EXPECTED), [])

    def test_missing_joined_release_fails_inventory_gate(self):
        rows = complete_records()
        rows.remove(next(row for row in rows if row.get("event") == "joined_release"))
        self.assertTrue(any("release inventory mismatch" in error
                            for error in audit(rows, EXPECTED)))

    def test_identity_corruption_fails_audit(self):
        rows = complete_records()
        row = next(row for row in rows if row.get("event") == "joined_release")
        row["caller_owner_id"] = "other-owner"
        self.assertTrue(any("caller receipt identity mismatch" in error
                            for error in audit(rows, EXPECTED)))

    def test_envelope_refuses_wrong_owner_event(self):
        with self.assertRaisesRegex(ValueError, "expected owner_key_release_bracket"):
            joined_release_envelope({"event": "owner_release"}, "case", {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
