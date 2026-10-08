from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent

def source(name): return (ROOT/'source'/name).read_text(encoding='utf-8')
def module(name): return ast.parse(source(name))
def function(tree,name,parent=None):
    root=tree if parent is None else parent
    matches=[n for n in ast.walk(root) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(matches)!=1: raise AssertionError(f'expected one function {name}, found {len(matches)}')
    return matches[0]
def has_call(node, attr):
    return any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr==attr for n in ast.walk(node))
def const_event(node,event):
    for n in ast.walk(node):
        if isinstance(n,ast.Dict) and any(isinstance(k,ast.Constant) and k.value=='event' and isinstance(v,ast.Constant) and v.value==event for k,v in zip(n.keys,n.values)): return True
        if isinstance(n,ast.Call) and any(k.arg=='event' and isinstance(k.value,ast.Constant) and k.value.value==event for k in n.keywords): return True
    return False
def line(path,node): return {'file':path,'line':node.lineno}

freeze=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
all_sources=[freeze['source'],*freeze['additional_sources'],*freeze['runtime_sources']]
verified=[]
for item in all_sources:
    p=ROOT/item['local_path']; data=p.read_bytes()
    assert len(data)==item['bytes']
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    actual=subprocess.check_output(['git','hash-object','--no-filters',str(p)],text=True).strip()
    assert actual==item['git_blob'],(item['local_path'],actual)
    verified.append(item['git_blob'])

controller=module('map01_overlap_controller_v39.py')
main=function(controller,'main')
reader=function(controller,'reader',main)
reader_for=next(n for n in ast.walk(reader) if isinstance(n,ast.For))
assert isinstance(reader_for.iter,ast.Attribute) and reader_for.iter.attr=='stdout'
reader_calls=[n for n in ast.walk(reader_for) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='put']
assert len(reader_calls)==1 and isinstance(reader_calls[0].func.value,ast.Name) and reader_calls[0].func.value.id=='incoming'
reader_call=reader_calls[0]
reader_decode=[n for n in ast.walk(reader_for) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='loads']
assert len(reader_decode)==1 and reader_decode[0].lineno==reader_call.lineno
wait=function(controller,'wait',main)
wait_text=ast.get_source_segment(source('map01_overlap_controller_v39.py'),wait)
assert wait_text.index('observation_monitor.observe(row)') < wait_text.index('if predicate(row)')
assert source('map01_overlap_controller_v39.py').count('incoming.put(row)')==1

session=module('session_map01_v12.py')
session_main=function(session,'main')
emit=function(session,'emit',session_main)
writer_with=next(n for n in emit.body if isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Name) and i.context_expr.id=='lock' for i in n.items))
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='print' and any(k.arg=='flush' and isinstance(k.value,ast.Constant) and k.value.value is True for k in n.keywords) for n in ast.walk(writer_with))

coast_typed=module('doom_typed_coast_backend_v1.py')
snapshot=function(coast_typed,'snapshot',next(n for n in coast_typed.body if isinstance(n,ast.ClassDef) and n.name=='Backend'))
assert const_event(snapshot,'observation') and has_call(snapshot,'emit')
coast=module('coast_backend_v1.py')
coast_backend=next(n for n in coast.body if isinstance(n,ast.ClassDef) and n.name=='Backend')
execute=function(coast,'execute',coast_backend)
assert has_call(execute,'snapshot') and const_event(execute,'coast_result')

executor5=module('executor_v5.py')
run=function(executor5,'_run')
backend_execute=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute' and isinstance(n.func.value,ast.Attribute) and n.func.value.attr=='backend')
terminal_emit=next(n for n in ast.walk(run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='emit' and const_event(n,'terminal'))
assert backend_execute.lineno < terminal_emit.lineno

v12=module('session_map01_v12.py')
v12text=source('session_map01_v12.py')
assert 'from executor_v12 import Executor' in v12text
assert 'Executor(backend, emit)' in v12text
v15text=source('session_map01_v15.py')
assert 'base.Executor=ReleaseOrderedExecutor' in v15text
assert 'base.main()' in v15text

# Census direct snapshot producers in the session process. Only startup and
# fixture setup call the backend directly; active samples occur inside execute.
session_main=function(v12,'main')
direct_snapshots=[]
for n in ast.walk(session_main):
    if (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='snapshot' and
        isinstance(n.func.value,ast.Name) and n.func.value.id=='backend'):
        arg=n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else None
        direct_snapshots.append((arg,n))
assert [x[0] for x in direct_snapshots]==['initial','fixture-source']
ready_emit=next(n for n in ast.walk(session_main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='emit' and const_event(n,'ready'))
stdin_loop=next(n for n in ast.walk(session_main) if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute) and isinstance(n.iter.value,ast.Name) and n.iter.value.id=='sys' and n.iter.attr=='stdin')
initial_call=direct_snapshots[0][1]; fixture_call=direct_snapshots[1][1]
assert ready_emit.lineno < initial_call.lineno < stdin_loop.lineno
controller_text=source('map01_overlap_controller_v39.py')
session_command=function(controller,'session_command')
session_command_text=ast.get_source_segment(controller_text,session_command)
assert '--fixture-out' not in session_command_text and '--load-fixture-manifest' in session_command_text
finish_branch=next(n for n in ast.walk(session_main) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(c,ast.Constant) and c.value=='finish' for c in n.test.comparators))
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='snapshot' for n in ast.walk(finish_branch))
finish_close=next(n for n in ast.walk(finish_branch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='close' and isinstance(n.func.value,ast.Name) and n.func.value.id=='executor')
score_emit=next(n for n in ast.walk(finish_branch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='emit' and n.args and isinstance(n.args[0],ast.Name) and n.args[0].id=='score')
assert finish_close.lineno < score_emit.lineno

# Legacy, typed, and coast observations are synchronous inside the active
# backend.execute call; derived executor workers publish terminal afterward.
execute_sites={}
for filename in ('session_v8.py','session_v9.py','session_v10.py','coast_backend_v1.py'):
    tree=module(filename)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Backend')
    methods=[n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='execute']
    assert len(methods)==1,filename
    method=methods[0]
    assert has_call(method,'snapshot') or has_call(method,'execute')
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('Thread','submit') for n in ast.walk(method))
    execute_sites[filename]=line(filename,method)

v13_tree=module('executor_v13.py')
v13_cls=next(n for n in v13_tree.body if isinstance(n,ast.ClassDef) and n.name=='Executor')
v13_run=function(v13_tree,'_run_with_watcher_cleanup',v13_cls)
v13_backend_execute=next(n for n in ast.walk(v13_run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='execute' and isinstance(n.func.value,ast.Attribute) and n.func.value.attr=='backend')
v13_terminal_emit=next(n for n in ast.walk(v13_run) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='emit' and n.args and isinstance(n.args[0],ast.Name) and n.args[0].id=='terminal')
assert v13_backend_execute.lineno < v13_terminal_emit.lineno

# v12 has no worker override and inherits v5's execute-before-terminal loop.
v12_exec_tree=module('executor_v12.py')
v12_cls=next(n for n in v12_exec_tree.body if isinstance(n,ast.ClassDef) and n.name=='Executor')
assert not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ('_run','_run_with_watcher_cleanup') for n in v12_cls.body)
assert '--fixture-out' not in session_command_text

evidence={
 'status':'PASS_SOURCE_VERIFIED_OBSERVATION_BEFORE_TERMINAL_FIFO',
 'main_commit':freeze['current_main_commit'],
 'verified_git_blobs':verified,
 'properties':{
  'single_stdout_reader_decodes_then_enqueues_before_next_line':True,
  'only_reader_producer_to_incoming_queue':True,
  'session_emitter_serializes_and_flushes_each_json_line_under_lock':True,
  'coast_observation_emitted_synchronously_during_backend_execute':True,
  'executor_terminal_emitted_after_backend_execute_returns':True,
  'wait_observes_policy_event_before_terminal_predicate':True,
  'default_v12_and_opt_in_v15_use_the_serialized_session_emitter':True,
  'active_observations_are_synchronous_inside_executor_backend_execute':True,
  'only_direct_snapshots_are_startup_or_disabled_fixture_setup':True,
  'controller_session_command_disables_fixture_out':True,
  'finish_path_closes_executor_then_emits_score_without_snapshot':True,
  'no_active_post_terminal_observation_producer_in_pinned_session_route':True,
  'default_v12_inherits_v5_execute_before_terminal_loop':True,
  'opt_in_v13_executes_backend_before_terminal':True
 },
 'scope':'Static current-main source ordering proof; no live pipe scheduling, model, HUD cadence, game, OS input, release timing or task outcome.',
 'anchors':{
  'controller_reader':line('map01_overlap_controller_v39.py',reader),
  'controller_wait':line('map01_overlap_controller_v39.py',wait),
  'session_emit':line('session_map01_v12.py',emit),
  'coast_snapshot':line('doom_typed_coast_backend_v1.py',snapshot),
  'coast_execute':line('coast_backend_v1.py',execute),
  'executor_run':line('executor_v5.py',run),
  'executor_backend_execute':line('executor_v5.py',backend_execute),
  'executor_terminal_emit':line('executor_v5.py',terminal_emit),
  'startup_snapshot':line('session_map01_v12.py',initial_call),
  'fixture_only_snapshot':line('session_map01_v12.py',fixture_call),
  'finish_executor_close':line('session_map01_v12.py',finish_close),
  'finish_score_emit':line('session_map01_v12.py',score_emit),
  'executor_v13_backend_execute':line('executor_v13.py',v13_backend_execute),
  'executor_v13_terminal_emit':line('executor_v13.py',v13_terminal_emit),
  'backend_execute_sites':execute_sites
 }
}
(ROOT/'PIPELINE_AUDIT.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(json.dumps(evidence,sort_keys=True))
