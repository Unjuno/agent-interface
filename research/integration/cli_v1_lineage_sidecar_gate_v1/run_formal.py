from __future__ import annotations
import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, types
from sidecar import seal_receipt, seal_sidecar, dispatch_with_gate
HERE=pathlib.Path(__file__).parent
EXPECTED_CORE_BLOB='a16620b65d22757ca9160d68feb1381306cc6ac3'
EXPECTED_API_BLOB='58e5489796959f120d973b595f36ed3d808533b3'
EXPECTED_CORE_SHA='268cf282c02f9e2dd38a8c45a36378049443ef2a2431063359011d0552b9c37c'
EXPECTED_API_SHA='1369a408438a013dbca5b891863c0b834f338e657f0937a291064d089eb92900'

def load_core():
    spec=importlib.util.spec_from_file_location('cli_gate_core_exact',HERE/'contract.py'); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

def install_selector_stub(core,state):
    runtime=types.ModuleType('runtime'); runtime.__path__=[]; sys.modules['runtime']=runtime
    sel=types.ModuleType('runtime.selector_v1')
    class BackendUnavailable(RuntimeError): pass
    sel.BackendUnavailable=BackendUnavailable
    sel.select_backend=lambda **kw: None
    class Session:
        def __init__(self,mode): self.mode=mode
        def dispatch(self,program,*,current_observation_seq,current_binding_revision):
            state['session_dispatch_calls'] += 1
            caps=[core.INPUT_POINTER,core.INPUT_RELEASE_ALL,core.DISPLAY_GEOMETRY] if self.mode=='full' else [core.INPUT_RELEASE_ALL,core.DISPLAY_GEOMETRY]
            mf=core.capability_manifest('fake-session','linux','fake',caps)
            a=core.admit_program(program,mf,now_ns=state['now_ns'],current_observation_seq=current_observation_seq,current_binding_revision=current_binding_revision)
            return {'accepted':a.accepted,'error':a.error,'required_capabilities':list(a.required_capabilities)}
    def open_session(targets,display_name=None):
        state['open_session_calls'] += 1
        return Session(state['manifest_mode'])
    sel.open_session=open_session; sys.modules['runtime.selector_v1']=sel

def load_api():
    spec=importlib.util.spec_from_file_location('cli_api_exact',HERE/'api.py'); m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m); return m

def git_blob(p): return subprocess.check_output(['git','hash-object',str(p)],text=True).strip()
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def prog(pid,point,obs,bind,expires=10_000_000_000):
    return {'schema':'agent-interface/program-v1','program_id':pid,'source':{'observation_seq':obs,'binding_revision':bind},'authority':{'lease_id':'lease-1','expires_at_ns':expires},'terminal':{'release_all_required':True},'ops':[{'op':'pointer_move','frame':'screen_physical_px','x':point[0],'y':point[1]},{'op':'release_all'}]}

def receipts():
    hint=seal_receipt({'receipt_id':'hint-1','role':'HINT','currentness':'HISTORICAL','point':[120,140],'observation_seq':10,'binding_revision':3,'source_receipt_id':None})
    cur=seal_receipt({'receipt_id':'cur-1','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':None})
    reval=seal_receipt({'receipt_id':'reval-1','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','point':[420,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':'hint-1'})
    stale=seal_receipt({'receipt_id':'reval-stale','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','point':[420,280],'observation_seq':19,'binding_revision':5,'source_receipt_id':'hint-1'})
    return hint,cur,reval,stale

def run():
    core=load_core()
    if git_blob(HERE/'contract.py')!=EXPECTED_CORE_BLOB or sha(HERE/'contract.py')!=EXPECTED_CORE_SHA: raise SystemExit('core identity mismatch')
    if git_blob(HERE/'api.py')!=EXPECTED_API_BLOB or sha(HERE/'api.py')!=EXPECTED_API_SHA: raise SystemExit('api identity mismatch')
    state={'open_session_calls':0,'session_dispatch_calls':0,'manifest_mode':'full','now_ns':1}
    install_selector_stub(core,state); api=load_api()
    hint,cur,reval,stale=receipts()
    p_cur=prog('p-cur',[420,280],20,5)
    p_hist=prog('p-hist',[120,140],10,3)
    p_launder=prog('p-launder',[120,140],20,5)
    p_reval=prog('p-reval',[420,280],20,5)
    p_stale=prog('p-stale',[420,280],19,5)
    p_expired=prog('p-expired',[420,280],20,5,expires=1)
    wrong_point=seal_receipt({'receipt_id':'wrong-point','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','point':[421,280],'observation_seq':20,'binding_revision':5,'source_receipt_id':'hint-1'})
    wrong_source=seal_receipt({'receipt_id':'wrong-source','role':'ADMISSION_DEPENDENCY','currentness':'CURRENT','point':[420,280],'observation_seq':21,'binding_revision':5,'source_receipt_id':'hint-1'})
    forged=copy.deepcopy(reval); forged['role']='HINT'
    cases=[
      ('direct_current',p_cur,cur,seal_sidecar(p_cur,cur),20,5,1,'full'),
      ('hint_stale_numeric',p_hist,hint,seal_sidecar(p_hist,hint),20,5,1,'full'),
      ('hint_laundered_current_numeric',p_launder,hint,seal_sidecar(p_launder,hint),20,5,1,'full'),
      ('hint_exact_revalidated',p_reval,reval,seal_sidecar(p_reval,reval),20,5,1,'full'),
      ('wrong_point_sidecar',p_reval,wrong_point,seal_sidecar(p_reval,wrong_point),20,5,1,'full'),
      ('wrong_source_sidecar',p_reval,wrong_source,seal_sidecar(p_reval,wrong_source),20,5,1,'full'),
      ('forged_receipt_role',p_reval,forged,seal_sidecar(p_reval,reval),20,5,1,'full'),
      ('stale_revalidation',p_stale,stale,seal_sidecar(p_stale,stale),20,5,1,'full'),
      ('expired_lease',p_expired,cur,seal_sidecar(p_expired,cur),20,5,20_000_000_000,'full'),
      ('missing_pointer_capability',p_cur,cur,seal_sidecar(p_cur,cur),20,5,1,'missing_pointer'),
      ('invalid_current_request',p_cur,cur,seal_sidecar(p_cur,cur),-1,5,1,'full'),
    ]
    rows=[]
    for policy in ('raw_cli','sidecar_gate'):
      for name,p,r,s,current_obs,current_bind,now,mode in cases:
        state.update(open_session_calls=0,session_dispatch_calls=0,manifest_mode=mode,now_ns=now)
        if policy=='raw_cli':
            out=api.dispatch(copy.deepcopy(p),{'T':1},current_observation_seq=current_obs,current_binding_revision=current_bind)
        else:
            out=dispatch_with_gate(api,copy.deepcopy(p),copy.deepcopy(r),copy.deepcopy(s),{'T':1},current_observation_seq=current_obs,current_binding_revision=current_bind)
        rows.append({'policy':policy,'scenario':name,'output':out,'open_session_calls':state['open_session_calls'],'session_dispatch_calls':state['session_dispatch_calls'],'program_point':[p['ops'][0]['x'],p['ops'][0]['y']],'program_source':p['source']})
    return {'task':'CLI-V1-LINEAGE-SIDECAR-GATE-20260917-001','core_blob':EXPECTED_CORE_BLOB,'api_blob':EXPECTED_API_BLOB,'formal_reruns':0,'rows':rows}
if __name__=='__main__': print(json.dumps(run(),sort_keys=True,indent=2))
