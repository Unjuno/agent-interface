import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent


def test_measurement_mapping():
    class E(ValueError): pass
    class W: start_ns=100; end_ns=700; duration_ns=600
    pkg=types.ModuleType('container_interruption_v1')
    occ=types.ModuleType('container_interruption_v1.occupancy')
    def analyze(events, identifier, start, end):
        assert events==[{'x':1}] and identifier=='p' and (start,end)==(100,700)
        return {'intent_token':'t','window_ns':600,'retained_lower_ns':200,'retained_upper_ns':240,
                'no_input_lower_ns':360,'no_input_upper_ns':400,'admission_count':2,
                'explicit_release_count':2,'measurement_class':'NORMAL_DIRECT_OR_EMPTY'}
    occ.analyze_program=analyze;occ.EvidenceError=E
    sys.modules['container_interruption_v1']=pkg;sys.modules['container_interruption_v1.occupancy']=occ
    spec=importlib.util.spec_from_file_location('m4',HERE/'map01_recovery_cover_mechanism_v4_measurement.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    out=mod.fallback_input_bounds([{'x':1}],'p',W())
    assert out['valid'] and out['retained_input_lower_bound_ns']==200 and out['no_retained_input_upper_bound_ns']==400


def test_missing_release_never_becomes_zero():
    class E(ValueError): pass
    class W: start_ns=100; end_ns=700; duration_ns=600
    pkg=types.ModuleType('container_interruption_v1');occ=types.ModuleType('container_interruption_v1.occupancy')
    def analyze(*args): raise E('completed program has missing/unverified direct release')
    occ.analyze_program=analyze;occ.EvidenceError=E
    sys.modules['container_interruption_v1']=pkg;sys.modules['container_interruption_v1.occupancy']=occ
    spec=importlib.util.spec_from_file_location('m4b',HERE/'map01_recovery_cover_mechanism_v4_measurement.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    out=mod.fallback_input_bounds([], 'p', W())
    assert out['valid'] is False and out['retained_input_lower_bound_ns'] is None and out['no_retained_input_upper_bound_ns'] is None


def test_runner_configure():
    base=types.ModuleType('map01_recovery_cover_matched_v2_runner')
    base.ALLOCATION_ID='old';base.EXPECTED_WORKFLOW_PATH='old';base.fallback_input_bounds=lambda *a:None;base.main=lambda:None
    measure=types.ModuleType('map01_recovery_cover_mechanism_v4_measurement')
    def f(*args): return {'valid':True}
    measure.fallback_input_bounds=f
    sys.modules['map01_recovery_cover_matched_v2_runner']=base;sys.modules['map01_recovery_cover_mechanism_v4_measurement']=measure
    spec=importlib.util.spec_from_file_location('r4',HERE/'map01_recovery_cover_mechanism_v4_runner.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);got=mod.configure()
    assert got is base and base.ALLOCATION_ID=='map01-recovery-cover-mechanism-live-v4-01'
    assert base.EXPECTED_WORKFLOW_PATH=='.github/workflows/map01-recovery-cover-mechanism-live-v4-01.yml' and base.fallback_input_bounds is f


def writej(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj)+'\n')
def writejl(path,rows):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(x)+'\n' for x in rows))

def build(root,reduction=.20,negative=0,missed=0):
    writej(root/'construction.json',{'allocation_id':'map01-recovery-cover-mechanism-live-v4-01','model_calls':0,'planner_wait_ms':600})
    pairs=[]
    for i in (1,2,3):
        pairs.append({'pair_index':i,'failures':([f'COAST_CONTROL:scorer_missed_period'] if missed else []),'coast_no_retained_input_upper_ns':600,'recovery_no_retained_input_upper_ns':int(600*(1-reduction)),'recovery_positive_event_count':0,'recovery_negative_event_count':negative})
        for arm in ('coast_control','bounded_recovery'):
            ar=root/f'pair-{i:02d}'/arm;rt=ar/'runtime';rows=[{'event':'x'}]
            writejl(rt/'events.jsonl',rows);writejl(rt/'delivered.jsonl',rows);writej(rt/'scorer-summary.json',{'scheduler':{'missed_sample_periods':missed}})
            writej(ar/'terminal-score-audit.json',{'pass':True});writej(ar/'arm-summary.json',{'terminal_release_verified':True,'input_bounds':{'valid':True,'admission_count':0 if arm=='coast_control' else 1,'measurement_class':'NORMAL_DIRECT_OR_EMPTY'}})
    writej(root/'summary.json',{'pairs':pairs})


def audit_module():
    spec=importlib.util.spec_from_file_location('a4',HERE/'audit_map01_recovery_cover_mechanism_v4.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def test_audit_pass_allows_descriptive_miss():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);build(root,missed=1);out=audit_module().audit(root);assert out['decision']=='PASS_MECHANISM_ONLY' and out['valid_experiment']
def test_audit_hold_on_weak_continuity():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);build(root,reduction=.05);out=audit_module().audit(root);assert out['decision']=='HOLD' and out['valid_experiment']
def test_audit_fail_on_negative():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);build(root,negative=1);out=audit_module().audit(root);assert out['decision']=='FAIL' and not out['valid_experiment']
def test_audit_fail_on_missing_recovery_exposure():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);build(root);p=root/'pair-01/bounded_recovery/arm-summary.json';row=json.loads(p.read_text());row['input_bounds']['admission_count']=0;writej(p,row);assert audit_module().audit(root)['decision']=='FAIL'
def test_audit_fail_on_terminal_disagreement():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);build(root);writej(root/'pair-02/coast_control/terminal-score-audit.json',{'pass':False});assert audit_module().audit(root)['decision']=='FAIL'


def test_prereg():
    p=json.loads((HERE/'map01_recovery_cover_mechanism_v4_prereg.json').read_text())
    assert p['schema']=='map01-recovery-cover-mechanism-v4-prereg' and p['allocation_id']=='map01-recovery-cover-mechanism-live-v4-01'
    assert p['supersedes']['workflow_run_id']==34974265196 and p['supersedes']['disposition']=='CONSTRUCTION_PREFLIGHT_FAILURE_NO_FORMAL_STEP_EXECUTED'
    assert p['dependencies']['windowed_union_occupancy_commit']=='a74c5cb704c17bc63e6d73aa98a4bac62d738c47'
    c=p['fixed_condition'];assert c['pairs']==3 and c['planner_wait_ms']==600 and c['model_calls']==0
    assert p['measurement']['schema']=='windowed-any-key-occupancy-v1' and 'never zero occupancy' in p['measurement']['missing_completed_release']
    assert set(p['decision'])=={'PASS_MECHANISM_ONLY','HOLD','FAIL'} and all(p['freeze_protocol'].values())

if __name__=='__main__':
    tests=sorted((n,f) for n,f in globals().items() if n.startswith('test_'))
    for name,fn in tests:fn();print('PASS',name)
    print('PASS total',len(tests))
