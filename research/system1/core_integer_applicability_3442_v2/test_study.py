from __future__ import annotations

import unittest

from runtime.core_v1.contract import ContractError, admit_program, capability_manifest, KNOWN_CAPABILITIES
from research.system1.core_integer_applicability_3442_v2.study import (
    CASE_KINDS,
    FIELD_SPECS,
    MODES,
    build_cases,
    build_program,
    run_case,
)


class CoreIntegerApplicabilityTests(unittest.TestCase):
    def test_successor_matrix_covers_all_13_integer_leaves(self) -> None:
        cases = build_cases()
        # The predecessor freeze says 12 fields, but current-main source has
        # 13 integer leaves. This successor covers every leaf rather than
        # silently omitting one.
        self.assertEqual(len(FIELD_SPECS), 13)
        self.assertEqual(len(CASE_KINDS), 15)
        self.assertEqual(set(MODES), {"direct", "json_roundtrip"})
        self.assertEqual(len(cases), 390)
        self.assertEqual(len({case["case_id"] for case in cases}), 390)
        self.assertEqual(
            {(case["field"], case["kind"], case["mode"]) for case in cases},
            {
                (field, kind, mode)
                for field in FIELD_SPECS
                for kind in CASE_KINDS
                for mode in MODES
            },
        )

    def test_current_validator_accepts_only_exact_in_range_integers(self) -> None:
        cases = build_cases()
        selected = {
            ("source.observation_seq", "lo", "direct"): True,
            ("source.observation_seq", "bool_false", "direct"): False,
            ("source.observation_seq", "float_mid", "direct"): False,
            ("source.observation_seq", "below", "json_roundtrip"): False,
            ("source.observation_seq", "lo_plus_two", "direct"): True,
            ("authority.expires_at_ns", "lo", "json_roundtrip"): True,
            ("authority.expires_at_ns", "bool_true", "direct"): False,
            ("pointer_move.x", "hi", "direct"): True,
            ("observe.h", "above", "json_roundtrip"): False,
        }
        by_key = {(case["field"], case["kind"], case["mode"]): case for case in cases}
        manifest = capability_manifest(
            "integer-boundary-fixture",
            "macos",
            "inert",
            KNOWN_CAPABILITIES,
        )
        for key, expected in selected.items():
            with self.subTest(key=key):
                record = run_case(
                    by_key[key],
                    main_sha="a" * 40,
                    source_sha256="b" * 64,
                    manifest=manifest,
                )
                self.assertEqual(record["validation"]["accepted"], expected)
                self.assertEqual(record["admission"]["accepted"], expected)
                if expected:
                    self.assertIsNone(record["admission"]["error"])
                else:
                    self.assertEqual(record["admission"]["error"], "INVALID_PROGRAM")

    def test_invalid_operation_values_preserve_the_failing_operation_index(self) -> None:
        program = build_program("activate.timeout_ms", False)
        with self.assertRaises(ContractError) as caught:
            from runtime.core_v1.contract import validate_program

            validate_program(program)
        self.assertEqual(caught.exception.operation_index, 0)


if __name__ == "__main__":
    unittest.main()
