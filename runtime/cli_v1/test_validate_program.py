"""Focused tests for the display-free, non-authoritative module entry point."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from runtime.cli_v1.validate_program import inspect_file, inspect_program, MAX_INPUT_BYTES


def program(ops=None):
    return {"schema": "agent-interface/program-v1", "program_id": "local-test",
            "source": {"observation_seq": 0, "binding_revision": 0},
            "authority": {"lease_id": "test-only", "expires_at_ns": 1},
            "terminal": {"release_all_required": True},
            "ops": ops if ops is not None else [{"op": "release_all"}]}


class ValidationTests(unittest.TestCase):
    def assert_no_authority(self, result):
        self.assertIs(result["side_effect_authority"], False)
        self.assertIs(result["backend_checked"], False)
        self.assertIsNone(result["task_success"])
        self.assertEqual(result["runtime_admission"], "not_evaluated")

    def test_minimum_and_expired_are_static_valid(self):
        r = inspect_program(program())
        self.assertIs(r["static_valid"], True)
        self.assert_no_authority(r)

    def test_input_unchanged(self):
        p = program([{"op": "text", "text": "ab", "gap_ms": 2}, {"op": "release_all"}])
        original = deepcopy(p)
        inspect_program(p)
        self.assertEqual(p, original)

    def test_non_object(self):
        for p in [None, [], "text", 1, True]:
            self.assertEqual(inspect_program(p)["error"], "PROGRAM_NOT_OBJECT")

    def test_observe_width_shape(self):
        p = program([{"op": "observe", "frame": "screen_physical_px", "x": 0,
                      "y": 0, "width": 20, "height": 20}, {"op": "release_all"}])
        r = inspect_program(p)
        self.assertEqual(r["detail"], "observe w must be int")
        self.assertEqual(r["source_operation_index"], 0)
        self.assert_no_authority(r)

    def test_boolean_width(self):
        p = program([{"op": "observe", "frame": "screen_physical_px", "x": 0,
                      "y": 0, "w": True, "h": 20}, {"op": "release_all"}])
        self.assertEqual(inspect_program(p)["detail"], "observe w must be int")

    def test_repeat_mapping(self):
        p = program([{"op": "key_chord", "keys": ["Right"], "repeat": 3},
                     {"op": "observe", "frame": "screen_physical_px", "x": 0, "y": 0},
                     {"op": "release_all"}])
        r = inspect_program(p)
        self.assertEqual((r["source_operation_index"], r["expanded_operation_index"]), (1, 3))

    def test_gap_mapping(self):
        p = program([{"op": "text", "text": "ab", "gap_ms": 1},
                     {"op": "observe", "frame": "screen_physical_px", "x": 0, "y": 0},
                     {"op": "release_all"}])
        r = inspect_program(p)
        self.assertEqual((r["source_operation_index"], r["expanded_operation_index"]), (1, 3))

    def test_mixed_expansion(self):
        p = program([{"op": "text", "text": "ab", "gap_ms": 1},
                     {"op": "key_chord", "keys": ["Right"], "repeat": 2},
                     {"op": "release_all"}])
        r = inspect_program(p)
        self.assertEqual((r["static_valid"], r["expanded_operation_count"]), (True, 6))

    def test_capacity_boundary(self):
        p = program([{"op": "focus", "target": "root"},
                     {"op": "key_chord", "keys": ["Right"], "repeat": 126},
                     {"op": "release_all"}])
        self.assertEqual(inspect_program(p)["expanded_operation_count"], 128)
        p["ops"].insert(0, {"op": "focus", "target": "root"})
        self.assertEqual(inspect_program(p)["error"], "INVALID_KEY_REPEAT")

    def test_invalid_repeat_and_gap(self):
        for directive, op, value, code in [
            ("repeat", "key_chord", True, "INVALID_KEY_REPEAT"),
            ("gap_ms", "text", -1, "INVALID_TEXT_GAP")]:
            p = program([{"op": op, "keys": ["Right"], "text": "a", directive: value},
                         {"op": "release_all"}])
            self.assertEqual(inspect_program(p)["error"], code)

    def test_missing_release(self):
        p = program([{"op": "text", "text": "ordinary text"}])
        self.assertEqual(inspect_program(p)["error"], "INVALID_PROGRAM")

    def test_unhashable_frame_returns_invalid(self):
        p = program([{"op": "observe", "frame": [], "x": 0, "y": 0, "w": 1, "h": 1},
                     {"op": "release_all"}])
        self.assertIs(inspect_program(p)["static_valid"], False)

    def test_unknown_fields_keep_core_semantics(self):
        p = program(); p["note"] = "ignored metadata"
        self.assertIs(inspect_program(p)["static_valid"], True)

    def test_diagnostics_do_not_echo_payload(self):
        sentinel = "PRIVATE_SENTINEL"
        for ops in [[{"op": sentinel}, {"op": "release_all"}],
                    [{"op": "key_state", "key": sentinel, "down": False}, {"op": "release_all"}],
                    [{"op": "text", "text": sentinel}, {"op": "release_all"}]]:
            self.assertNotIn(sentinel, json.dumps(inspect_program(program(ops))))

    def test_file_errors(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "program.json"
            self.assertEqual(inspect_file(p)["error"], "INPUT_UNREADABLE")
            p.write_bytes(b'{"ops":')
            self.assertEqual(inspect_file(p)["error"], "INVALID_JSON")
            p.write_bytes(b'\xff')
            self.assertEqual(inspect_file(p)["error"], "INVALID_JSON_ENCODING_OR_LIMIT")
            p.write_bytes(b' ' * (MAX_INPUT_BYTES + 1))
            self.assertEqual(inspect_file(p)["error"], "INPUT_TOO_LARGE")

    def test_real_module_cli_without_site_or_display(self):
        env = dict(os.environ)
        env.pop("DISPLAY", None); env.pop("WAYLAND_DISPLAY", None)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "program.json"
            for data, code in [(program(), 0), ({}, 1), (None, 1)]:
                p.write_text(json.dumps(data), encoding="utf-8")
                before = p.read_bytes()
                r = subprocess.run([sys.executable, "-S", "-B", "-m", "runtime.cli_v1.validate_program",
                                    "--program", str(p)], env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(r.returncode, code, r.stderr)
                self.assertEqual(r.stderr, "")
                self.assert_no_authority(json.loads(r.stdout))
                self.assertEqual(before, p.read_bytes())


if __name__ == "__main__":
    unittest.main()
