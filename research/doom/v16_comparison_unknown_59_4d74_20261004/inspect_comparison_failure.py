from pathlib import Path
import json
r=Path(__file__).resolve().parent/'comparison-guarded-01/episode/runtime'
rows=[json.loads(x) for x in (r/'events.jsonl').read_bytes().splitlines()]
print(json.dumps({'observations':[x for x in rows if x.get('event')=='observation'][-1:],'typed':[x for x in rows if 'typed' in x.get('event','')][-1:],'command_ops':[x.get('command') for x in rows if x.get('event')=='command'],'files':[p.name for p in r.iterdir() if p.is_file() and p.suffix=='.json']}))
