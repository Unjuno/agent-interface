"""Current-context identity must not rely on coercive numeric equality."""
import unittest

from runtime.core_v1.contract import admit_program, capability_manifest


def release_program():
    return {
        'schema': 'agent-interface/program-v1', 'program_id': 'context-test',
        'source': {'observation_seq': 1, 'binding_revision': 1},
        'authority': {'lease_id': 'context-lease', 'expires_at_ns': 100},
        'terminal': {'release_all_required': True}, 'ops': [{'op': 'release_all'}],
    }


class AdmissionContextTests(unittest.TestCase):
    def admit(self, **changes):
        context = {'now_ns': 1, 'current_observation_seq': 1, 'current_binding_revision': 1}
        context.update(changes)
        manifest = capability_manifest('context-backend', 'linux', 'test', ['input.release_all'])
        return admit_program(release_program(), manifest, **context)

    def test_malformed_context_is_typed_refusal(self):
        invalid = (False, True, 1.0, 1.5, '1', None, [], {}, -1, 2**63)
        for field in ('now_ns', 'current_observation_seq', 'current_binding_revision'):
            for value in invalid:
                with self.subTest(field=field, value=value):
                    result = self.admit(**{field: value})
                    self.assertIs(result.accepted, False)
                    self.assertEqual(result.error, 'INVALID_PROGRAM')
                    self.assertEqual(result.required_capabilities, ())

    def test_valid_current_context_and_expiry_boundary_are_unchanged(self):
        for now in (0, 1, 99, 100):
            with self.subTest(now=now):
                result = self.admit(now_ns=now)
                self.assertIs(result.accepted, True)
                self.assertIsNone(result.error)
                self.assertEqual(result.required_capabilities, ('input.release_all',))

    def test_valid_integer_stale_and_expired_controls(self):
        for changes, expected in (
            ({'now_ns': 101}, 'LEASE_EXPIRED'),
            ({'current_observation_seq': 0}, 'STALE_OBSERVATION'),
            ({'current_observation_seq': 2**63 - 1}, 'STALE_OBSERVATION'),
            ({'current_binding_revision': 0}, 'STALE_BINDING'),
            ({'current_binding_revision': 2**63 - 1}, 'STALE_BINDING'),
        ):
            with self.subTest(changes=changes):
                result = self.admit(**changes)
                self.assertIs(result.accepted, False)
                self.assertEqual(result.error, expected)
                self.assertEqual(result.required_capabilities, ('input.release_all',))


if __name__ == '__main__':
    unittest.main()
