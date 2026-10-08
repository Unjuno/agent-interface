import json, os, sys, time
from pathlib import Path
case=Path('/var/tmp/agent-interface-evidence-storage-main/runtime/results/common-public-pixel-admission-01')/sys.argv[1]
index=int(sys.argv[2]); request=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8-sig'))
path=case/'commands'/f'{index:03d}.json'
if path.exists(): raise RuntimeError('command already allocated; inspect original reply instead')
tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(request)+'\n'); tmp.rename(path)
reply=case/'replies'/path.name
for _ in range(250):
    if reply.exists(): print(reply.read_text()); break
    if (case/'exception.json').exists(): print((case/'exception.json').read_text()); sys.exit(1)
    time.sleep(.02)
else: print('REPLY_PENDING: inspect original command/reply; do not reissue')
