"""Checkpoint transport/reconciliation controls and legacy submit/clock replay."""
import copy,hashlib,json,tempfile
from pathlib import Path
from durable_submit_v5 import initialize,run,reconcile
from durable_submit_v4 import reconcile as previous_reconcile
from received_continuation_v1 import start
from append_checkpoint_v1 import load
from effect_checkpoint_v2 import archived_sample
H=Path(__file__).resolve().parent;R=H/'results/durable-checkpoint-controls-01';R.mkdir(exist_ok=False)
contract={'kind':'saved_cells','expected':{'A1':480,'A2':192}}
source=H/'results/sampled-effect-calc-02/workbook-snapshot-03.xlsx'
evidence=archived_sample(source,contract,R/'artifacts');assert evidence['status']=='VERIFIED'
def checkpoint(identifier='checkpoint-1'):
 return {'event':'effect_checkpoint','transport_request_id':identifier,'command_op':'effect_checkpoint',
         'task_success':None,'authority':'none','evidence':copy.deepcopy(evidence)}
def pending():
 q={'request_id':'checkpoint-1','command':{'op':'effect_checkpoint','contract':contract}}
 return {'request':q,'write_state':'may_have_been_sent','echo_seen':False,'accepted':False,'conflict':False}
echo={'event':'command','command':{'op':'effect_checkpoint','contract':contract,'transport_request_id':'checkpoint-1'}}
cases=[]
def check(name,records,resolved,conflict=False):
 p,r=reconcile(pending(),records)
 assert (p is None)==resolved and (r is not None)==resolved
 if p is not None:assert p['conflict']==conflict
 cases.append({'name':name,'resolved':resolved,'conflict':conflict})
check('matching_verified',[echo,checkpoint()],True)
unknown=checkpoint();unknown['evidence'].update(status='UNKNOWN',actual={'A1':None,'A2':None},reason='sample_mismatch_window_open')
check('matching_unknown_is_resolved_query',[echo,unknown],True)
check('unrelated_reply_not_current',[echo,checkpoint('other')],False)
wrong=checkpoint();wrong['evidence']['contract']['expected']['A1']=481
check('wrong_contract_sticky',[echo,wrong,checkpoint()],False,True)
wrong=checkpoint();wrong['evidence']['actual']['A1']=True
check('wrong_typed_value',[echo,wrong],False,True)
wrong=checkpoint();wrong['task_success']=True
check('semantic_success_field_rejected',[echo,wrong],False,True)
wrong=checkpoint();wrong['evidence'].pop('artifact_sha256')
check('verified_digest_required',[echo,wrong],False,True)
check('other_command_breaks_attribution',[echo,{'event':'command','command':{'op':'clock'}},checkpoint()],False,True)
busy={k:v for k,v in checkpoint().items() if k!='evidence'};busy.update(status='UNKNOWN',reason='verifier_busy')
check('busy_resolves_without_positive_effect',[echo,busy],True)
rejected={'event':'rejected','op':'effect_checkpoint','transport_request_id':'checkpoint-1','admission':'unknown','reason':'unsupported application'}
check('correlated_query_rejection',[echo,rejected],True)

with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'journal.jsonl';initialize(path,start('private-test.sock'));sent=[]
 def first(socket,q,**kwargs):
  sent.append(copy.deepcopy(q));assert q['read_request_id']==q['request_id']
  return {'status':'timeout','cursor':q['after']+1,'records':[{'event':'command','command':dict(q['command'],transport_request_id=q['request_id'])}]}
 result=run(path,{'command':{'op':'effect_checkpoint','contract':contract}},first)
 assert result['state']['pending'] is not None
 def forbidden(*args,**kwargs):raise AssertionError('new command reached transport')
 try:run(path,{'command':{'op':'clock'}},forbidden)
 except ValueError as error:assert str(error)=='unresolved command; read only'
 else:raise AssertionError('pending query did not block command')
 def read_only(socket,q,**kwargs):
  assert 'command' not in q and q['read_request_id']==sent[0]['request_id']
  return {'status':'boundary','cursor':q['after']+1,'records':[checkpoint(q['read_request_id'])]}
 recovered=run(path,{},read_only);assert recovered['state']['pending'] is None and len(sent)==1
 assert load(path)==recovered['state']
 (R/'recovery.json').write_text(json.dumps({'sent':sent,'first':result,'recovered':recovered},indent=2)+'\n',encoding='utf-8')

with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'journal.jsonl';initialize(path,start('lost-test.sock'))
 def lost(socket,q,**kwargs):raise ConnectionError('synthetic lost response')
 try:run(path,{'command':{'op':'effect_checkpoint','contract':contract}},lost)
 except ConnectionError:pass
 else:raise AssertionError('loss not propagated')
 assert load(path)['pending']['write_state']=='may_have_been_sent'

legacy=H/'results/shared-phased-calc-01/calls.json';count=0
for call in json.loads(legacy.read_text(encoding='utf-8')):
 r=call['result'];q=r['request']
 if 'command' not in q:continue
 p={'request':q,'write_state':'may_have_been_sent','echo_seen':False,'accepted':False,'conflict':False}
 assert reconcile(p,r['reply']['records'])==previous_reconcile(p,r['reply']['records']);count+=1
names=[Path(__file__),H/'durable_submit_v5.py',H/'checkpoint_contract_v1.py',H/'effect_checkpoint_v2.py',source,legacy]
report={'cases':cases,'one_query_write_then_explicit_read':True,'loss_retains_pending':True,'legacy_reconcile_replays':count,
        'sources':{str(p.relative_to(H)):hashlib.sha256(p.read_bytes()).hexdigest() for p in names}}
(R/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checkpoint_cases':len(cases),'legacy_replays':count,'pending_recovery_passed':True}))
