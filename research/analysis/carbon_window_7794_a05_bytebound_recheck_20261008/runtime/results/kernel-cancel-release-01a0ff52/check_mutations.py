"""Three implementation mutations must fail the real candidate regressions."""
import io
import json
from pathlib import Path
import sys
import types
import unittest
from probe import load_kernel
from check_candidate import CancellationBoundaryTests


class MutationResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_types = []

    def addError(self, test, err):
        self.error_types.append(err[0])
        super().addError(test, err)


def run_mutations():
    kernel = load_kernel(True)
    original = (Path(__file__).parent / 'candidate_lifecycle.py.txt').read_text()
    guard = 'self.execution_started_ns is not None and release.observed_ns < self.execution_started_ns'
    mutations = {
        'missing_lower_bound': original.replace(guard, 'False'),
        'reject_equal_timestamp': original.replace(guard, guard.replace(' < ', ' <= ')),
        'overwrite_first_start': original.replace('if self.execution_started_ns is None:', 'if True:'),
    }
    rows = []
    for name, source in mutations.items():
        assert source != original
        module = types.ModuleType('cancel_candidate.mutant_' + name)
        module.__package__ = 'cancel_candidate'
        sys.modules[module.__name__] = module
        exec(compile(source, name, 'exec'), module.__dict__)
        target = types.SimpleNamespace(**{key: value for key, value in vars(kernel).items() if not key.startswith('_')})
        target.RequestLifecycle = module.RequestLifecycle
        # Each test still executes real contract/lifecycle code; only source differs.
        case = type('MutationTests', (CancellationBoundaryTests,),
                    {'setUp': lambda self, target=target: setattr(self, 'k', target)})
        log = io.StringIO()
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=MutationResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(case))
        rows.append({'mutation': name, 'tests': result.testsRun,
                     'failures': len(result.failures), 'errors': len(result.errors),
                     'unexpected_errors': sum(not issubclass(t, kernel.ContractError) for t in result.error_types),
                     'detected': not result.wasSuccessful(), 'log': log.getvalue()})
    return rows


if __name__ == '__main__':
    rows = run_mutations()
    print(json.dumps(rows, indent=2))
    raise SystemExit(not all(row['detected'] and row['unexpected_errors'] == 0 for row in rows))
