from pathlib import Path
import sys,os,json,hashlib,dataclasses
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.persistent_planner_adapter_v2 import PersistentPlannerAdapter
out=Path('/out');source=Path('/study/fixture-input/source.png')
digest=hashlib.sha256(source.read_bytes()).hexdigest()
if digest!='70723e24d671fd656fa3ba40294b4cd28272493a9ffcacf93843cd86f13ab16d':
    raise ValueError('source image changed')
client=CodexAppServerClient([sys.executable,'/study/real_file_stdio_proxy.py',str(out)],
                           journal_path=out/'client-journal.jsonl')
try:
    client.initialize()
    planner=PersistentPlannerAdapter(client,model='gpt-5.6-luna',effort='low',
         cwd=os.environ['HOST_WORKSPACE'],base_instructions='Read only the supplied image. Return JSON. Do not use tools.',
         thread_config={'project_doc_max_bytes':0,'features.shell_tool':False,'features.plugins':False,
                        'features.remote_plugin':False})
    planner.start_session()
    schema={'type':'object','properties':{'health':{'type':'integer'},'ammo':{'type':'integer'}},
            'required':['health','ammo'],'additionalProperties':False}
    handle=planner.begin_turn('Read the visible HEALTH and AMMO numbers in this screenshot.',
                  output_schema=schema,image_path=os.environ['HOST_IMAGE'])
    result=planner.await_turn(handle,timeout=30)
    r={'scope':'single retained static image transport; not live game/visual reliability/recovery',
       'source_sha256':digest,'submitted_host_image':os.environ['HOST_IMAGE'],
       'result':dataclasses.asdict(result),'expected':{'health':100,'ammo':48},
       'expected_source':'pre-run direct visual inspection of unchanged public fixture source screenshot'}
    (out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n')
    if not result.answer_eligible or result.answer!=r['expected']:
        raise RuntimeError('image transport/read gate failed; retained first response')
finally:
    client.close()
print(json.dumps({'answer':result.answer,'scope':r['scope']}),flush=True)
