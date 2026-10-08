"""Apply the existing nine oracle controls to retained raw; forbid construction."""
import json
import unittest
from pathlib import Path
import test_audit


def forbid_candidate(*args, **kwargs):
    raise RuntimeError('retained-output checks must not execute candidate')


def retained_setup(cls):
    root = Path(__file__).parent
    cls.fixtures = json.loads((root / 'fixtures.json').read_text())
    cls.raw = json.loads((root / 'run-a01/raw.json').read_text())


if __name__ == '__main__':
    test_audit.run = forbid_candidate
    test_audit.AuditControls.setUpClass = classmethod(retained_setup)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_audit.AuditControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
