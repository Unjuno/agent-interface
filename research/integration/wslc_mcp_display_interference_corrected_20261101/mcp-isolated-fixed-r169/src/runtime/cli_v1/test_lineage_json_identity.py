"""Canonical JSON identity must survive the lineage admission boundary."""
from copy import deepcopy
import unittest

from runtime.cli_v1.lineage import (
    dispatch_with_lineage, program_digest, receipt_digest, sidecar_digest,
)
from runtime.cli_v1.test_lineage_freshness import case


def rehash(program, receipt, sidecar):
    receipt['digest'] = receipt_digest(receipt)
    sidecar['program_digest'] = program_digest(program)
    sidecar['evidence_receipt_digest'] = receipt['digest']
    sidecar['digest'] = sidecar_digest(sidecar)


class LineageJsonIdentityTests(unittest.TestCase):
    def check_refusal(self, program, receipt, sidecar, error, **current):
        rehash(program, receipt, sidecar)
        before = deepcopy((program, receipt, sidecar))
        calls = []
        result = dispatch_with_lineage(
            program, {}, receipt, sidecar,
            current_observation_seq=current.get('observation', 7),
            current_binding_revision=current.get('binding', 3),
            dispatch_fn=lambda *args, **kwargs: calls.append((args, kwargs)),
        )
        self.assertEqual(result['status'], 'lineage_rejected')
        self.assertEqual(result['error'], error)
        self.assertEqual(calls, [])
        self.assertEqual((program, receipt, sidecar), before)

    def test_sidecar_number_representation_cannot_match_receipt(self):
        for field, value in (
            ('point', [10.0, 20]), ('point', [10, 20.0]),
            ('observation_seq', 7.0), ('binding_revision', 3.0),
        ):
            with self.subTest(field=field, value=value):
                program, receipt, sidecar = case()
                sidecar[field] = value
                self.check_refusal(program, receipt, sidecar, 'SIDECAR_RECEIPT_MISMATCH')

    def test_program_source_and_point_cannot_change_number_representation(self):
        for field in ('observation_seq', 'binding_revision', 'x', 'y'):
            with self.subTest(field=field):
                program, receipt, sidecar = case()
                if field in program['source']:
                    program['source'][field] = float(program['source'][field])
                    error = 'PROGRAM_SOURCE_MISMATCH'
                else:
                    program['ops'][0][field] = float(program['ops'][0][field])
                    error = 'PROGRAM_POINT_MISMATCH'
                self.check_refusal(program, receipt, sidecar, error)

    def test_current_runtime_numbers_cannot_match_integer_receipt(self):
        program, receipt, sidecar = case()
        self.check_refusal(program, receipt, sidecar, 'STALE_OBSERVATION', observation=7.0)
        self.check_refusal(program, receipt, sidecar, 'STALE_BINDING', binding=3.0)

    def test_boolean_false_cannot_match_zero_coordinate(self):
        program, receipt, sidecar = case()
        program['ops'][0]['x'] = 0
        receipt['point'] = [0, 20]
        sidecar['point'] = [False, 20]
        self.check_refusal(program, receipt, sidecar, 'SIDECAR_RECEIPT_MISMATCH')

    def test_identical_json_with_different_key_order_delegates_once(self):
        program, receipt, sidecar = case()
        program['source'] = dict(reversed(list(program['source'].items())))
        rehash(program, receipt, sidecar)
        before = deepcopy((program, receipt, sidecar))
        calls = []
        result = dispatch_with_lineage(
            program, {}, receipt, sidecar,
            current_observation_seq=7, current_binding_revision=3,
            dispatch_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or {'ok': True},
        )
        self.assertEqual(result['status'], 'delegated')
        self.assertEqual(result['cli_result'], {'ok': True})
        self.assertEqual(len(calls), 1)
        self.assertEqual((program, receipt, sidecar), before)


if __name__ == '__main__':
    unittest.main()
