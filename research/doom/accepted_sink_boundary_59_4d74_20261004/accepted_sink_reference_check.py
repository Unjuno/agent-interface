import sys,time,json
from pathlib import Path
sys.path.insert(0,'/study/accepted-sink-source-01')
sys.path.insert(0,'/study')
from accepted_sink_reference import Executor
from types import SimpleNamespace
results=[]
for case in ['raise_before_accept','accept_then_raise']:
 observed=[]
 def emit(event):
  if case=='accept_then_raise':observed.append(event)
  raise RuntimeError('injected accepted sink failure')
 backend=SimpleNamespace(sequence=0,validate=lambda steps:None)
 executor=Executor(backend,emit);submit_error=close_error=None
 try:executor.submit('probe',[],0,time.perf_counter_ns()+1000000000)
 except Exception as e:submit_error=repr(e)
 before={'active':executor.active,'receipts':executor.prestart_failure_receipts}
 try:executor.close()
 except Exception as e:close_error=repr(e)
 results.append({'case':case,'submit_error':submit_error,'before_close':before,'close_error':close_error,'closed':executor.closed,'active_remains':executor.active is not None,'events':observed})
r={'scope':'additive prestart reference over exact peer executor; no worker/game/model/input starts','results':results};Path('/out/RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))

assert all(x['close_error'] is None and x['closed'] and not x['active_remains'] and len(x['before_close']['receipts'])==1 for x in results)
