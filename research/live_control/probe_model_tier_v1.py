"""Fixed screenshot/proposal ABBA, requested default versus fast on same Luna model."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
root=HERE/'results/model-tier-01';root.mkdir(exist_ok=False)
source=HERE/'results/auto-append-calc-01'
image=source/'runtime/007.png'
# Use exact previously supplied modal prompt and its matching screenshot, no live input.
prompt=HERE/'results/live-append-calc-01/prompt-2.txt'
image=HERE/'results/live-append-calc-01/runtime/007.png'
cache=Path.home()/'.codex/models_cache.json';catalog=json.loads(cache.read_text(encoding='utf-8'))
selected=[]
for m in catalog.get('models',[]):
    if m.get('slug') in ('gpt-5.6-luna','gpt-5.3-codex-spark'):
        selected.append({k:m.get(k) for k in ('slug','input_modalities','supported_reasoning_levels','service_tiers','supported_in_api')})
plan={'order':['default','fast','fast','default'],'model':'gpt-5.6-luna','effort':'low',
      'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'prompt_sha256':hashlib.sha256(prompt.read_bytes()).hexdigest(),
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['probe_model_tier_v1.py','model_tier_runner_v1.py']},
      'catalog_fetched_at':catalog.get('fetched_at'),'catalog_client_version':catalog.get('client_version'),'capabilities':selected,
      'docs':'https://learn.chatgpt.com/docs/agent-configuration/speed',
      'scope':'archived actual Calc dialog screenshot, identical prompt; inference only, no new GUI input; requested service tier, honored tier unavailable'}
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
runs=[]
for n,tier in enumerate(plan['order'],1):
    out=root/f'{n}-{tier}';begin=time.perf_counter_ns()
    result=subprocess.run([sys.executable,str(HERE/'model_tier_runner_v1.py'),r'C:\Program Files\nodejs\node.exe',
                          str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),
                          str(image),str(prompt),str(REPO),str(out),tier],capture_output=True,timeout=90)
    (root/f'{n}-stdout.txt').write_bytes(result.stdout);(root/f'{n}-stderr.txt').write_bytes(result.stderr)
    runs.append({'index':n,'requested_tier':tier,'exit_code':result.returncode,'begin_ns':begin,'end_ns':time.perf_counter_ns()})
    (root/'runs.json').write_text(json.dumps(runs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(runs[-1]),flush=True)
    if result.returncode!=0:break # capability/config failure, no automatic fallback or retry
