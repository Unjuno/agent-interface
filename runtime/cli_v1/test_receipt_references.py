"""Public receipt decoders must evaluate canonical JSON Pointer positions."""
import copy
import unittest

from runtime.cli_v1.receipt_references import (
    NATIVE_REFS, NATIVE_MULTI_REFS, expand_native_receipt, expand_receipt,
)


EVENT = {'event': 'released', 'verified': True}
OBSERVATION = {'sequence': 1, 'native': {'title': 'private fixture'}}
INVALID_ARRAY_TOKENS = ('-1', '+0', '00', '01', ' 0', '0 ', '٠', '０', '0_0', '0\n')


def receipt(kind, token, *, object_member=False):
    if kind == 'event':
        marker = {'event_ref': 0}
        report = {token: marker} if object_member else [marker, marker]
        return expand_receipt, {
            'schema': 'agent-interface/receipt-view-v2-event-refs',
            'events': [EVENT], 'report': report,
            'event_references': {'/report/' + token: 0}, 'reference_scope': 'fixture',
        }
    marker = {'observation_ref': '/native_result/observation'}
    history = {token: marker} if object_member else [marker, marker]
    path = '/native_result/history/' + token
    return expand_native_receipt, {
        'schema': NATIVE_MULTI_REFS if kind == 'native_multiple' else NATIVE_REFS,
        'native_result': {'observation': OBSERVATION, 'history': history},
        'observation_references': {path: '/native_result/observation'}
        if kind == 'native_multiple' else [path],
        'reference_scope': 'fixture',
    }


class ReceiptPointerTests(unittest.TestCase):
    def test_array_aliases_are_refused_without_mutating_input(self):
        # Reintroducing int(token) traversal accepts these invalid positions.
        for kind in ('event', 'native_single', 'native_multiple'):
            for token in INVALID_ARRAY_TOKENS:
                expand, value = receipt(kind, token)
                before = copy.deepcopy(value)
                with self.subTest(kind=kind, token=token), self.assertRaises(ValueError):
                    expand(value)
                self.assertEqual(value, before)

    def test_canonical_array_positions_expand_only_the_listed_member(self):
        for kind in ('event', 'native_single', 'native_multiple'):
            for token in ('0', '1'):
                expand, value = receipt(kind, token)
                before = copy.deepcopy(value)
                result = expand(value)
                actual = result['report'] if kind == 'event' else result['native_result']['history']
                prior = before['report'] if kind == 'event' else before['native_result']['history']
                expected = EVENT if kind == 'event' else OBSERVATION
                self.assertEqual(actual[int(token)], expected)
                self.assertEqual(actual[1 - int(token)], prior[1 - int(token)])
                self.assertEqual(value, before)

    def test_numeric_looking_object_names_are_preserved(self):
        for kind in ('event', 'native_single', 'native_multiple'):
            for token in ('-1', '00', '٠', ''):
                expand, value = receipt(kind, token, object_member=True)
                result = expand(value)
                actual = result['report'] if kind == 'event' else result['native_result']['history']
                self.assertEqual(actual, {token: EVENT if kind == 'event' else OBSERVATION})

    def test_valid_pointer_escapes_are_decoded_once(self):
        for kind in ('event', 'native_single', 'native_multiple'):
            for key, token in (('a/b', 'a~1b'), ('a~b', 'a~0b'), ('~1', '~01')):
                expand, value = receipt(kind, token, object_member=True)
                mapping = value['report'] if kind == 'event' else value['native_result']['history']
                mapping[key] = mapping.pop(token)
                result = expand(value)
                actual = result['report'] if kind == 'event' else result['native_result']['history']
                self.assertEqual(actual, {key: EVENT if kind == 'event' else OBSERVATION})

    def test_invalid_escape_is_not_treated_as_a_literal_object_name(self):
        for kind in ('event', 'native_single', 'native_multiple'):
            for token in ('bad~', 'bad~2'):
                expand, value = receipt(kind, token, object_member=True)
                with self.subTest(kind=kind, token=token), self.assertRaises(ValueError):
                    expand(value)

    def test_unresolved_array_positions_are_refused(self):
        for kind in ('event', 'native_single', 'native_multiple'):
            for token in ('2', '-'):
                expand, value = receipt(kind, token)
                with self.subTest(kind=kind, token=token), self.assertRaises(ValueError):
                    expand(value)

    def test_event_report_root_can_be_an_explicit_reference(self):
        value = {'schema': 'agent-interface/receipt-view-v2-event-refs',
                 'events': [EVENT], 'report': {'event_ref': 0},
                 'event_references': {'/report': 0}, 'reference_scope': 'fixture'}
        self.assertEqual(expand_receipt(value)['report'], EVENT)


if __name__ == '__main__':
    unittest.main()
