"""Manifest mistakes must become contract refusals, never hashing errors."""
from copy import deepcopy
import unittest

from runtime.core_v1 import contract as c


def manifest():
    return {
        'schema': 'agent-interface/backend-v1',
        'backend_id': 'manifest-boundary',
        'platform': {'os': 'linux', 'backend': 'no-device'},
        'capabilities': {'input.release_all': {'state': 'supported'}},
        'coordinate_frames': ['screen_physical_px'],
        'clock': {'unit': 'ns', 'monotonic': True},
        'permissions': [],
    }


def program():
    return {
        'schema': 'agent-interface/program-v1', 'program_id': 'manifest-test',
        'source': {'observation_seq': 1, 'binding_revision': 1},
        'authority': {'lease_id': 'test-only', 'expires_at_ns': 100},
        'terminal': {'release_all_required': True},
        'ops': [{'op': 'release_all'}],
    }


BAD = [None, False, True, 0, 1.5, '', 'not-a-member', [], {},
       ['supported'], {'state': 'supported'}]


def invalid_manifests():
    for field in ('os', 'state', 'frame'):
        for index, value in enumerate(BAD):
            row = manifest()
            if field == 'os':
                row['platform']['os'] = deepcopy(value)
            elif field == 'state':
                row['capabilities']['input.release_all']['state'] = deepcopy(value)
            else:
                row['coordinate_frames'] = [deepcopy(value)]
            yield f'{field}-{index}', row


class ManifestEnumTypesTests(unittest.TestCase):
    def test_invalid_json_enums_raise_contract_error_without_mutation(self):
        for name, row in invalid_manifests():
            with self.subTest(name=name):
                before = deepcopy(row)
                with self.assertRaises(c.ContractError):
                    c.validate_backend_manifest(row)
                self.assertEqual(row, before)

    def test_admission_returns_invalid_program_for_bad_manifest(self):
        for name, row in invalid_manifests():
            with self.subTest(name=name):
                result = c.admit_program(program(), row, now_ns=1,
                                         current_observation_seq=1,
                                         current_binding_revision=1)
                self.assertEqual(result, c.Admission(False, 'INVALID_PROGRAM', ()))

    def test_readiness_rejects_bad_manifest_as_contract_error(self):
        for name, row in invalid_manifests():
            with self.subTest(name=name), self.assertRaises(c.ContractError):
                c.office_readiness(row)

    def test_valid_enums_preserve_validation_and_admission(self):
        for os_name in ('linux', 'windows', 'macos'):
            for frame in ('screen_physical_px', 'screen_logical', 'window_client'):
                for state, error in (('supported', None),
                                     ('unsupported', 'UNSUPPORTED_CAPABILITY'),
                                     ('unknown', 'UNSUPPORTED_CAPABILITY'),
                                     ('permission_required', 'PERMISSION_DENIED')):
                    with self.subTest(os=os_name, frame=frame, state=state):
                        row = manifest()
                        row['platform']['os'] = os_name
                        row['coordinate_frames'] = [frame]
                        row['capabilities']['input.release_all']['state'] = state
                        before = deepcopy(row)
                        self.assertIs(c.validate_backend_manifest(row), row)
                        result = c.admit_program(program(), row, now_ns=1,
                                                 current_observation_seq=1,
                                                 current_binding_revision=1)
                        self.assertEqual((result.accepted, result.error), (error is None, error))
                        self.assertEqual(row, before)

    def test_frame_list_must_be_nonempty_unique_known_strings(self):
        for frames in ([], None, 'screen_physical_px',
                       ['screen_physical_px', 'screen_physical_px'],
                       ['screen_physical_px', []], ['screen_physical_px', {}],
                       ['screen_physical_px', 'unknown']):
            with self.subTest(frames=frames), self.assertRaises(c.ContractError):
                row = manifest()
                row['coordinate_frames'] = frames
                c.validate_backend_manifest(row)
        row = manifest()
        row['coordinate_frames'] = ['screen_physical_px', 'window_client', 'screen_logical']
        self.assertIs(c.validate_backend_manifest(row), row)


if __name__ == '__main__':
    unittest.main()
