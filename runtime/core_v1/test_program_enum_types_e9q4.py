"""Regression for indexed rejection of JSON-valued operation enum mistakes.

No backend is opened. The static inspector is loaded by its file path so this
focused core suite does not import cli_v1's unrelated dispatch facade.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from runtime.core_v1 import contract as c
from runtime.core_v1.sequence import expand_text_gaps

BAD = [None, False, True, 0, 1.5, '', 'not-a-member', [], {}, ['left'], {'name': 'left'}]
OPS = [({'op': 'pointer_move', 'x': 0, 'y': 0}, 'frame', c.COORDINATE_FRAMES, 'invalid pointer frame'),
       ({'op': 'observe', 'x': 0, 'y': 0, 'w': 1, 'h': 1}, 'frame', c.COORDINATE_FRAMES, 'invalid observe frame'),
       ({'op': 'pointer_button', 'down': True}, 'button', c.BUTTONS, 'invalid pointer button')]


def program(ops):
    return {'schema': c.SCHEMA_PROGRAM, 'program_id': 'enum-test',
            'source': {'observation_seq': 1, 'binding_revision': 1},
            'authority': {'lease_id': 'test-only', 'expires_at_ns': 100},
            'terminal': {'release_all_required': True},
            'ops': deepcopy(ops) + [{'op': 'release_all'}]}


def manifest():
    return c.capability_manifest('test-only', 'linux', 'no-device', c.KNOWN_CAPABILITIES,
                                 frames=sorted(c.COORDINATE_FRAMES))


def inspector():
    path = Path(__file__).parents[1] / 'cli_v1' / 'validate_program.py'
    spec = importlib.util.spec_from_file_location('enum_static_inspector', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProgramEnumTypesTests(unittest.TestCase):
    def test_invalid_json_values_have_exact_contract_location(self):
        for template, field, _, message in OPS:
            for value in BAD:
                with self.subTest(op=template['op'], value=value):
                    row = program([{'op': 'wait_update', 'timeout_ms': 0}, dict(template, **{field: value})])
                    before = deepcopy(row)
                    with self.assertRaises(c.ContractError) as caught:
                        c.validate_program(row)
                    self.assertEqual(str(caught.exception), message)
                    self.assertIs(type(caught.exception.operation_index), int)
                    self.assertEqual(caught.exception.operation_index, 1)
                    self.assertEqual(row, before)

    def test_invalid_values_are_admission_refusals(self):
        for template, field, _, _ in OPS:
            for value in BAD:
                with self.subTest(op=template['op'], value=value):
                    result = c.admit_program(program([dict(template, **{field: value})]), manifest(),
                                             now_ns=1, current_observation_seq=1, current_binding_revision=1)
                    self.assertEqual(result, c.Admission(False, 'INVALID_PROGRAM', ()))

    def test_all_valid_enum_members_are_unchanged(self):
        for template, field, members, _ in OPS:
            for value in sorted(members):
                with self.subTest(op=template['op'], value=value):
                    row = program([dict(template, **{field: value})])
                    self.assertIs(c.validate_program(row), row)
                    result = c.admit_program(row, manifest(), now_ns=1,
                                             current_observation_seq=1, current_binding_revision=1)
                    self.assertTrue(result.accepted)

    def test_earlier_failure_keeps_precedence(self):
        row = program([{'op': 'key_state', 'key': 'F8', 'down': False},
                       {'op': 'pointer_button', 'button': [], 'down': True}])
        with self.assertRaises(c.ContractError) as caught:
            c.validate_program(row)
        self.assertEqual(str(caught.exception), 'key F8 released while not held')
        self.assertEqual(caught.exception.operation_index, 0)

    def test_global_error_has_no_operation_index(self):
        row = program([{'op': 'pointer_button', 'button': [], 'down': True}])
        row['schema'] = 'wrong'
        with self.assertRaises(c.ContractError) as caught:
            c.validate_program(row)
        self.assertFalse(hasattr(caught.exception, 'operation_index'))

    def test_static_source_mapping_survives_mixed_expansion(self):
        static = inspector()
        prefix = [{'op': 'text', 'text': 'ab', 'gap_ms': 1},
                  {'op': 'key_chord', 'keys': ['F8'], 'repeat': 2}]
        for template, field, _, message in OPS:
            for value in BAD:
                with self.subTest(op=template['op'], value=value):
                    row = program(prefix + [dict(template, **{field: value})])
                    before = deepcopy(row)
                    report = static.inspect_program(row)
                    self.assertIs(report['static_valid'], False)
                    self.assertEqual(report['detail'], message)
                    self.assertEqual(report['source_operation_index'], 2)
                    self.assertEqual(report['expanded_operation_index'], 5)
                    self.assertIs(report['side_effect_authority'], False)
                    self.assertIsNone(report['task_success'])
                    self.assertEqual(row, before)

    def test_capability_and_freshness_controls_remain(self):
        row = program([{'op': 'pointer_move', 'frame': 'window_client', 'x': 0, 'y': 0}])
        for updates, expected in [({'now_ns': 101}, 'LEASE_EXPIRED'),
                                  ({'current_observation_seq': 2}, 'STALE_OBSERVATION'),
                                  ({'current_binding_revision': 2}, 'STALE_BINDING')]:
            args = dict(now_ns=1, current_observation_seq=1, current_binding_revision=1)
            args.update(updates)
            self.assertEqual(c.admit_program(row, manifest(), **args).error, expected)
        m = manifest(); m['capabilities']['input.pointer']['state'] = 'permission_required'
        self.assertEqual(c.admit_program(row, m, now_ns=1, current_observation_seq=1,
                                         current_binding_revision=1).error, 'PERMISSION_DENIED')

    def test_operation_capacity_boundary_remains(self):
        row = program([{'op': 'wait_update', 'timeout_ms': 0}] * 127)
        self.assertIs(c.validate_program(row), row)
        row['ops'].insert(0, {'op': 'wait_update', 'timeout_ms': 0})
        with self.assertRaisesRegex(c.ContractError, 'ops length out of range'):
            c.validate_program(row)


if __name__ == '__main__':
    unittest.main()
