"""Run the retained 18-test kernel suite against the isolated candidate."""
from pathlib import Path
import types
import unittest
from probe import load_kernel

if __name__ == '__main__':
    load_kernel(True)
    source = (Path(__file__).parent / 'source/test_kernel.py.txt').read_text()
    source = source.replace('from runtime.kernel import (', 'from cancel_candidate import (')
    module = types.ModuleType('retained_candidate_kernel_tests')
    exec(compile(source, 'retained_test_kernel.py', 'exec'), module.__dict__)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    raise SystemExit(not result.wasSuccessful())
