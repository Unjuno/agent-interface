"""Mutation tests for the independent Xvfb trace auditor."""
import importlib.util
import hashlib
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def fixture(cycles=10):
    actions = audit.expected(cycles)
    raw = {
        "status": "CANDIDATE_COMPLETE",
        "cycles_requested": cycles,
        "source_sha256": {},
        "candidate_sha256": sha(HERE / "candidate.py"),
        "actions": [
            {k: row[k] for k in ("key", "down", "keymap")}
            for row in actions
        ],
        "keycodes": {"a": 38, "space": 65},
        "client_window": 1234,
        "client_events": [],
        "emitted_rows": [],
        "errors": [],
        "server_keymap_empty_after_edges": True,
        "cleanup": {
            "explicit_owner_release": {"verified": True, "keys_down": []},
            "owner_close_result": {"verified": True, "keys_down": []},
            "owner_closed": True, "owner_stopped": True,
            "owner_thread_alive": False,
            "server_keymap_empty_after_close": True, "xvfb_stopped": True,
        },
    }
    for i, action in enumerate(actions):
        raw["client_events"].append({
            "cycle": action["cycle"], "edge": action["edge"],
            "key": action["key"], "down": action["down"],
            "event_type": 2 if action["down"] else 3,
            "keycode": raw["keycodes"][action["key"]],
            "event_window": 1234,
            "dispatch_ns": i + 1,
        })

    admission_position = 0
    batch_number = 0
    for cycle in range(cycles):
        groups = [PATTERN_KEYS[:2], PATTERN_KEYS[2:4], PATTERN_KEYS[4:8]]
        for group in groups:
            admitted = []
            for key, down in group:
                if down:
                    row = {
                        "event": "input_admission", "id": "xvfb-per-key-a03",
                        "step": 7, "admission_position": admission_position,
                        "key": key, "owner_id": "owner-1",
                        "intent_token": "intent-1",
                        "admission_key_matches_request": True,
                    }
                    raw["emitted_rows"].append(row)
                    admitted.append(row)
                    admission_position += 1
            release_rows = []
            for key, down in group:
                if not down:
                    admission = next(row for row in reversed(raw["emitted_rows"])
                                     if row.get("event") == "input_admission"
                                     and row.get("key") == key
                                     and (row.get("id"), row.get("step"),
                                          row.get("admission_position"))
                                     not in {(r.get("id"),r.get("step"),r.get("admission_position")) for r in raw["emitted_rows"] if r.get("event") == "input_release_transition"})
                    release_rows.append({
                        "event": "input_release_transition", "id": admission["id"],
                        "step": admission["step"],
                        "admission_position": admission["admission_position"],
                        "key": key, "owner_id": "owner-1",
                        "intent_token": "intent-1",
                        "admission_identity_status": "matched",
                        "release_key_matches_request": True,
                        "owner_transition_verified": True,
                        "owner_identity_matches_after_batch": True,
                        "intent_token_matches_after_batch": True,
                        "owner_sample_ordered_after_batch": True,
                        "owned_keycodes_after_batch": [],
                        "physical_verification_authoritative": False,
                        "grants_input_authority": False,
                        "release_batch_keys_match_requests": True,
                        "release_batch_identifier": "xvfb-per-key-a03",
                        "release_batch_step": 7,
                        "owner_sample_after_finished_ns": batch_number + 100,
                        "release_batch_size": len([x for x in group if not x[1]]),
                        "release_batch_position": len(release_rows),
                    })
            for row in release_rows:
                raw["emitted_rows"].append(row)
            batch_number += 1
    return raw


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


PATTERN_KEYS = audit.PATTERN
FREEZE = {
    "cycles": 10,
    "executor_identifier": "xvfb-per-key-a03",
    "executor_step": 7,
    "source_sha256": {},
    "candidate_sha256": sha(HERE / "candidate.py"),
    "auditor_sha256": sha(HERE / "audit.py"),
}


class AuditTests(unittest.TestCase):
    def test_complete_fixture_passes(self):
        result = audit.run(fixture(), FREEZE)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")

    def test_release_identity_corruption_fails(self):
        raw = fixture()
        next(row for row in raw["emitted_rows"]
             if row.get("event") == "input_release_transition")["admission_position"] = 39
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_release_owner_mismatch_fails(self):
        raw = fixture()
        next(row for row in raw["emitted_rows"]
             if row.get("event") == "input_release_transition")["owner_id"] = "owner-2"
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_release_intent_mismatch_fails(self):
        raw = fixture()
        next(row for row in raw["emitted_rows"]
             if row.get("event") == "input_release_transition")["intent_token"] = "intent-2"
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_authority_escalation_fails(self):
        raw = fixture()
        next(row for row in raw["emitted_rows"]
             if row.get("event") == "input_release_transition")["physical_verification_authoritative"] = True
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_client_dispatch_omission_fails(self):
        raw = fixture()
        raw["client_events"].pop()
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_wrong_client_window_fails(self):
        raw = fixture()
        raw["client_events"][0]["event_window"] = 4321
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_admission_key_order_corruption_fails(self):
        raw = fixture()
        next(row for row in raw["emitted_rows"] if row.get("event") == "input_admission")["key"] = "space"
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_keymap_transition_corruption_fails(self):
        raw = fixture()
        raw["actions"][4]["keymap"]["a"] = False
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")

    def test_unverified_close_fails(self):
        raw = fixture()
        raw["cleanup"]["owner_close_result"]["verified"] = False
        self.assertEqual(audit.run(raw, FREEZE)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
