"""Separate ordinary regression replay on the exact inert baseline snapshot."""
import importlib.machinery
import importlib.util
import sys
import unittest
from pathlib import Path

package = Path(__file__).resolve().parent
root = package.parents[2]
sys.path.insert(0, str(root))
name = 'runtime.core_v1.contract'
loader = importlib.machinery.SourceFileLoader(name, str(package/'baseline_contract.txt'))
spec = importlib.util.spec_from_loader(name, loader)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
loader.exec_module(module)
suite = unittest.defaultTestLoader.loadTestsFromName('runtime.core_v1.test_admission_current_evidence')
result = unittest.TextTestRunner(verbosity=1).run(suite)
sys.exit(not result.wasSuccessful())
