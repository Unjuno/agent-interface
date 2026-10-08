import unittest
import gates


class GateTests(unittest.TestCase):
    def setUp(self):
        self.expected = {'generation': 1, 'owner': 'source', 'scope': 'fixture', 'summary': 'plain', 'formats': [['text/plain', 'plain'], ['text/html', 'html']]}
        self.observed = dict(self.expected)

    def test_html_mutation_is_invisible_to_summary(self):
        self.observed['formats'] = [['text/plain', 'plain'], ['text/html', 'changed']]
        self.assertEqual(gates.precheck('summary', self.expected, self.observed), 'ELIGIBLE')
        self.assertEqual(gates.precheck('manifest', self.expected, self.observed), 'REJECT_DEPENDENCY')

    def test_generation_and_owner_are_not_format_checks(self):
        for key, value in [('generation', 2), ('owner', 'other'), ('scope', 'other')]:
            with self.subTest(key=key):
                changed = dict(self.observed, **{key: value})
                self.assertEqual(gates.precheck('manifest', self.expected, changed), 'REJECT_DEPENDENCY')

    def test_false_epoch_is_not_integer_one(self):
        self.observed['generation'] = True
        self.assertEqual(gates.precheck('manifest', self.expected, self.observed), 'HOLD_RESOURCE')

    def test_empty_resource_is_unavailable(self):
        self.observed.update(summary=None, formats=[])
        self.assertEqual(gates.precheck('manifest', self.expected, self.observed), 'HOLD_RESOURCE')

    def test_unknown_format_does_not_erase_verified_effect(self):
        contract = {'text': 'Alex', 'bold': True, 'formats': ['text/html']}
        effect = {'text': 'Alex', 'bold': True}
        self.assertEqual(gates.postcheck(True, [], effect, contract, require_format=True), 'HOLD_FORMAT')
        self.assertEqual(gates.postcheck(True, [], effect, contract, require_format=False), 'VERIFIED_CORRECT')

    def test_format_match_does_not_prove_markup_effect(self):
        contract = {'text': 'Alex', 'bold': True, 'formats': ['text/html']}
        effect = {'text': 'Alex', 'bold': False}
        self.assertEqual(gates.postcheck(True, ['text/html'], effect, contract, require_format=True), 'VERIFIED_WRONG')

    def test_no_paste_is_no_effect(self):
        self.assertEqual(gates.postcheck(False, [], {'text': '', 'bold': False}, {'text': 'Alex', 'bold': False, 'formats': ['text/plain']}, require_format=True), 'NO_EFFECT')


if __name__ == '__main__':
    unittest.main()
