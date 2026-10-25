"""Runs construction tests before freeze; never invoke after formal candidate/auditor."""
import json
import tempfile
import unittest
from pathlib import Path
from candidate import build_corpus
from auditor import audit_corpus
from test_contract import ContractTests

class CliContract(ContractTests):
    pass

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
