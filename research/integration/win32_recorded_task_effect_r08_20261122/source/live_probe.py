import asyncio, hashlib, importlib.util, json, sys, time, uuid
from datetime import timedelta
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); raw=out/'raw'
sys.path.insert(0,str(repo))
sys.path.insert(0,str(repo/'research/integration/standard_mcp_task_ledger_57_v1'))
from provider_attempt_recorder import ProviderAttemptRecorder
from recorded_public_mcp_caller_v1 import RecordedPublicMcpCaller
from recorded_comparison_adapter_v1 import build_measured_run
from effect_receipt_handoff_v1 import adapt_measured_run
from runtime.cli_v1.mcp_relay import Relay
cfg=json.loads((out/'conditions.json').read_text(encoding='utf-8-sig'))
window=json.loads((raw/'window.json').read_text(encoding='utf-8-sig')); x1,y1,x2,y2=window['rect']; region=[x1,y1,x2-x1,y2-y1]
targets=raw/'targets.json'; target=json.loads(targets.read_text(encoding='utf-8-sig'))
server_args=['-m','runtime.cli_v1.mcp_server','--targets',str(targets),'--output-directory',str(raw/'mcp'),'--session-mode','supervised-win32','--supervised-win32-late-input-horizon-ms','2000']
recorder_root=raw/'recorder'; recorder=ProviderAttemptRecorder(recorder_root)
scorer_path=out/'source/scorer.py'; spec=importlib.util.spec_from_file_location('r07_scorer',scorer_path); scorer=importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
def body(response):
    result=response.get('result',{})
    rows=[x.get('text') for x in result.get('content',[]) if x.get('type')=='text' and isinstance(x.get('text'),str)]
    if len(rows)!=1: raise ValueError('expected exactly one public text receipt')
    return json.loads(rows[0])
def save_json(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def terminal(value):
    action=value.get('action') if isinstance(value,dict) else None
    if isinstance(action,dict): return action.get('status') in ('completed','recovered','unknown')
    return value.get('status') in ('returned','recovered','unknown','runtime_failed','receipt_unavailable')
def observation_row(call_id,response):
    public=body(response); report=public.get('receipt',{}).get('source',{}).get('raw_report',{})
    if report.get('status')!='returned' or report.get('side_effect_authority') not in (False,'none') or report.get('input_dispatched') is not False: raise ValueError('public observation did not prove no-authority/no-input')
    obs=report.get('observation',{}); pngs=[c.get('data') for c in response.get('result',{}).get('content',[]) if c.get('type')=='image' and c.get('mimeType')=='image/png']
    if len(pngs)!=1: raise ValueError('observation does not contain exactly one PNG block')
    import base64
    png=base64.b64decode(pngs[0],validate=True); digest=hashlib.sha256(png).hexdigest()
    artifact=obs.get('artifact',{});
    if digest!=artifact.get('sha256') or artifact.get('bytes')!=len(png) or artifact.get('source_raw_sha256')!=obs.get('sha256'): raise ValueError('PNG block, artifact hash/size, and raw-source hash do not form a consistent capture')
    name='observation-'+call_id+'.png'; (raw/name).write_bytes(png); (recorder_root/'raw'/name).write_bytes(png)
    return {'tool_call_id':call_id,'observation_id':report['observation_id'],'target_generation':report['target_generation'],'capture_started_ns':obs['capture_started_ns'],'capture_ended_ns':obs['capture_ended_ns'],'image_sha256':digest},public
async def main():
    params=StdioServerParameters(command=sys.executable,args=server_args,cwd=str(repo))
    timeline=[]
    async with stdio_client(params) as (rd,wr):
      async with ClientSession(rd,wr,read_timeout_seconds=timedelta(seconds=50)) as session:
        await session.initialize()
        relay=Relay(session)
        caller=RecordedPublicMcpCaller(relay,recorder,allowed_methods={'interface_observe','interface_dispatch','interface_results','interface_cancel','interface_close'})
        async def call(method,args,cid):
            t0=time.monotonic_ns(); value=await caller.call_tool(None,cid,method,args); t1=time.monotonic_ns()
            save_json(raw/(method+'-'+cid+'.json'),value); timeline.append({'method':method,'recorder_call_id':cid,'started_ns':t0,'ended_ns':t1})
            return value
        before_id=cfg['recorder_call_ids']['observe_before']; pre=await call('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':region},before_id)
        before_obs,before_public=observation_row(before_id,pre); gen=before_obs['target_generation']
        fg_script=out/'source/foreground_probe.py'
        import subprocess
        fg=subprocess.run([sys.executable,str(fg_script),str(window['hwnd']),str(window['pid']),str(raw/'foreground-pre-dispatch.json')],cwd=str(out),capture_output=True,text=True)
        if fg.returncode: raise RuntimeError('foreground identity mismatch; dispatch stopped')
        now=time.monotonic_ns(); program={'schema':'agent-interface/program-v1','program_id':cfg['program_id'],'source':{'observation_seq':1,'binding_revision':1,'target_generations':{'fixture':gen}},'authority':{'lease_id':cfg['lease_id'],'expires_at_ns':now+60_000_000_000},'terminal':{'release_all_required':True},'ops':[{'op':'focus','target':'fixture'},{'op':'key_chord','keys':['A']},{'op':'release_all'}]}
        dispatch_id=cfg['recorder_call_ids']['dispatch_boundary']; d=await call('interface_dispatch',{'program':program,'current_observation_seq':1,'current_binding_revision':1,'wait_for_result_ms':10000},dispatch_id); db=body(d); action_id=db.get('call_id')
        if not isinstance(action_id,str) or len(action_id)!=32: raise ValueError('dispatch response lacks public action call id')
        exact_id=cfg['recorder_call_ids']['results_exact']; lookup=await call('interface_results',{'call_id':action_id,'include_image':False},exact_id); owner=body(lookup)
        if not terminal(owner):
            deadline=time.monotonic()+20
            while not terminal(owner) and time.monotonic()<deadline:
                await asyncio.sleep(.2); poll_id=uuid.uuid4().hex; lookup=await call('interface_results',{'call_id':action_id,'include_image':False},poll_id); owner=body(lookup); exact_id=poll_id
            if not terminal(owner):
                cancel_id=uuid.uuid4().hex; await call('interface_cancel',{'call_id':action_id},cancel_id)
                deadline=time.monotonic()+20
                while not terminal(owner) and time.monotonic()<deadline:
                    await asyncio.sleep(.2); poll_id=uuid.uuid4().hex; lookup=await call('interface_results',{'call_id':action_id,'include_image':False},poll_id); owner=body(lookup); exact_id=poll_id
        if not terminal(owner): raise RuntimeError('single dispatch unresolved after finite cancel; no replay')
        effect_path=raw/'effect.json'; deadline=time.monotonic()+10; effect=None
        while time.monotonic()<deadline:
            try: effect=json.loads(effect_path.read_text(encoding='utf-8'))
            except (FileNotFoundError,json.JSONDecodeError): effect=None
            if effect and effect.get('verified') is True: break
            await asyncio.sleep(.05)
        after_id=cfg['recorder_call_ids']['observe_after']; aft=await call('interface_observe',{'target':'fixture','frame':'screen_physical_px','region':region},after_id); after_obs,after_public=observation_row(after_id,aft)
        close_id=cfg['recorder_call_ids']['close_boundary']; close=await call('interface_close',{},close_id)
        ok,state_bytes,effect=scorer.score(raw/'events.jsonl',effect_path)
        scorer_id=cfg['scorer_id']; recorder.record_task_score(scorer_id,ok,state_bytes)
        receipt=recorder.reconcile(); save_json(raw/'recorder-receipt.json',receipt)
        # Add the independently retained PNG bytes to the recorder's custody references.
        for obs in (before_obs,after_obs):
            name='observation-'+obs['tool_call_id']+'.png'; data=(raw/name).read_bytes(); receipt['raw_refs'].append({'path':'raw/'+name,'sha256':hashlib.sha256(data).hexdigest()})
        env_bytes=(raw/'environment.json').read_bytes(); fixture_sha=hashlib.sha256((out/'source/fixture_app.py').read_bytes()).hexdigest(); scorer_sha=hashlib.sha256(scorer_path.read_bytes()).hexdigest(); route_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        metadata={'schema':'agent-interface/standard-mcp-task-ledger-v1','run_id':cfg['run_id'],'comparison':{'arm':'C','block':1,'order':3,'task_seed':cfg['run_id']},'task':{'task_id':cfg['task_id'],'fixture_sha256':fixture_sha,'scorer_sha256':scorer_sha},'source':{'commit':cfg['source_main'],'route_sha256':route_sha},'environment_sha256':hashlib.sha256(env_bytes).hexdigest(),'model':None}
        all_events=receipt['events']; started=min(e['started_ns'] for e in all_events); ended=max(e['ended_ns'] for e in all_events)
        measurement={'started_ns':started,'ended_ns':ended,'elapsed_ns':ended-started,'phases':[{'name':'other','started_ns':started,'ended_ns':ended,'reason':'fixture lifecycle, public calls, delayed effect, and independent score; no provider/model'}],'model_delivered_images':[],'local_observations':[before_obs,after_obs],'native_owner_evidence':{'lookup_tool_call_id':exact_id,'action_call_id':action_id,'effect_observed_ns':effect.get('effect_observed_ns') if effect else None}}
        measured=build_measured_run(receipt,recorder_root=recorder_root,ledger_metadata=metadata,measurement=measurement); save_json(raw/'measured-run.json',measured)
        score_event=next(e for e in measured['task_ledger']['events'] if e['kind']=='task_score')
        before_state=json.dumps({'text':'','accepted_a_keydowns':0},sort_keys=True,separators=(',',':')).encode()
        effect_receipt={'schema':'agent-interface/task-effect-score-receipt-v1','task_id':cfg['task_id'],'lookup_tool_call_id':exact_id,'action_call_id':action_id,'action_operation_id':owner.get('action',{}).get('operation_id'),'target_generation':gen,'scorer_id':score_event['scorer_id'],'scorer_sha256':scorer_sha,'task_success':score_event['task_success'],'state_sha256':score_event['state_sha256'],'before_task_success':False,'before_state_sha256':hashlib.sha256(before_state).hexdigest(),'before_observation':before_obs,'after_observation':after_obs,'effect_interval_ns':{'lower_ns':effect.get('key_down_accepted_ns'),'upper_ns':effect.get('effect_observed_ns')} if effect else None}
        (recorder_root/'effect-score.json').write_text(json.dumps(effect_receipt,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
        adapted=adapt_measured_run(measured,receipt_root=recorder_root,receipt_path='effect-score.json'); save_json(raw/'adapted-run.json',adapted)
        summary={'status':'PASS_RECORDED_FIXTURE_EFFECT' if ok and owner.get('action',{}).get('release_confirmed') is True else 'FAIL_OR_UNKNOWN','run_id':cfg['run_id'],'public_action_call_id':action_id,'recorder_dispatch_call_id':dispatch_id,'lookup_recorder_call_id':exact_id,'operation_id':owner.get('action',{}).get('operation_id'),'target_generation':gen,'before_observation_id':before_obs['observation_id'],'after_observation_id':after_obs['observation_id'],'release_confirmed':owner.get('action',{}).get('release_confirmed'),'late_input_horizon_verified':owner.get('action',{}).get('completion_custody',{}).get('completion_readback',{}).get('late_input_horizon_verified'),'independent_task_success':ok,'public_task_success':owner.get('task_success'),'effect_interval':effect_receipt['effect_interval_ns'],'effect_timing_status':adapted.get('timing_status'),'eligible_task_success':adapted.get('eligible_task_success'),'factual_task_success':adapted.get('factual_task_success'),'close_status':body(close).get('status'),'timeline':timeline}
        save_json(raw/'summary.json',summary); print(json.dumps(summary,indent=2))
asyncio.run(main())




