import sys,time,json,threading
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=['/study','/study/accepted-sink-source-01']
from accepted_sink_reference import Executor
rows=[]
# Actual worker lifecycle; empty program and stub release are construction only.
events=[];done=threading.Event()
def emit(event):
 events.append(event)
 if event['event']=='terminal':done.set()
backend=SimpleNamespace(sequence=0,validate=lambda steps:None,release_all=lambda:{'verified':True})
e=Executor(backend,emit);e.submit('normal',[],0,time.perf_counter_ns()+2000000000)
assert done.wait(2);e.close();rows.append({'case':'ordinary_empty_program','events':events,'closed':e.closed,'active':e.active,'prestart_failure_receipts':e.prestart_failure_receipts})
# Failed accepted cannot open another submission on the same executor.
def failed(event):raise RuntimeError('accepted failure')
e=Executor(backend,failed)
try:e.submit('first',[],0,time.perf_counter_ns()+2000000000)
except RuntimeError:pass
second_error=None
try:e.submit('second',[],0,time.perf_counter_ns()+2000000000)
except Exception as error:second_error=type(error).__name__+':'+str(error)
e.close();rows.append({'case':'resubmit_after_unknown','second_error':second_error,'active':e.active,'closed':e.closed,'receipt_count':len(e.prestart_failure_receipts)})
passed=rows[0]['events'][0]['event']=='accepted' and rows[0]['events'][-1]['status']=='completed' and rows[0]['active'] is None and rows[0]['prestart_failure_receipts']==[] and second_error=='ValueError:closed or busy; no implicit queue' and rows[1]['receipt_count']==1
r={'scope':'actual executor thread with empty program/stub release; no physical input/model/game; no concurrency or physical release proof','cases':rows,'checks_pass':passed};Path('/out/RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if passed else 1)
