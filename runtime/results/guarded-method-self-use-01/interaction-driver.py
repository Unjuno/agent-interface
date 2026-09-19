import sys,json,time
from pathlib import Path
sys.path.insert(0,'research/live_control')
from integrated_efficiency_client_v1 import RuntimeClient
from durable_submit_v4 import initialize
from received_continuation_v1 import start
from received_exchange_v2 import request_once
root=Path('results-local/guarded-self-use').resolve()
endpoint={'socket':'/tmp/agent-interface-events-bhet4kpq/events.sock'}
client=RuntimeClient(root,991077);client.endpoint=endpoint;client.journal=root/'control/journal.jsonl'
def dump(name,value):
    (root/name).write_text(json.dumps(value,indent=2)+'\n')
mode=sys.argv[1]
if mode=='initial':
    (root/'control').mkdir()
    initial=request_once(endpoint['socket'],start(endpoint['socket']),{'events':['observation'],'timeout':30})
    dump('initial.json',initial)
    initialize(client.journal,initial['continuation'])
    client.ready=next(r for r in initial['reply']['records'] if r.get('event')=='ready')
    dump('ready.json',client.ready)
    task=client.ready['goal']['tasks'][0]
    source=client.navigate(task)
    dump('source.json',source);dump('initial-programs.json',client.programs)
    print(json.dumps({'task':task,'source':source}))
else:
    client.ready=json.loads((root/'ready.json').read_text())
    tasks=client.ready['goal']['tasks']
    if mode=='first':
        source=json.loads((root/'source.json').read_text())
        aliases,refusal=client.mint(tasks[0]['layout'],source,{'field_point':[300,401],'submit_point':[377,401]},'assistant_a')
        dump('mint-a.json',{'aliases':aliases,'refusal':refusal,'programs':client.programs})
        if aliases is None: raise RuntimeError('mint refused; no replay')
        rows=[]
        for i,task in enumerate(tasks):
            if i: client.navigate(task)
            before=len(client.programs)
            outcome=client.execute_handles(task,aliases)
            rows.append({'task':task,'outcome':outcome,'programs':client.programs[before:]})
            dump('first-results.json',rows);dump('first-programs.json',client.programs)
            if outcome['status']!='completed':
                source=client.submit('review-stop',[{'op':'observe'}])['observations'][-1]
                dump('stopped.json',{'index':i,'source':source,'outcome':outcome})
                dump('first-programs.json',client.programs)
                print(json.dumps({'completed_tasks':i,'stopped_task':task,'outcome':outcome,'source':source}));break
        else: print(json.dumps({'all_completed':True}))
    elif mode=='repair':
        stopped=json.loads((root/'stopped.json').read_text());i=stopped['index'];source=stopped['source']
        aliases,refusal=client.mint(tasks[i]['layout'],source,{'field_point':[760,558],'submit_point':[689,634]},'assistant_b')
        dump('mint-b.json',{'aliases':aliases,'refusal':refusal,'programs':client.programs})
        if aliases is None: raise RuntimeError('repair mint refused; no replay')
        rows=[]
        for j in range(i,len(tasks)):
            task=tasks[j]
            if j!=i: client.navigate(task)
            before=len(client.programs);outcome=client.execute_handles(task,aliases)
            rows.append({'task':task,'outcome':outcome,'programs':client.programs[before:]})
            dump('repair-results.json',rows);dump('repair-programs.json',client.programs)
            if outcome['status']!='completed': raise RuntimeError('method yielded; inspect saved result, no replay')
        source=client.submit('review-final',[{'op':'observe'}])['observations'][-1]
        dump('final-source.json',source);dump('repair-programs.json',client.programs)
        evaluation=client.finish('finish-guarded-991077');dump('evaluation.json',evaluation)
        print(json.dumps({'evaluation':evaluation,'source':source}))
