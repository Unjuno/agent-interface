"""Regression tests for JSON enum types; no backend is opened."""
from copy import deepcopy
from pathlib import Path
import runpy
import unittest

from runtime.core_v1.contract import (
    ContractError, COORDINATE_FRAMES, KNOWN_CAPABILITIES, admit_program,
    capability_manifest, required_capabilities, validate_program,
)
from runtime.core_v1.sequence import expand_key_repeats, expand_text_gaps

INVALID = (None, False, 0, 1.5, "", "sentinel-k8r3", [], {},
           ["sentinel-k8r3"], {"tag": "sentinel-k8r3"})
TOKENS = {
    "observe": ("screen_physical_px", "screen_logical", "window_client"),
    "pointer_move": ("screen_physical_px", "screen_logical", "window_client"),
    "pointer_button": ("left", "middle", "right", "x1", "x2"),
}
DETAILS = {"observe": "invalid observe frame", "pointer_move": "invalid pointer frame",
           "pointer_button": "invalid pointer button"}


def make_program(kind, value, mode="plain"):
    prefix = {"plain": [], "repeat": [{"op": "key_chord", "keys": ["Tab"], "repeat": 2}],
              "gap": [{"op": "text", "text": "abc", "gap_ms": 1}]}[mode]
    op = {"op": kind}
    if kind == "pointer_button":
        op.update(button=deepcopy(value), down=True)
    else:
        op.update(frame=deepcopy(value), x=0, y=0)
        if kind == "observe":
            op.update(w=1, h=1)
    return {"schema": "agent-interface/program-v1", "program_id": "enum-check",
            "source": {"observation_seq": 1, "binding_revision": 1},
            "authority": {"lease_id": "test-only", "expires_at_ns": 100},
            "terminal": {"release_all_required": True},
            "ops": deepcopy(prefix) + [op, {"op": "release_all"}]}


def compiled(program, mode):
    result = deepcopy(program)
    if mode == "repeat":
        result["ops"] = expand_key_repeats(result["ops"], max_ops=128)
    elif mode == "gap":
        result["ops"], _ = expand_text_gaps(result["ops"])
    return result


def manifest():
    return capability_manifest("test", "linux", "inert", KNOWN_CAPABILITIES,
                               frames=sorted(COORDINATE_FRAMES))


class ProgramEnumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Execute the entire existing validator, not cli_v1's dispatch initializer.
        source = Path(__file__).resolve().parents[1] / "cli_v1" / "validate_program.py"
        cls.inspect = staticmethod(runpy.run_path(str(source))["inspect_program"])

    def test_invalid_json_values_have_typed_location(self):
        for mode, index in (("plain", 0), ("repeat", 2), ("gap", 5)):
            for kind in TOKENS:
                for value in INVALID:
                    with self.subTest(mode=mode, kind=kind, value=value):
                        program = compiled(make_program(kind, value, mode), mode)
                        before = deepcopy(program)
                        with self.assertRaises(ContractError) as caught:
                            validate_program(program)
                        self.assertEqual(caught.exception.operation_index, index)
                        self.assertEqual(str(caught.exception), DETAILS[kind])
                        self.assertEqual(program, before)

    def test_invalid_json_values_are_typed_admission_refusals(self):
        for kind in TOKENS:
            for value in INVALID:
                result = admit_program(make_program(kind, value), manifest(), now_ns=10,
                                       current_observation_seq=1, current_binding_revision=1)
                self.assertFalse(result.accepted)
                self.assertEqual(result.error, "INVALID_PROGRAM")
                self.assertEqual(result.required_capabilities, ())

    def test_static_mapping_and_no_value_echo(self):
        for mode, index in (("plain", 0), ("repeat", 2), ("gap", 5)):
            for kind in TOKENS:
                for value in INVALID:
                    program = make_program(kind, value, mode)
                    before = deepcopy(program)
                    report = self.inspect(program)
                    self.assertIs(report["static_valid"], False)
                    self.assertEqual(report["expanded_operation_index"], index)
                    self.assertEqual(report["source_operation_index"], int(mode != "plain"))
                    self.assertEqual(report["detail"], DETAILS[kind])
                    self.assertNotIn("sentinel-k8r3", str(report))
                    self.assertIs(report["side_effect_authority"], False)
                    self.assertIsNone(report["task_success"])
                    self.assertEqual(program, before)

    def test_all_supported_tokens_remain_valid(self):
        for mode in ("plain", "repeat", "gap"):
            for kind, tokens in TOKENS.items():
                for token in tokens:
                    with self.subTest(mode=mode, kind=kind, token=token):
                        program = make_program(kind, token, mode)
                        expanded = compiled(program, mode)
                        self.assertIs(validate_program(expanded), expanded)
                        result = admit_program(expanded, manifest(), now_ns=10,
                                               current_observation_seq=1, current_binding_revision=1)
                        self.assertTrue(result.accepted)
                        self.assertEqual(result.required_capabilities, required_capabilities(expanded))
                        self.assertIs(self.inspect(program)["static_valid"], True)

    def test_live_admission_conditions_are_not_weakened(self):
        p = make_program("observe", "screen_physical_px")
        cases = [(101, 1, 1, "LEASE_EXPIRED"), (10, 2, 1, "STALE_OBSERVATION"),
                 (10, 1, 2, "STALE_BINDING")]
        for now, seq, binding, error in cases:
            r = admit_program(p, manifest(), now_ns=now, current_observation_seq=seq,
                              current_binding_revision=binding)
            self.assertFalse(r.accepted)
            self.assertEqual(r.error, error)
        for state, error in (("unknown", "UNSUPPORTED_CAPABILITY"),
                             ("permission_required", "PERMISSION_DENIED")):
            m = manifest()
            m["capabilities"]["capture.frame"]["state"] = state
            r = admit_program(p, m, now_ns=10, current_observation_seq=1, current_binding_revision=1)
            self.assertEqual(r.error, error)
        m = manifest()
        m["coordinate_frames"] = ["window_client"]
        r = admit_program(p, m, now_ns=10, current_observation_seq=1, current_binding_revision=1)
        self.assertEqual(r.error, "COORDINATE_UNSUPPORTED")


if __name__ == "__main__":
    unittest.main()
