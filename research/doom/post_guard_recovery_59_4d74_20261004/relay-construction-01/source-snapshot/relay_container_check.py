from pathlib import Path
import sys,json,dataclasses
from concurrent.futures import ThreadPoolExecutor
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter

out=Path('/out'); results=[]
client=CodexAppServerClient([sys.executable,'/study/file_stdio_proxy.py',str(out)],
                           journal_path=out/'client-journal.jsonl')
try:
    client.initialize()
    planner=PersistentPlannerAdapter(client,model='EXPLICIT_FAKE_NO_PROVIDER',effort='low',
           cwd='/out',base_instructions='fake protocol construction')
    planner.start_session()
    schema={'type':'object','properties':{'action':{'type':'string'}},
            'required':['action'],'additionalProperties':False}
    for n in (1,2):
        handle=planner.begin_turn('pending fake',output_schema=schema)
        client.wait_notification(lambda m:m.get('method')=='turn/started' and
              m.get('params',{}).get('turn',{}).get('id')==handle.turn_id,timeout=5)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(planner.await_turn,handle,10)
            assert not future.done()
            interrupt=planner.interrupt(handle)
            result=future.result(timeout=10)
        assert interrupt['outcome']=='requested'
        assert result.cancellation_requested and not result.answer_eligible
        assert result.status==('interrupted' if n==1 else 'completed')
        results.append({'kind':'pending_interrupt' if n==1 else 'completed_after_interrupt',
                        'interrupt':interrupt,'result':dataclasses.asdict(result)})
    fresh=planner.begin_turn('fresh fake',output_schema=schema)
    result=planner.await_turn(fresh,timeout=5)
    assert result.answer_eligible and not result.cancellation_requested
    assert result.answer=={'action':'fresh'}
    results.append({'kind':'fresh_continuation','result':dataclasses.asdict(result)})
finally:
    client.close()
r={'scope':'Windows fake peer via real WSLc file/stdio relay and unchanged current planner/client; no provider/game/input',
   'rows':results,'reader_alive':client._reader.is_alive(),'proxy_exit':client.process.returncode}
(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
