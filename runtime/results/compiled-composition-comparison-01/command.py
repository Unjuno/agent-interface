import json,sys,time
from pathlib import Path
case=Path('/var/tmp/agent-interface-evidence-storage-main/runtime/results/compiled-composition-comparison-01')/sys.argv[1]
index=int(sys.argv[2]); requests=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8-sig')); requests=requests if isinstance(requests,list) else [requests]
replies=[]
for request in requests:
    path=case/'commands'/f'{index:03d}.json'
    if path.exists(): raise RuntimeError('already allocated command; inspect existing reply')
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(request)+'\n'); tmp.rename(path)
    reply=case/'replies'/path.name
    for _ in range(500):
        if reply.exists(): replies.append(json.loads(reply.read_text())); break
        if (case/'exception.json').exists(): print((case/'exception.json').read_text()); sys.exit(1)
        time.sleep(.02)
    else: print(json.dumps({'status':'REPLY_PENDING','index':index,'replay_allowed':False})); sys.exit(0)
    index+=1
print(json.dumps(replies if len(replies)>1 else replies[0]))
