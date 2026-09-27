import importlib.util
import sys
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(fake_result):
    base=types.ModuleType('audit_map01_recovery_cover_mechanism_v4')
    base.ALLOCATION_ID='v4-id'
    seen=[]
    def audit(root):
        seen.append((Path(root),base.ALLOCATION_ID))
        out=dict(fake_result);out.setdefault('schema','map01-recovery-cover-mechanism-v4-audit');out.setdefault('allocation_id',base.ALLOCATION_ID)
        return out
    base.audit=audit
    sys.modules['audit_map01_recovery_cover_mechanism_v4']=base
    spec=importlib.util.spec_from_file_location('a5',HERE/'audit_map01_recovery_cover_mechanism_v5.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,base,seen


def test_allocation_substitution_and_restore():
    mod,base,seen=load({'decision':'PASS_MECHANISM_ONLY','valid_experiment':True})
    out=mod.audit(Path('/tmp/x'))
    assert seen==[(Path('/tmp/x'),'map01-recovery-cover-mechanism-live-v5-01')]
    assert base.ALLOCATION_ID=='v4-id'
    assert out['allocation_id']=='map01-recovery-cover-mechanism-live-v5-01'
    assert out['schema']=='map01-recovery-cover-mechanism-v5-audit'


def test_failure_semantics_preserved():
    mod,_,_=load({'decision':'FAIL','valid_experiment':False,'hard_failures':['x']})
    out=mod.audit(Path('/tmp/x'))
    assert out['decision']=='FAIL' and not out['valid_experiment'] and out['hard_failures']==['x']


def test_hold_semantics_preserved():
    mod,_,_=load({'decision':'HOLD','valid_experiment':True,'hold_reasons':['weak']})
    out=mod.audit(Path('/tmp/x'))
    assert out['decision']=='HOLD' and out['valid_experiment'] and out['hold_reasons']==['weak']

if __name__=='__main__':
    tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
    for n,f in tests:f();print('PASS',n)
    print('PASS total',len(tests))
