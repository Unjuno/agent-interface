"""Run the preregistered static action-region diagnostic without GUI input."""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/openttd-l-action-region-diagnostic-01';REPO=HERE.parent.parent
def parse(text):
    value=json.loads(text)
    if set(value)!={'judgment','rationale'} or value['judgment'] not in {'correct','incorrect','uncertain'} or not isinstance(value['rationale'],str) or not 1<=len(value['rationale'])<=400:raise ValueError('invalid diagnostic response')
    return value
plan=json.loads((ROOT/'preregistration.json').read_text());assert plan['status']=='PREREGISTERED_BEFORE_MODEL_CALLS'
for index,condition in enumerate(plan['execution_order'],1):
    spec=plan['conditions'][condition];image=REPO/spec['image'];out=ROOT/condition
    args=[sys.executable,str(HERE/'model_pair_runner_v2.py'),r'C:\Program Files\nodejs\node.exe',str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(image),str(ROOT/'prompt.txt'),str(REPO),str(out),plan['model'],plan['effort']]
    result=subprocess.run(args,capture_output=True,timeout=90);(ROOT/f'{condition}-stdout.txt').write_bytes(result.stdout);(ROOT/f'{condition}-stderr.txt').write_bytes(result.stderr)
    if result.returncode!=0:raise RuntimeError(condition+' model runner failed; no retry')
    events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()];items=[e['item'] for e in events if e.get('type')=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message';typed=parse(items[0]['text']);usage=next(e['usage'] for e in events if e.get('type')=='turn.completed')
    (ROOT/f'{condition}-result.json').write_text(json.dumps({'condition':condition,'typed':typed,'usage':usage},indent=2)+'\n',encoding='utf-8');print(json.dumps({'condition':condition,'typed':typed,'usage':usage}),flush=True)
