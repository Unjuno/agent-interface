"""Small source-contract construction tests; no formal allocation."""
import unittest
import receiver
import run

class ContractTests(unittest.TestCase):
    def test_valid(self):
        receiver.validate({'scope': 'e5d7-private', 'operation_id': 'A', 'delta': 1})
    def test_boolean(self):
        with self.assertRaises(ValueError):
            receiver.validate({'scope': 'e5d7-private', 'operation_id': 'A', 'delta': True})
    def test_foreign_scope(self):
        with self.assertRaises(ValueError):
            receiver.validate({'scope': 'other', 'operation_id': 'A', 'delta': 1})
    def test_shape(self):
        with self.assertRaises(ValueError):
            receiver.validate({'scope': 'e5d7-private', 'operation_id': 'A', 'delta': 1, 'extra': 0})
    def test_empty_id(self):
        with self.assertRaises(ValueError):
            receiver.validate({'scope': 'e5d7-private', 'operation_id': '', 'delta': 1})
    def test_bounds(self):
        for delta in (4, -4, 1.0, None):
            with self.assertRaises(ValueError):
                receiver.validate({'scope': 'e5d7-private', 'operation_id': 'A', 'delta': delta})
    def test_denominator(self):
        self.assertEqual(sum(len(run.commands(s)) for s in run.SCENARIOS) * 4, 96)
    def test_aba(self):
        self.assertEqual(run.commands('ABA'), [('A', 1), ('B', 3), ('C', -3), ('A', 1), ('A', 1)])

if __name__ == '__main__':
    unittest.main(verbosity=2)
