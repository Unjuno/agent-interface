import json,unittest
from unittest.mock import patch
from runtime.backends.win32_v1 import backend as native
names=['runtime.backends.win32_v1.test_release_ledger','runtime.backends.win32_v1.test_explicit_up_ledger','runtime.backends.win32_v1.test_unknown_release_custody','runtime.backends.win32_v1.test_integration.PureWin32HelperTests','runtime.backends.win32_v1.test_integration.Win32SessionRecoveryTests']

names += ['runtime.core_v1.'+n for n in ['test_compiled_admission_custody_01a0ff35','test_compiled_callback_custody_01a0ff35','test_compiled_clock_custody','test_compiled_custody_effect_join_01a0ff35','test_compiled_effect_return_custody_01a0ff35','test_compiled_release_recovery_01a0ff35','test_compiled_terminal_return_custody_01a0ff35']]
names += ['runtime.guarded_win32_v1.'+p.stem for p in __import__('pathlib').Path(__import__('os').environ['AGENT_INTERFACE_TEST_REPO']).joinpath('runtime/guarded_win32_v1').glob('test_*.py')]
with patch.object(native.ctypes,'WinDLL',create=True,side_effect=AssertionError('native DLL forbidden')), patch.object(native.Win32Backend,'__init__',side_effect=AssertionError('native construction forbidden')):
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
print(json.dumps({'selected':names,'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'skipped':len(result.skipped)}))
raise SystemExit(not result.wasSuccessful())
