"""Offline transport controls against actual archived pending/reply evidence."""
import copy,json,tempfile
from pathlib import Path
from append_checkpoint_v1 import store,load
from durable_submit_v4 import run
from recover_once_v1 import recover_once
H=Path(__file__).resolve().parent;R=H/'results/recover-once-controls-01';R.mkdir(exist_ok=False)
S=H/'results/live-responder-ink-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
base=read(S/'pending.json');reply=read(S/'recovered.json')['reply'];rows=[]
for case in ['timeout','closed','transport_error','conflicting_echo','matched','no_pending']:
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'journal';state=copy.deepcopy(base)
  if case=='no_pending':state['pending']=None
  store(path,state);before=path.read_bytes();seen=[]
  def fake(session,q,**kw):
   seen.append(q);assert 'command' not in q and q['action_id']==base['pending']['request']['command']['id']
   if case=='transport_error':raise ConnectionError('injected read failure')
   if case in ('timeout','closed'):return {'status':case,'cursor':q['after'],'records':[]}
   r=copy.deepcopy(reply)
   if case=='conflicting_echo':
    e=next(e for e in r['records'] if e['event']=='command');e['command']['transport_request_id']='wrong-request'
   return r
  error=None
  try:result=recover_once(path,transport=fake)
  except (ConnectionError,ValueError) as e:error=str(e)
  after=load(path)
  if case in ('transport_error','no_pending'):
   assert error and path.read_bytes()==before
  else:assert error is None
  assert len(seen)==(0 if case=='no_pending' else 1)
  if case=='matched':assert after['pending'] is None
  elif case!='no_pending':
   assert after['pending'] is not None
   if case=='conflicting_echo':assert after['pending']['conflict'] is True
   if case=='closed':assert after['continuation']['channel_closed'] is True
   def forbidden(*a,**k):raise AssertionError('blocked command reached transport')
   try:run(path,{'command':{'op':'clock'}},forbidden)
   except ValueError:pass
   else:raise AssertionError('new command admitted')
  rows.append({'case':case,'read_transport_calls':len(seen),'error':error,'pending_retained':after['pending'] is not None})
(R/'result.json').write_text(json.dumps({'scope':'offline injected replies, zero actual transports','rows':rows},indent=2)+'\n',encoding='utf-8');print(json.dumps(rows))
