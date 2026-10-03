import unittest
from audit import same, integer, Text


class TypeAndEffect(unittest.TestCase):
    def test_json_identity_keeps_boolean_and_float_distinct(self):
        for other in [True, 1.0]:
            self.assertFalse(same({'value': 1}, {'value': other}))
        self.assertTrue(same({'a': [1, False]}, {'a': [1, False]}))

    def test_native_identifiers_are_strict_positive_integers(self):
        for other in [True, 1.0, 0, -1, '1']:
            self.assertFalse(integer(other, True))
        self.assertTrue(integer(1, True))

    def test_saved_html_oracle_excludes_title_and_style(self):
        parser = Text(); parser.feed('<html><head><title>Cedar</title><style>Cedar</style></head><body><p>Juniper</p></body></html>')
        self.assertEqual(''.join(parser.parts), 'Juniper')


if __name__ == '__main__': unittest.main()
