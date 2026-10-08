import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("witness_audit", HERE / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def make_fixture(root):
    audit.ROOT = root
    env = {"network_namespace_preflight_exit": 1}
    (root / "ENVIRONMENT.json").write_text(json.dumps(env), encoding="utf-8")
    env_hash = hashlib.sha256((root / "ENVIRONMENT.json").read_bytes()).hexdigest()
    cases = {"allocation_id": "MAP01-V39-OWNER-KEYMAP-WITNESS-C02-20261004-01", "key": "w", "expected_keycode": 25,
             "occurrences": 2, "witness_stages": ["pre_down", "post_down", "post_up"],
             "expected_key_down_by_stage": [False, True, False]}
    freeze = {"runtime_environment_sha256": env_hash, "network_isolation": "none", "sha256": {}}
    (root / "FREEZE.json").write_text(json.dumps(freeze), encoding="utf-8")
    freeze_hash = hashlib.sha256((root / "FREEZE.json").read_bytes()).hexdigest()
    started = {"allocation_id": "MAP01-V39-OWNER-KEYMAP-WITNESS-C02-20261004-01", "candidate_invocation": 1,
               "network_isolation": "none", "freeze_sha256": freeze_hash,
               "environment_sha256": env_hash}
    raw = {"schema": "map01-v39-owner-keymap-witness-raw-v1", "allocation_id": "MAP01-V39-OWNER-KEYMAP-WITNESS-C02-20261004-01",
           "candidate_invocations": 1, "candidate_complete": True, "failure": None,
           "freeze_sha256": freeze_hash, "environment_sha256": env_hash,
           "xvfb_tcp_enabled": False, "xvfb_argv": ["Xvfb", "-nolisten", "tcp"],
           "xvfb_exit_code_after_controlled_terminate": -15,
           "xvfb_socket_removed": True, "xvfb_lock_removed": True,
           "xvfb_stderr_fatal": False, "owner_state_before_close": {"owned_keycodes": []},
           "owner_records": [
               {"event": "owner_release", "reason": "release", "verified": True,
                "keys_down": [], "buttons_down": []},
               {"event": "owner_release", "reason": "release", "verified": True,
                "keys_down": [], "buttons_down": []},
               {"event": "owner_release", "reason": "close", "verified": True,
                "keys_down": [], "buttons_down": []}],
           "events": [], "occurrences": []}
    for i in range(2):
        token = f"MAP01-V39-OWNER-KEYMAP-WITNESS-C02-20261004-01:{i+1:02d}"
        samples = []
        for j, down in enumerate((False, True, False)):
            bits = bytearray(32)
            if down: bits[25 // 8] |= 1 << (25 % 8)
            bitmap = bytes(bits)
            samples.append({"keycode": 25, "key_down": down, "keys_down": [25] if down else [],
                            "bitmap_hex": bitmap.hex(), "bitmap_sha256": hashlib.sha256(bitmap).hexdigest(),
                            "sample_started_ns": 10 + j*10 + i*100,
                            "sample_finished_ns": 11 + j*10 + i*100})
        raw["occurrences"].append({"occurrence": i+1, "intent_token": token,
                                   "pre_down": samples[0], "post_down": samples[1], "post_up": samples[2]})
        raw["events"].append({"event": "input_admission", "key": "w", "intent_token": token})
        raw["events"].append({"event": "input_release_transition", "key": "w", "intent_token": token,
                              "ordinary_release_candidate": True, "owner_transition_verified": True,
                              "intent_token_matches_after_batch": True,
                              "owner_identity_matches_after_batch": True,
                              "owner_sample_ordered_after_batch": True,
                              "owned_keycodes_after_batch": [],
                              "physical_verification_authoritative": False,
                              "grants_input_authority": False,
                              "release_batch_identifier": token,
                              "release_batch_step": i, "release_batch_size": 1,
                              "release_batch_position": 0,
                              "release_call_started_ns": 22+i*100,
                              "release_call_returned_ns": 23+i*100})
    return raw, cases, freeze, started, env


class AuditTests(unittest.TestCase):
    def test_positive_record_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            raw, cases, freeze, started, env = make_fixture(Path(temp))
            checks = audit.evaluate(raw, cases, freeze, started, env)
            self.assertTrue(all(checks.values()), checks)

    def test_inverted_keymap_witness_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            raw, cases, freeze, started, env = make_fixture(Path(temp))
            raw["occurrences"][0]["post_down"]["key_down"] = False
            checks = audit.evaluate(raw, cases, freeze, started, env)
            self.assertFalse(checks["six_32_byte_keymap_witnesses_false_true_false"])

    def test_authority_claim_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            raw, cases, freeze, started, env = make_fixture(Path(temp))
            raw["events"][1]["grants_input_authority"] = True
            checks = audit.evaluate(raw, cases, freeze, started, env)
            self.assertFalse(checks["backend_receipts_bind_each_occurrence"])


if __name__ == "__main__":
    unittest.main()
