from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys,os,json,dataclasses
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter

out=Path('/out');rows=[]
client=CodexAppServerClient([sys.executable,'/study/real_file_stdio_proxy.py',str(out)],
                           journal_path=out/'client-journal.jsonl')
try:
    client.initialize()
    planner=PersistentPlannerAdapter(client,model='gpt-5.6-luna',effort='low',
        cwd=os.environ['HOST_WORKSPACE'],base_instructions='Return only JSON matching the supplied schema. Do not use tools.',
        thread_config={'project_doc_max_bytes':0,'features.shell_tool':False,
                       'features.plugins':False,'features.remote_plugin':False})
    planner.start_session()
    schema={'type':'object','properties':{'marker':{'type':'string'}},
            'required':['marker'],'additionalProperties':False}
    handle=planner.begin_turn('Write a marker containing integers 1 through 1000 separated by commas.',output_schema=schema)
    client.wait_notification(lambda m:m.get('method')=='turn/started' and
            m.get('params',{}).get('turn',{}).get('id')==handle.turn_id,timeout=10)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(planner.await_turn,handle,25)
        interrupt=planner.interrupt(handle)
        result=future.result(timeout=25)
    rows.append({'kind':'real_pending_interrupt','interrupt':interrupt,'result':dataclasses.asdict(result)})
    (out/'INTERRUPT_RESULT.json').write_text(json.dumps(rows[-1],indent=2)+'\n')
    if interrupt['outcome']!='requested' or result.answer_eligible or not result.cancellation_requested:
        raise RuntimeError('interrupt exposure/refusal gate failed; no continuation attempt')
    fresh=planner.begin_turn('Return marker exactly recovery-relay-59-4d74.',output_schema=schema)
    result=planner.await_turn(fresh,timeout=25)
    rows.append({'kind':'real_fresh_continuation','result':dataclasses.asdict(result)})
    if not result.answer_eligible or result.answer!={'marker':'recovery-relay-59-4d74'}:
        raise RuntimeError('fresh continuation gate failed')
finally:
    client.close()
r={'scope':'actual provider protocol transport construction only; no game/GUI/input/recovery efficacy',
   'rows':rows,'reader_alive':client._reader.is_alive(),'proxy_exit':client.process.returncode}
(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'rows':len(rows),'scope':r['scope']}),flush=True)

