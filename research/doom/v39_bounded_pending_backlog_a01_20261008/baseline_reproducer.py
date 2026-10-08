import ast, hashlib, json, queue, subprocess, threading
from types import MethodType, SimpleNamespace
EXPECTED_MAIN = '6ea1269defb6d48a607f13b08f1aa2d223ba06e9'
main = subprocess.check_output(['git','rev-parse',EXPECTED_MAIN], text=True).strip()
assert main == EXPECTED_MAIN
controller_path='research/doom/map01_overlap_controller_v39.py'
executor_path='research/live_control/executor_v12.py'
controller=subprocess.check_output(['git','show',f'{EXPECTED_MAIN}:{controller_path}'])
executor=subprocess.check_output(['git','show',f'{EXPECTED_MAIN}:{executor_path}'])
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def sha(data): return hashlib.sha256(data).hexdigest()
ct=ast.parse(controller)
node=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=='drain_pending_observation_events')
ns={'queue':queue}
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<pinned-v39-drain>','exec'),ns)
q=queue.Queue()
class Monitor:
    event_types={'observation','typed_observation'}
    def __init__(self): self.seen=[]
    def observe(self,row):
        self.seen.append(row['sequence'])
        if row['sequence']==11:
            q.put({'event':'typed_observation','sequence':12,'health':60,'crosses_floor':True})
        if row['sequence']==12:
            return {'event':'policy_invalidation','reason':'health:below_hard_minimum'}
        return None
q.put({'event':'observation','sequence':11,'health':90,'crosses_floor':False})
monitor=Monitor()
# Same control state as main after its terminal has already been consumed.
current_terminal={'event':'terminal','id':'cover-0','status':'completed','release':{'verified':True,'keys_down':[],'buttons_down':[]}}
drained=ns['drain_pending_observation_events'](q,monitor,'cover-0')
latest=drained['latest']
queued=q.get_nowait()
# The production caller waits for the terminal only when current_terminal is None.
source=controller.decode('utf-8').splitlines()
wait_branch=next(i for i,line in enumerate(source) if 'if current_terminal is None:' in line and i>990)
final_admission=next(i for i,line in enumerate(source) if 'final_action_admission=final_admission_from_planner_result(' in line)
assert latest['sequence']==11 and queued['sequence']==12
assert drained['invalidation'] is None
assert current_terminal is not None and wait_branch < final_admission
# Exact ExecutorV12.submit rejects the stale expected_sequence before any admission.
et=ast.parse(executor)
cls=next(n for n in et.body if isinstance(n,ast.ClassDef) and n.name=='Executor')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='submit')
method_ns={'Lease':object}
exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<pinned-executor-submit>','exec'),method_ns)
fake=SimpleNamespace(lock=threading.Lock(),closed=False,active=None,backend=SimpleNamespace(sequence=12),used_ids=set())
try:
    MethodType(method_ns['submit'],fake)('stale-plan',[{'op':'observe'}],latest['sequence'],0)
except ValueError as exc:
    rejection=str(exc)
else:
    raise AssertionError('stale sequence unexpectedly accepted')
assert rejection=='latest observation sequence required before input'
result={'schema':'currentmain-v39-pending-drain-race-a01-v1','status':'REPRODUCED_STALE_ANSWER_REACHES_EXECUTOR_REJECTION_WITHOUT_REPLAN','main_commit':main,'sources':{controller_path:{'git_blob':blob(controller),'sha256':sha(controller)},executor_path:{'git_blob':blob(executor),'sha256':sha(executor)}},'drain':{'latest_sequence_used':latest['sequence'],'hard_crossing_sequence_left_queued':queued['sequence'],'invalidation_returned':drained['invalidation'],'current_terminal_already_present':True,'caller_wait_branch_skipped':True},'executor':{'backend_sequence':12,'submitted_expected_sequence':11,'outcome':'rejected','reason':rejection},'scope':'Exact production drain helper and ExecutorV12.submit with deterministic queue schedule; caller branch/order checked in exact controller source; no live App Server, game, model, GUI, or OS input.'}
print(json.dumps(result,indent=2))

