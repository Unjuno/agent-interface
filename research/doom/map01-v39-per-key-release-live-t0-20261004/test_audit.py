import hashlib
import json
import unittest

import audit


def keymap(keys, down):
    codes = {"space": 65, "Up": 111}
    bitmap = bytearray(32)
    for key in down:
        code = codes[key]
        bitmap[code // 8] |= 1 << (code % 8)
    return {"keycodes": {key: codes[key] for key in keys},
            "keymap_hex": bytes(bitmap).hex(),
            "keys_down": {key: key in down for key in keys}}


def fixture():
    freeze = {"runtime_sources_sha256": {}, "sha256": {},
              "runtime_environment_sha256": "environment",
              "source_support_sha256": "support",
              "support_archive_path": "source-support.tar.gz"}
    events = []
    observers = []
    trials = []
    owner = "owner-1"
    for trial_id, keys in audit.PROGRAMS.items():
        start = len(events)
        token = "intent-" + trial_id
        events.append({"event": "accepted", "id": trial_id,
                       "intent_token": token})
        held = []
        observers.append(dict(keymap(keys, []), trial_id=trial_id, label="before"))
        for key in keys:
            held.append(key)
            events.append({"event": "input_admission", "key": key})
            observers.append(dict(keymap(keys, held), trial_id=trial_id,
                                  label="after_admission:" + key))
        returns = []
        base = 1000 + start * 100
        for position, key in enumerate(keys):
            returned = base + 20 + position * 20
            returns.append(returned)
            events.append({
                "event": "input_release_transition", "key": key,
                "release_batch_identifier": trial_id, "release_batch_step": 0,
                "intent_token": token, "owner_id": owner,
                "release_call_started_ns": returned - 10,
                "release_call_returned_ns": returned,
                "owner_sample_after_started_ns": base + 80,
                "owner_sample_after_finished_ns": base + 90,
                "emit_started_ns": base + 100 + position,
                "owned_keycodes_after_batch": [],
                "release_batch_size": len(keys),
                "release_batch_position": position,
                "owner_transition_verified": True,
                "backend_owned_before_release": True,
                "ordinary_release_candidate": True,
                "grants_input_authority": False,
                "physical_verification_authoritative": False,
            })
        terminal = {"event": "terminal", "id": trial_id, "status": "completed",
                    "release": {"verified": True}}
        events.append(terminal)
        observers.append(dict(keymap(keys, []), trial_id=trial_id,
                              label="after_terminal"))
        trials.append({"trial_id": trial_id, "keys": keys, "intent_token": token,
                       "event_start_index": start,
                       "event_end_index": len(events), "terminal": terminal,
                       "pre_keymap": observers[-(len(keys)+2)],
                       "post_keymap": observers[-1]})
    raw = b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in events)
    candidate = {
        "candidate_completed": True, "model_calls": 0,
        "runtime_environment_sha256": "environment",
        "network_interfaces": ["ip6tnl0", "lo", "sit0", "tunl0"],
        "network_link_states": {"ip6tnl0": "DOWN", "lo": "DOWN",
                                "sit0": "DOWN", "tunl0": "DOWN"},
        "network_ipv4_routes": "", "network_ipv6_routes": "",
        "backend_class": "doom_typed_release_backend_v3.Backend",
        "executor_class": "executor_v12.Executor", "owner_id": owner,
        "runtime_source_hashes": {}, "trials": trials,
        "cleanup": {"owner_thread_alive": False,
                    "x11_processes": [{"returncode": -15}, {"returncode": -15}]},
        "events_sha256": hashlib.sha256(raw).hexdigest(),
        "events_bytes": raw,
        "owner_events": [{"event": "owner_release", "verified": True,
                          "keys_down": []}],
    }
    return freeze, candidate, events, observers


class AuditTests(unittest.TestCase):
    def test_complete_positive_record_passes_and_mutation_controls_reject(self):
        report = audit.evaluate(*fixture())
        self.assertEqual(report["gate"], "PASS_X11_TELEMETRY_ADAPTER_SCOPED")
        self.assertTrue(all(report["mutation_controls"].values()))

    def test_inverted_timing_fails_closed(self):
        freeze, candidate, events, observers = fixture()
        row = next(row for row in events if row.get("event") == "input_release_transition")
        row["release_call_returned_ns"] = row["release_call_started_ns"] - 1
        report = audit.evaluate(freeze, candidate, events, observers)
        self.assertFalse(report["checks"]["v39-single-space.monotonic_call_and_post_batch_sample"])

    def test_wrong_token_fails_closed(self):
        freeze, candidate, events, observers = fixture()
        row = next(row for row in events if row.get("event") == "input_release_transition")
        row["intent_token"] = "wrong"
        report = audit.evaluate(freeze, candidate, events, observers)
        self.assertFalse(report["checks"]["v39-single-space.identity_and_owner_match"])

    def test_keymap_claim_without_down_witness_fails_closed(self):
        freeze, candidate, events, observers = fixture()
        row = next(row for row in observers if row.get("trial_id") == "v39-single-space"
                   and row.get("label", "").startswith("after_admission:"))
        row.update(keymap(audit.PROGRAMS[row["trial_id"]], []))
        report = audit.evaluate(freeze, candidate, events, observers)
        self.assertFalse(report["checks"]["v39-single-space.independent_keymap_down_during_hold"])

    def test_missing_key_release_fails_closed(self):
        freeze, candidate, events, observers = fixture()
        row = next(row for row in events if row.get("event") == "input_release_transition"
                   and row.get("release_batch_identifier") == "v39-two-key-up-space")
        events.remove(row)
        report = audit.evaluate(freeze, candidate, events, observers)
        self.assertFalse(report["checks"]["v39-two-key-up-space.per_key_release_one_per_key"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
