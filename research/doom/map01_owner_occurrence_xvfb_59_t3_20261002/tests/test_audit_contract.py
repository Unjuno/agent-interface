"""Behavior tests for the independent raw-only T3 auditor."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit.py"


def witness(owner_id, interval_id, stage, down, start, finish):
    bitmap = bytearray(32)
    if down:
        bitmap[25 // 8] |= 1 << (25 % 8)
    data = bytes(bitmap)
    return {
        "event": "owner_keymap_witness",
        "schema": "owner-keymap-witness-v1",
        "owner_id": owner_id,
        "intent_token": "xvfb-t3-repeat-w",
        "interval_id": interval_id,
        "key": "W",
        "keycode": 25,
        "stage": stage,
        "sample_started_ns": start,
        "sample_finished_ns": finish,
        "bitmap_valid": True,
        "bitmap_hex": data.hex(),
        "bitmap_sha256": hashlib.sha256(data).hexdigest(),
        "keys_down": [25] if down else [],
        "key_down": down,
        "expected_key_down": down,
        "matches_expected": True,
        "grants_input_authority": False,
        "physical_key_up_claimed": False,
    }


def valid_fixture():
    ids = ["a" * 32, "b" * 32]
    records = []
    admissions = []
    for i, interval_id in enumerate(ids):
        base = 1000 + i * 1000
        records.extend([
            witness("owner-1", interval_id, "pre_down", False, base + 5, base + 10),
            witness("owner-1", interval_id, "post_down", True, base + 25, base + 30),
            witness("owner-1", interval_id, "post_up", False, base + 105, base + 110),
            {"event": "owner_key_release_bracket", "schema": "owner-key-release-bracket-v1",
             "owner_id": "owner-1", "intent_token": "xvfb-t3-repeat-w",
             "interval_id": interval_id, "key": "W", "keycode": 25,
             "reason": "explicit_up", "trigger_class": "explicit_up",
             "request_started_ns": base + 80, "request_returned_ns": base + 85,
             "shared_sync_returned_ns": base + 90, "timing_valid": True,
             "grants_input_authority": False, "physical_key_up_claimed": False},
        ])
        admissions.append({"event": "input_admission", "key": "W",
                           "interval_id": interval_id, "admitted_ns": base,
                           "input_ack_ns": base + 20})
    records.append({"event": "owner_release", "reason": "close", "verified": True,
                    "keys_down": [], "buttons_down": []})
    cases = {
        "allocation_id": "t3-allocation", "main_sha": "main-sha",
        "upstream_owner_commit": "upstream-commit",
        "upstream_owner_blob_sha1": "upstream-blob", "expected_key": "W",
        "expected_keycode": 25, "occurrences": 2,
        "witness_stages": ["pre_down", "post_down", "post_up"],
        "expected_key_down_by_stage": [False, True, False],
        "expected_all_down_keycodes_by_stage": [[], [25], []],
    }
    freeze = {"sha256": {"dependencies/input_owner_v11.py": "owner-sha"}}
    raw = {
        "schema": "map01-owner-occurrence-xvfb-raw-v1",
        "allocation_id": "t3-allocation", "main_sha": "main-sha",
        "upstream_owner_commit": "upstream-commit",
        "upstream_owner_blob_sha1": "upstream-blob",
        "cases_sha256": "cases-sha", "instrumented_owner_sha256": "owner-sha",
        "candidate_invocations": 1, "retries": 0,
        "namespace_tmpfs": True, "socket_directory_mode": "0o1777",
        "xvfb_argv": ["Xvfb", "-displayfd", "1", "-screen", "0",
                       "640x480x24", "-nolisten", "tcp", "-ac"],
        "xvfb_tcp_enabled": False, "xvfb_display_number": 201, "xvfb_pid": 12345,
        "xvfb_displayfd_ready": True, "xvfb_keycode_w": 25,
        "xvfb_exit_code_after_controlled_terminate": -15,
        "xvfb_socket_removed": True, "xvfb_lock_removed": True,
        "xvfb_stderr_fatal": False, "owner_id": "owner-1",
        "admissions": admissions, "owner_records": records,
    }
    return raw, cases, freeze


class AuditContractTests(unittest.TestCase):
    def load_auditor(self):
        self.assertTrue(AUDIT.is_file(), "independent raw-only audit implementation is required")
        spec = importlib.util.spec_from_file_location("t3_raw_only_audit", AUDIT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_accepts_two_ordered_server_bitmap_occurrences(self):
        raw, cases, freeze = valid_fixture()
        result = self.load_auditor().audit_payload(raw, cases, freeze)
        self.assertEqual(result["status"], "PASS_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED")

    def test_rejects_bitmap_that_disagrees_with_reported_key_state(self):
        raw, cases, freeze = valid_fixture()
        bitmap = bytearray.fromhex(raw["owner_records"][0]["bitmap_hex"])
        bitmap[25 // 8] |= 1 << (25 % 8)
        raw["owner_records"][0]["bitmap_hex"] = bytes(bitmap).hex()
        result = self.load_auditor().audit_payload(raw, cases, freeze)
        self.assertNotEqual(result["status"], "PASS_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED")

    def test_rejects_release_bound_to_another_occurrence(self):
        raw, cases, freeze = valid_fixture()
        raw["owner_records"][4]["interval_id"] = "c" * 32
        result = self.load_auditor().audit_payload(raw, cases, freeze)
        self.assertNotEqual(result["status"], "PASS_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED")


if __name__ == "__main__":
    unittest.main()
