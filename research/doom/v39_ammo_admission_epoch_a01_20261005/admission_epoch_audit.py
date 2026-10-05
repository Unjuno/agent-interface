import ast, hashlib, json
from pathlib import Path
def blob(path):
 b=Path(path).read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
baseline=Path('admission-controller-baseline.py').read_text(encoding='utf-8')
candidate=Path('admission-controller-candidate.py').read_text(encoding='utf-8')
test=Path('admission-regression-test-candidate.py').read_text(encoding='utf-8')
assert blob('admission-controller-baseline.py')=='d42df13b36ec56eaaf316a12675deab08736b003'
assert blob('admission-controller-candidate.py')=='304ec68c03eb5f10e9130d40f8af8d2bcf5c889f'
assert blob('admission-regression-test-candidate.py')=='36e6a10bfdc73c2af4a1f02087005bb95d300625'
fn='def prepare_action_admission('
base_fn=baseline[baseline.index(fn):baseline.index('\n\nclass DoomRunningActionMonitor')]
candidate_fn=candidate[candidate.index(fn):candidate.index('\n\nclass DoomRunningActionMonitor')]
assert 'type(signal[field]) is not int' not in base_fn
assert candidate_fn.index('type(signal[field]) is not int') < candidate_fn.index('current_ammo["sequence"] != current_health["sequence"]')
tree=ast.parse(test)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PairedCoverGuardTests')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_current_action_admission_rejects_float_epoch_metadata')
assert sum(1 for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='assertRaisesRegex')==1
assert '("sequence", 4.0)' in test and '("capture_ns", 40.0)' in test
assert 'self.assertEqual(snapshot["sequence"], 4)' in test and 'self.assertEqual(snapshot["capture_ns"], 40)' in test
red=Path('red-output.txt').read_text(encoding='utf-8-sig')
assert red.count('ValueError not raised')==2, red.count('ValueError not raised')
green=Path('green-output.txt').read_text(encoding='utf-8-sig')
assert 'Ran 1 test' in green and 'OK' in green
print(json.dumps({'audit':'PASS_PINNED_TDD_EVIDENCE_AUDIT','baseline_blob':blob('admission-controller-baseline.py'),'candidate_blob':blob('admission-controller-candidate.py'),'test_blob':blob('admission-regression-test-candidate.py'),'float_counterexamples_red':2,'focused_candidate_tests_green':1,'integer_control_preserved':True},sort_keys=True))