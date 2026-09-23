import json,sys,time
sys.path.insert(0,'/workspace')
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.backends.x11_v1.backend import X11ExecutionError
from runtime.core_v1.contract import OFFICE_FLOOR, SCHEMA_PROGRAM, validate_program

class FakeBackend:
    def __init__(self, mode='normal'):
        self.mode=mode; self.emissions=0; self.events=[]
    def monotonic_ns(self): return time.monotonic_ns()
    def manifest(self):
        caps={k:{'state':'supported','detail':'fault-fixture'} for k in OFFICE_FLOOR}
        return {'schema':'agent-interface/backend-v1','backend_id':'fault_fixture','platform':{'os':'linux','backend':'x11-fault-fixture'},'capabilities':caps,'coordinate_frames':['window_client'],'clock':{'unit':'ns','monotonic':True},'permissions':[]}
    def preflight(self,program):
        self.events.append('preflight')
        if self.mode=='preflight_fail': raise RuntimeError('preflight fault')
    def execute(self,program):
        self.events.append('execute'); self.emissions += 1
        if self.mode=='execute_fail':
            raise X11ExecutionError({'error':'execute fault','emissions':1,'releases':[],'status':'failed'})
        if self.mode=='release_fail':
            return {'emissions':self.emissions,'releases':[{'keys_down':['A'],'buttons_down':[],'verified':False}]}
        return {'emissions':self.emissions,'releases':[{'keys_down':[],'buttons_down':[],'verified':True}]}
    def release_all(self):
        self.events.append('release')
        if self.mode=='release_fail': raise RuntimeError('release fault')
        return {'keys_down':[],'buttons_down':[],'verified':True}

PROGRAM={'schema':SCHEMA_PROGRAM,'program_id':'safety3066','source':{'observation_seq':1,'binding_revision':1},'authority':{'lease_id':'safety','expires_at_ns':time.monotonic_ns()+10_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'release_all'}]}
try: validate_program(PROGRAM)
except Exception as e: print(json.dumps({'decision':'STOP_SAFETY_INFRASTRUCTURE','validation_error':repr(e)})); raise SystemExit(1)
DECLARED=['caller','session','core_admission','preflight','execute','release_receipt','cleanup']
def run(mode,obs=1):
 b=FakeBackend(mode); s=X11RuntimeSession(b)
 try: result=s.dispatch(PROGRAM,current_observation_seq=obs,current_binding_revision=1)
 except Exception as exc: result={'status':'exception','error':repr(exc),'recovery_required':s.recovery_required}
 observed=['caller','session','core_admission']+b.events+(['release_receipt'] if result.get('execution',{}).get('releases') or result.get('release') else [])+['cleanup']
 return {'mode':mode,'result':result,'events':b.events,'observed_dependencies':sorted(set(observed)),'undeclared':sorted(set(observed)-set(DECLARED)),'recovery_required':s.recovery_required}
rows=[run('normal'),run('execute_fail'),run('release_fail'),run('normal',obs=0)]
print(json.dumps({'decision':'PASS_SAFETY_GRAPH_RUNTIME_RECONCILIATION_SCOPED' if all(not r['undeclared'] for r in rows) and rows[0]['result'].get('status')=='completed' and rows[1]['result'].get('status')=='execution_failed' and rows[3]['result'].get('status')=='refused' else 'HOLD_SAFETY_GRAPH_EVIDENCE_INCOMPLETE','declared_dependencies':DECLARED,'rows':rows,'model_calls':0,'network_calls':0},sort_keys=True))
