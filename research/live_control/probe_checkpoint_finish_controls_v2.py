"""Recorded query plus malformed/negative controls for explicit conditional finish."""
import copy,hashlib,json
from pathlib import Path
from checkpoint_finish_v2 import run
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-finish-controls-03';out.mkdir(exist_ok=False)
source_path=HERE/'results/checkpoint-calc-self-use-01/after-checkpoint.json'
source=json.loads(source_path.read_text());query=source['reply'];qid=source['request']['request_id'];fid='finish-policy'
after=source['request']['after'];contract=source['request']['command']['contract']
final=dict(status='boundary',cursor=query['cursor']+1,records=[dict(event='independent_evaluation',success=True,
    evaluation_request=dict(transport_request_id=fid,command_op='finish'))])
results={}
for case in ('positive','unknown','wrong_query','wrong_contract','wrong_actual','bad_hash','gap','busy','missing_cursor','final_false','wrong_final_id','legacy_unscoped','final_error'):
    q=copy.deepcopy(query);f=copy.deepcopy(final);calls=[]
    if case=='unknown':q['records'][-1]['evidence']['status']='UNKNOWN'
    if case=='wrong_query':q['records'][-1]['transport_request_id']='other'
    if case=='wrong_contract':q['records'][-1]['evidence']['contract']['expected']['A1']=True
    if case=='wrong_actual':q['records'][-1]['evidence']['actual']['A1']=999
    if case=='bad_hash':q['records'][-1]['evidence']['artifact_sha256']='bad'
    if case=='gap':q['status']='gap'
    if case=='busy':q['records'][-1]=dict(event='effect_checkpoint',transport_request_id=qid,status='UNKNOWN',reason='verifier_busy',task_success=None)
    if case=='missing_cursor':q.pop('cursor')
    if case=='final_false':f['records'][-1]['success']=False
    if case=='wrong_final_id':f['records'][-1]['evaluation_request']['transport_request_id']='other'
    if case=='legacy_unscoped':f['records'][-1].pop('evaluation_request')
    def exchange(spec):
        calls.append(spec)
        if len(calls)==2 and case=='final_error':raise TimeoutError('injected')
        return q if len(calls)==1 else f
    r=run(exchange,after=after,contract=contract,checkpoint_id=qid,finish_id=fid,finish_on_match=True)
    if case in ('positive','final_false'):assert r['state']=='evaluated' and r['task_success']==(case=='positive')
    else:assert r['task_success'] is None
    should_finish=case in ('positive','final_false','wrong_final_id','legacy_unscoped','final_error')
    assert len(calls)==(2 if should_finish else 1) and r['finish_attempted']==should_finish
    if case=='unknown':assert r['state']=='needs_decision' and r['continuation_allowed'] is True
    elif case in ('wrong_query','wrong_contract','wrong_actual','bad_hash','gap','busy','missing_cursor'):
        assert r['state']=='needs_reconciliation' and r['continuation_allowed'] is False
    results[case]=r
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
    (Path(__file__),HERE/'checkpoint_finish_v2.py',HERE/'request_boundary_v4.py',source_path)},indent=2)+'\n')
print('13 controls passed')
