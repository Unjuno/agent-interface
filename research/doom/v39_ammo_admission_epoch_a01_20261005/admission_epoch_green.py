import ast, sys, types, unittest
from unittest.mock import patch
from pathlib import Path
source=Path('admission-controller-candidate.py').read_text(encoding='utf-8')
controller_tree=ast.parse(source)
prepare=next(n for n in controller_tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_action_admission')
controller=types.ModuleType('controller')
controller.bindings_equal_exact=lambda left,right: left==right
controller.SNAPSHOT_FORMAT='action-snapshot-v1'
controller.build_action_contract=None
controller.evaluate_action_validity=None
controller.record_action_validity=None
exec(compile(ast.fix_missing_locations(ast.Module(body=[prepare],type_ignores=[])),'<frozen-prepare-action-admission>','exec'),controller.__dict__)
test_tree=ast.parse(Path('admission-regression-test-candidate.py').read_text(encoding='utf-8'))
signal=next(n for n in test_tree.body if isinstance(n,ast.FunctionDef) and n.name=='signal')
orig_class=next(n for n in test_tree.body if isinstance(n,ast.ClassDef) and n.name=='PairedCoverGuardTests')
test=next(n for n in orig_class.body if isinstance(n,ast.FunctionDef) and n.name=='test_current_action_admission_rejects_float_epoch_metadata')
regression=ast.ClassDef(name='AdmissionEpochTypeRegression',bases=[ast.Attribute(value=ast.Name(id='unittest',ctx=ast.Load()),attr='TestCase',ctx=ast.Load())],keywords=[],body=[test],decorator_list=[])
ns={'ast':ast,'unittest':unittest,'patch':patch,'controller':controller}
exec(compile(ast.fix_missing_locations(ast.Module(body=[signal,regression],type_ignores=[])),'<frozen-admission-test>','exec'),ns)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['AdmissionEpochTypeRegression']))
print(f'CASE_SUMMARY tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)}')
sys.exit(0 if result.wasSuccessful() else 1)