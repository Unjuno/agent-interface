"""Validate original RFC 6901 tokens, including adjacent tilde escapes."""
import copy
import itertools
import re
import unittest

from runtime.cli_v1.receipt_references import (
    NATIVE_REFS, NATIVE_MULTI_REFS, _json_pointer,
    expand_native_receipt, expand_receipt,
)


INVALID = ('~~01', 'a~~01b', '~0~~01', '~2', '~', '~~1')
VALID = ('~01', '~001', '~0~1', '', 'a~0b', '~0~0')


def decoded(token):
    return token.replace('~1', '/').replace('~0', '~')


def source_case(kind, token):
    key = decoded(token)
    observation = {'sequence': 7, 'native': {'value': 'observed'}}
    if kind == 'event':
        view = {'schema': 'agent-interface/receipt-view-v2-event-refs',
                'events': [{'event': 'observed'}],
                'report': {'rows': {key: {'event_ref': 0}}},
                'event_references': {'/report/rows/' + token: 0},
                'reference_scope': 'test'}
        expected = copy.deepcopy(view)
        expected.update(schema='agent-interface/receipt-view-v1')
        expected['report']['rows'][key] = copy.deepcopy(view['events'][0])
        del expected['event_references'], expected['reference_scope']
        return expand_receipt, view, expected
    path = '/native_result/rows/' + token
    view = {'schema': NATIVE_REFS if kind == 'single' else NATIVE_MULTI_REFS,
            'native_result': {'observation': observation,
                             'rows': {key: {'observation_ref': '/native_result/observation'}}},
            'observation_references': ([path] if kind == 'single' else
                                      {path: '/native_result/observation'}),
            'reference_scope': 'test'}
    expected = copy.deepcopy(view)
    expected['native_result']['rows'][key] = copy.deepcopy(observation)
    for field in ('schema', 'observation_references', 'reference_scope'):
        del expected[field]
    return expand_native_receipt, view, expected


def target_case(token):
    observation = {'sequence': 7, 'native': {'value': 'observed'}}
    target = '/native_result/captures/' + token
    view = {'schema': NATIVE_MULTI_REFS,
            'native_result': {'rows': {'observation_ref': target},
                             'captures': {decoded(token): observation}},
            'observation_references': {'/native_result/rows': target},
            'reference_scope': 'test'}
    expected = {'native_result': {'rows': copy.deepcopy(observation),
                                 'captures': {decoded(token): copy.deepcopy(observation)}}}
    return expand_native_receipt, view, expected


class ReceiptPointerEscapeTests(unittest.TestCase):
    def test_invalid_original_source_tokens_refuse_without_mutation(self):
        for kind, token in itertools.product(('single', 'multiple', 'event'), INVALID):
            with self.subTest(kind=kind, token=token):
                expand, view, _ = source_case(kind, token)
                before = copy.deepcopy(view)
                with self.assertRaises(ValueError):
                    expand(view)
                self.assertEqual(view, before)

    def test_valid_source_and_target_tokens_preserve_exact_outputs(self):
        for kind, token in itertools.product(('single', 'multiple', 'event', 'target'), VALID):
            with self.subTest(kind=kind, token=token):
                expand, view, expected = (target_case(token) if kind == 'target'
                                          else source_case(kind, token))
                before = copy.deepcopy(view)
                self.assertEqual(expand(view), expected)
                self.assertEqual(view, before)

    def test_invalid_original_target_tokens_refuse_without_mutation(self):
        for token in INVALID:
            with self.subTest(token=token):
                expand, view, _ = target_case(token)
                before = copy.deepcopy(view)
                with self.assertRaises(ValueError):
                    expand(view)
                self.assertEqual(view, before)

    def test_finite_original_token_grammar_matches_independent_regex(self):
        # All 341 strings over this alphabet through length four. The runtime
        # scanner is checked against the RFC grammar expressed independently.
        for length in range(5):
            for chars in itertools.product('~01a', repeat=length):
                token = ''.join(chars)
                with self.subTest(token=token):
                    root = {decoded(token): 31}
                    before = copy.deepcopy(root)
                    if re.fullmatch(r'(?:[^~/]|~[01])*', token) is None:
                        with self.assertRaises(ValueError):
                            _json_pointer(root, '/' + token)
                    else:
                        parent, key = _json_pointer(root, '/' + token)
                        self.assertIs(parent, root)
                        self.assertEqual(key, decoded(token))
                        self.assertEqual(parent[key], 31)
                    self.assertEqual(root, before)


if __name__ == '__main__':
    unittest.main()
