"""Mutation checks execute real copied lifecycle and runtime regressions."""
import io
import json
from pathlib import Path
import sys
import types
import unittest
from probe import load_kernel

ROOT = Path(__file__).parent


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_types = []

    def addError(self, test, err):
        self.error_types.append(err[0])
        super().addError(test, err)


def run():
    kernel = load_kernel(True)
    helper_source = (ROOT / 'source/test_kernel.py.txt').read_text().replace(
        'from runtime.kernel import (', 'from cancel_integration_candidate import (')
    helper = types.ModuleType('cancel_integration_candidate.test_kernel')
    sys.modules[helper.__name__] = helper
    exec(compile(helper_source, helper.__name__, 'exec'), helper.__dict__)
    test_source = (ROOT / 'regressions.py.txt').read_text().replace(
        'from runtime.kernel import ', 'from cancel_integration_candidate import ').replace(
        'from runtime.kernel.test_kernel import ', 'from cancel_integration_candidate.test_kernel import ')
    original = (ROOT / 'candidate_lifecycle.py.txt').read_text()
    guard = 'self.execution_started_ns is not None and release.observed_ns < self.execution_started_ns'
    signature = '    def begin_execution(self, request: ExecutionRequest, *, now_ns: int) -> None:\n'
    cases = {'original': original,
             'missing_bound': original.replace(guard, 'False'),
             'reject_equality': original.replace(guard, guard.replace(' < ', ' <= ')),
             'remember_rejected_begin': original.replace(signature, signature + '        self.execution_started_ns = now_ns\n')}
    rows = []
    for name, source in cases.items():
        if name != 'original':
            assert source != original
        module = types.ModuleType('cancel_integration_candidate.mutation_' + name)
        module.__package__ = 'cancel_integration_candidate'
        sys.modules[module.__name__] = module
        exec(compile(source, name, 'exec'), module.__dict__)
        kernel.RequestLifecycle = module.RequestLifecycle
        tests = types.ModuleType('cancel_mutation_tests_' + name)
        exec(compile(test_source, tests.__name__, 'exec'), tests.__dict__)
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
        rows.append({'name': name, 'source_changed': source != original,
                     'tests': result.testsRun, 'pass': result.wasSuccessful(),
                     'failures': len(result.failures), 'errors': len(result.errors),
                     'unrelated_errors': sum(not issubclass(t, kernel.ContractError) for t in result.error_types),
                     'log': output.getvalue()})
    return rows


if __name__ == '__main__':
    rows = run()
    print(json.dumps(rows, indent=2))
    ok = rows[0]['pass'] and all(not r['pass'] and not r['unrelated_errors'] for r in rows[1:])
    raise SystemExit(not ok)
