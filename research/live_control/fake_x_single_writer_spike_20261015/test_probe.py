"""Construction checks before the frozen finite spike; no real X."""
import unittest
from .probe import Case, MATRIX
from .audit import audit


class ConstructionTests(unittest.TestCase):
    def test_all_named_schedules_satisfy_predeclared_trace_gates(self):
        for arm, mode in MATRIX:
            with self.subTest(arm=arm,mode=mode):
                row = Case(arm,mode).run()
                self.assertEqual(audit(row), [], row)


if __name__ == '__main__':
    unittest.main()
