"""Wrapper orchestration with recorded replies and mocked I/O; no GUI input."""
import contextlib,copy,hashlib,io,json,sys
from pathlib import Path
from types import SimpleNamespace
import prepared_checkpoint_v2 as caller
HERE=Path(__file__).resolve().parent;out=HERE/'results/prepared-checkpoint-continuation-01';out.mkdir(exist_ok=False)
source=HERE/'results/prepared-checkpoint-self-use-01/enter/report.json'
recorded=json.loads(source.read_text());program=recorded['program'];template=recorded['policy']['exchanges'][0]['reply']
contract=recorded['policy']['exchanges'][0]['request']['command']['contract']
(out/'contract.json').write_text(json.dumps(contract)+'\n')
original_run=caller.subprocess.run;original_exchange=caller.exchange;original_argv=sys.argv
results={}
try:
    for case in ('unknown','wrong_identity','wrong_contract','bad_cursor','gap','timeout','busy','bad_busy','missing_records','claimed_success'):
        case_out=out/case;calls=[]
        caller.subprocess.run=lambda *a,**kw:SimpleNamespace(returncode=0,stdout=json.dumps(program),stderr='')
        def exchange(address,spec,**kwargs):
            calls.append(spec);assert spec['command']['op']=='effect_checkpoint'
            reply=copy.deepcopy(template);record=reply['records'][-1]
            record['transport_request_id']=spec['request_id']
            if case=='wrong_identity':record['transport_request_id']='different'
            if case=='wrong_contract':record['evidence']['contract']['expected']['A1']=999
            if case=='bad_cursor':reply['cursor']+=1
            if case in ('gap','timeout'):reply['status']=case
            if case in ('busy','bad_busy'):
                reply['records'][-1]=dict(event='effect_checkpoint',transport_request_id=spec['request_id'],status='UNKNOWN',reason='verifier_busy',task_success=None,authority='none')
                if case=='bad_busy':reply['records'][-1].pop('authority')
            if case=='missing_records':reply['records']=None
            if case=='claimed_success':record['task_success']=True
            return reply
        caller.exchange=exchange
        sys.argv=['prepared_checkpoint_v2','unused-socket','unused-batch','unused-root','test','unused-steps',str(out/'contract.json'),
            '--lease-ms','30000','--finish-on-match','--producer','scripted','--out',str(case_out)]
        with contextlib.redirect_stdout(io.StringIO()) as capture:caller.main()
        report=json.loads(capture.getvalue());assert len(calls)==1
        allowed=case in ('unknown','busy')
        assert (case_out/'continuation-batch.json').exists()==allowed
        assert report['policy']['continuation_allowed']==allowed
        expected='needs_decision' if allowed else ('checkpoint_pending' if case=='timeout' else 'needs_reconciliation')
        assert report['state']==expected and report['task_success'] is None
        assert not report['policy']['finish_attempted']
        if allowed:
            batch=json.loads((case_out/'continuation-batch.json').read_text())
            assert batch['records']==program['records']+report['policy']['exchanges'][0]['reply']['records']
        results[case]=dict(state=report['state'],continuation_written=allowed,calls=len(calls))
finally:
    caller.subprocess.run=original_run;caller.exchange=original_exchange;sys.argv=original_argv
(out/'results.json').write_text(json.dumps(dict(cases=results,scope='mocked prepared subprocess and socket callback; wrapper behavior only, no live GUI regression'),indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
    (Path(__file__),HERE/'prepared_checkpoint_v2.py',HERE/'checkpoint_finish_v2.py',HERE/'request_boundary_v4.py',source)},indent=2)+'\n')
print(json.dumps(results,indent=2))
