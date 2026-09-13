"""Durable OpenTTD L driver with explicit typed finish reasons."""
import hashlib,json,subprocess,sys,tempfile,time,shutil,os
from pathlib import Path
from append_checkpoint_v1 import load
from durable_submit_v4 import initialize,run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from openttd_finish_outcome_v2 import classify as classify_finish
HERE=Path(__file__).resolve().parent
arm=sys.argv[1]
if arm not in {'fixed-astra','negative-control'}:raise SystemExit('arm must be fixed-astra/negative-control')
study=sys.argv[2] if len(sys.argv)>2 else 'timing-envelope-openttd-l-07'
root=HERE/'results'/study/arm;root.mkdir(parents=True,exist_ok=False)
def dump(name,value):
    path=root/name;temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
names=['timing_envelope_openttd_l_driver_v6.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','pointer_socket_entry_v8.py','event_socket_v11.py','openttd_finish_outcome_v2.py','session_v22.py']
dump('plan.json',{'seed_semantics':'byte-pinned seed-991003 save; five-tile L objective; closed toolbar; opaque trees before pre-action','scope':'fresh OpenTTD L driver with one pre-planner tree-transparency transition','arm':arm,'study':study,'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,'-u',str(HERE/'pointer_socket_entry_v8.py'),'openttd','serve','--','--root','/home/taka/agent-interface-bench-feasibility','--out',str(root/'runtime'),'--controller','assistant'],stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
temporary=tempfile.TemporaryDirectory(prefix='agent-interface-live-openttd-l-');journal=Path(temporary.name)/'journal.jsonl';calls=[]
try:
    endpoint=json.loads(p.stdout.readline());dump('endpoint.json',endpoint)
    initial=request_once(endpoint['socket'],start(endpoint['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
    def call(spec):
        begin=time.perf_counter_ns();result=run(journal,spec);end=time.perf_counter_ns();calls.append({'begin_ns':begin,'end_ns':end,'result':result});dump('calls.json',calls);assert result['state']['pending'] is None;shutil.copy2(journal,root/'journal.jsonl');return result
    def clock():return call({'command':{'op':'clock'},'timeout':3})['state']['last_resolution']['clock']
    task=next(e['task'] for e in initial['reply']['records'] if e['event']=='ready');before=initial['continuation']['observation'];preaction_begin=time.perf_counter_ns();current=clock();transformed=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'chord','modifier':'Control_L','key':'2'},{'op':'observe'}]},'timeout':5});preaction_end=time.perf_counter_ns();after=transformed['state']['continuation']['observation'];assert after['pointer_binding']==before['pointer_binding'] and after['input_focus_before']==after['input_focus_after'],'pre-action binding changed'
    dump('preaction.json',{'method':'openttd.ensure_trees_transparent','known_state_before':'opaque','tracked_state_after':'transparent','begin_ns':preaction_begin,'end_ns':preaction_end,'duration_ns':preaction_end-preaction_begin,'before_observation':before,'after_observation':after,'expanded_steps':[{'op':'chord','modifier':'Control_L','key':'2'}],'task_state_assurance':'independent finish score remains authoritative'})
    dump('ready.json',{'task':task,'observation':after,'bridge_pid':p.pid,'view_state':'transparent','preaction_duration_ns':preaction_end-preaction_begin});print(json.dumps({'ready':str(root/'ready.json')}),flush=True)
    for index in range(1,13):
        path=root/f'proposal-{index}.json';deadline=time.monotonic()+300
        while not path.exists():
            if (root/'abort.json').exists():path=root/'abort.json';break
            assert p.poll() is None,'bridge exited while waiting for model'
            if time.monotonic()>deadline:raise TimeoutError('proposal wait limit; no automatic input')
            time.sleep(.05)
        proposal=json.loads(path.read_text(encoding='utf-8'));received=time.perf_counter_ns()
        if proposal.get('finish') is True:
            state=load(journal)['continuation'];finish=request_once(endpoint['socket'],state,{'events':['independent_evaluation'],'timeout':25,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);code=p.wait(timeout=10);evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');outcome_name,outcome=classify_finish(evaluation,finish_kind=proposal['outcome_kind'],exit_code=code,proposals_executed=index-1,journal_calls=len(calls),reason=proposal.get('reason'),arm=arm);dump(outcome_name,outcome);break
        steps=proposal['steps'];assert type(steps) is list and 1<=len(steps)<=6
        assert all(step.get('op') in ('pointer_move','pointer_click','pointer_drag','observe','dwell_observe','chord') for step in steps)
        for step in steps:
            if step.get('op')=='chord':assert step=={'op':'chord','modifier':'Control_L','key':'2'},'only the preregistered tree-transparency chord is admitted'
        before=load(journal)['continuation']['observation'];current=clock();fresh=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]},'timeout':3});observation=fresh['state']['continuation']['observation']
        assert observation['pointer_binding']==before['pointer_binding'] and observation['input_focus_before']==observation['input_focus_after'],'binding changed; replan'
        current=clock();program=steps+[{'op':'observe'}];dwell_seconds=sum(step.get('delay_ms',0) for step in program)/1000;action_timeout=min(25,max(5,3+dwell_seconds+0.75*len(program)))
        applied=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+30_000_000_000,'steps':program},'timeout':action_timeout});dump(f'applied-{index}.json',{'proposal_received_ns':received,'source_observation':before,'fresh_observation':observation,'result':applied,'returned_ns':time.perf_counter_ns()});print(json.dumps({'applied':index,'observation':applied['state']['continuation']['observation'],'resolution':applied['state']['last_resolution']}),flush=True)
    else:
        path=root/'abort.json';deadline=time.monotonic()+30
        while not path.exists():
            assert p.poll() is None,'bridge exited while waiting for bounded-limit supervisor stop'
            if time.monotonic()>deadline:raise TimeoutError('bounded-limit supervisor stop wait')
            time.sleep(.05)
        proposal=json.loads(path.read_text(encoding='utf-8'))
        assert proposal.get('finish') is True,'bounded-limit supervisor message must finish'
        state=load(journal)['continuation'];finish=request_once(endpoint['socket'],state,{'events':['independent_evaluation'],'timeout':25,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);code=p.wait(timeout=10);evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');outcome_name,outcome=classify_finish(evaluation,finish_kind=proposal['outcome_kind'],exit_code=code,proposals_executed=12,journal_calls=len(calls),reason=proposal.get('reason'),arm=arm);dump(outcome_name,outcome)
finally:
    if journal.exists():shutil.copy2(journal,root/'journal.jsonl')
    if p.poll() is None:p.terminate();p.wait(timeout=10)
    temporary.cleanup()
