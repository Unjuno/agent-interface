"""Execute current-main executor freshness gate for late observation schedule."""
import ast, hashlib, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED={
'map01_overlap_controller_v39.py':'02a6289390837bb97198c98fe03c41c775d829bf6606fc4c11085630b3de0793',
'session_map01_v12.py':'97d60f64ae6dc075fd7b18a452813c90d7c5d366d71e324905c17d74604585b2',
'doom_typed_coast_backend_v1.py':'fda541e12414d6c77b41787eaf208e8dae6b462846ad401d4c7b235b8ae2b079',
'executor_v12.py':'e78440263866dd06eaf868e902ae50b08aa2b634f086bfbd412f6c338ccea2b2',}
for name,want in EXPECTED.items():
 got=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(); assert got==want,(name,got)
controller=(ROOT/'map01_overlap_controller_v39.py').read_text()
backend=(ROOT/'doom_typed_coast_backend_v1.py').read_text()
session=(ROOT/'session_map01_v12.py').read_text()
# Verify the production flow that creates the race and its stale expected_sequence.
assert 'for _ in range(incoming.qsize())' in controller
assert 'if future.done() and invalidation is None:' in controller
assert 'fresh_before_plan=dict(latest)' in controller
assert '"expected_sequence":latest["sequence"]' in controller
assert 'if accepted["event"]!="accepted":raise RuntimeError(accepted)' in controller
assert 'self.sequence += 1' in backend and backend.index('self.sequence += 1') < backend.index('self.emit(typed)')
assert 'incoming.put(row)' in controller
assert 'expected_sequence != self.backend.sequence' in (ROOT/'executor_v12.py').read_text()
# Execute the exact current-main Executor.submit method AST. Stale controller sequence
# 1 meets producer/backend sequence 2 because a newer typed observation was emitted.
tree=ast.parse((ROOT/'executor_v12.py').read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Executor')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='submit')
module=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='HarnessExecutor',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
ns={}; exec(compile(module,str(ROOT/'executor_v12.py'),'exec'),ns)
class Lock:
 def __enter__(self): return self
 def __exit__(self,*args): return False
class Backend:
 sequence=2
 def validate(self,steps): raise AssertionError('validation must not run after stale sequence rejection')
class Harness:
 pass
x=ns['HarnessExecutor'](); x.lock=Lock(); x.closed=False; x.active=None; x.backend=Backend(); x.used_ids=set(); x.emit=lambda row: (_ for _ in ()).throw(AssertionError('no event/input emission expected'))
try:
 x.submit('late-action',[{'op':'observe'}],1,10**30)
except ValueError as e:
 reason=str(e)
else:
 raise AssertionError('stale expected_sequence unexpectedly passed')
assert reason=='latest observation sequence required before input'
# Execute the exact current-main nested controller execute_segment function with
# its real rejected-response branch and deterministic process/queue fakes.
ctree=ast.parse(controller)
main_fn=next(n for n in ctree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
segment=next(n for n in ast.walk(main_fn) if isinstance(n,ast.FunctionDef) and n.name=='execute_segment')
outer=ast.FunctionDef(name='make_segment',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[
 ast.Assign(targets=[ast.Name(id='program_admissions',ctx=ast.Store())],value=ast.Constant(0)),
 ast.Assign(targets=[ast.Name(id='first_accepted',ctx=ast.Store())],value=ast.Constant(None)),
 ast.Assign(targets=[ast.Name(id='final_action_admission',ctx=ast.Store())],value=ast.Dict(keys=[],values=[])),
 segment,ast.Return(value=ast.Name(id='execute_segment',ctx=ast.Load()))],decorator_list=[])
controller_ns={'json':json,'time':time}
exec(compile(ast.fix_missing_locations(ast.Module(body=[outer],type_ignores=[])),str(ROOT/'map01_overlap_controller_v39.py'),'exec'),controller_ns)
class Stdin:
 def __init__(self): self.data=''
 def write(self,value): self.data+=value
 def flush(self): pass
class Process: pass
controller_process=Process(); controller_process.stdin=Stdin()
rejected={'event':'rejected','reason':reason}
controller_ns.update({'latest':{'sequence':1},'all_events':[],'process':controller_process,
 'compile_commands':lambda commands:[{'op':'observe'}], 'wait':lambda predicate,**kw:rejected})
try:
 controller_ns['make_segment']()('late-plan',[{'action':'observe'}],'primary',[0])
except RuntimeError as e:
 controller_error=str(e)
else:
 raise AssertionError('current controller did not propagate executor rejection')
submitted=json.loads(controller_process.stdin.data.strip())
assert submitted['expected_sequence']==1 and controller_error==str(rejected)
controller_result={'rejection_propagates_as_runtime_error':True,'submitted_expected_sequence':submitted['expected_sequence'],'submit_attempts':1,'retry_or_accept_event_count':0,'disposition':'segment aborts into controller failure cleanup'}
result={'schema':'issue59-v39-late-observation-executor-gate-a01','main_commit':'bfcc14e08fbfe5f2f04cd0237d13559e5d62538b','source_sha256':EXPECTED,'scenario':{'controller_latest_sequence':1,'late_typed_observation_sequence':2,'producer_backend_sequence_at_submit':2,'executor_expected_sequence':1},'exact_executor_method_result':{'rejected':True,'reason':reason,'accepted_or_input_events':0},'controller_rejection_disposition':controller_result,'decision':'PASS_FAIL_CLOSED_NO_STALE_EXECUTOR_ADMISSION; CONTROLLER_SEGMENT_ABORTS; SESSION_CONTINUITY_NOT_ESTABLISHED','scope':'Synthetic late-event schedule; exact current-main Executor.submit and nested execute_segment ASTs. No full Doom backend, queue process, GUI, model, OS input, game, or live threat/recovery run.'}
(ROOT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
