import json, os, sys, time
from pathlib import Path
case=Path(__file__).resolve().parent/sys.argv[1]
index=int(sys.argv[2]); request=json.loads(Path(sys.argv[3]).read_text(encoding='utf-8-sig'))
path=case/'commands'/f'{index:03d}.json'
if path.exists(): raise RuntimeError('command already allocated; inspect original reply instead')
tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(request)+'\n'); tmp.rename(path)
reply=case/'replies'/path.name
for _ in range(250):
    if reply.exists():
        row=json.loads(reply.read_text())
        if isinstance(row.get('reply'),dict) and isinstance(row['reply'].get('image'),dict):row['reply']['image']['data']='[original bytes retained in reply file; view image artifact separately]'
        print(json.dumps(row)); break
    if (case/'exception.json').exists(): print((case/'exception.json').read_text()); sys.exit(1)
    time.sleep(.02)
else: print('REPLY_PENDING: inspect original command/reply; do not reissue')
