import importlib.util,json,sys,tempfile,types
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(fake):
    b=types.ModuleType('audit_map01_recovery_cover_mechanism_v4');b.ALLOCATION_ID='old';b.audit=lambda root:dict(fake)
    sys.modules['audit_map01_recovery_cover_mechanism_v4']=b
    spec=importlib.util.spec_from_file_location('a6',HERE/'audit_map01_recovery_cover_mechanism_v6.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m,b

def build(root,phase='immediately_after_delay_before_fallback_cleanup'):
    for i in (1,2,3):
        for arm in ('coast_control','bounded_recovery'):
            p=root/f'pair-{i:02d}'/arm/'arm-summary.json';p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps({'planner_window':{'duration_ns':600_000_000,'end_boundary_phase':phase}}))

def test_valid_phase_preserves_pass():
    with tempfile.TemporaryDirectory() as d:
        r=Path(d);build(r);m,b=load({'decision':'PASS_MECHANISM_ONLY','valid_experiment':True,'hard_failures':[],'promotable_mechanism_result':True});out=m.audit(r)
        assert out['decision']=='PASS_MECHANISM_ONLY' and out['valid_experiment'] and not out['planner_boundary_failures'];assert b.ALLOCATION_ID=='old'

def test_wrong_phase_fails():
    with tempfile.TemporaryDirectory() as d:
        r=Path(d);build(r,'after_cleanup');m,_=load({'decision':'PASS_MECHANISM_ONLY','valid_experiment':True,'hard_failures':[],'promotable_mechanism_result':True});out=m.audit(r)
        assert out['decision']=='FAIL' and not out['valid_experiment'] and len(out['planner_boundary_failures'])==6

def test_missing_summary_fails():
    with tempfile.TemporaryDirectory() as d:
        r=Path(d);m,_=load({'decision':'PASS_MECHANISM_ONLY','valid_experiment':True,'hard_failures':[],'promotable_mechanism_result':True});out=m.audit(r)
        assert out['decision']=='FAIL' and not out['valid_experiment']
if __name__=='__main__':
    tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
    for n,f in tests:f();print('PASS',n)
    print('PASS total',len(tests))
