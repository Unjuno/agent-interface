"""Validate retained local source/test closure without checkout or test replay."""
from pathlib import Path
import json,hashlib,zipfile,io,re
p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text());metrics=json.loads((p/'metrics.json').read_text())
def need(x,msg):
 if not x:raise SystemExit('FAIL: '+msg)
raw=(p/m['archive']).read_bytes();need(hashlib.sha256(raw).hexdigest()==m['sha256'],'archive hash');z=zipfile.ZipFile(io.BytesIO(raw));names=z.namelist()
need(len(names)==len(set(names)) and set(names)=={x['path'] for x in m['files']},'exact archive closure')
for x in m['files']:
 b=z.read(x['path']);need(len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],'member '+x['path'])
load=lambda n:json.loads(z.read(n));plan=load('PLAN.json');old=load('baseline-v2-files.json');new=load('candidate-v2-files.json')
old_by_path={f['path']:f for f in old};new_by_path={f['path']:f for f in new}
need(len(old_by_path)==len(old) and len(new_by_path)==len(new),'unique file paths')
need(all(old_by_path.get(f['path'])==f for f in new),'candidate subset same bytes')
need(len(old)==metrics['old_files']==35718 and len(new)==metrics['new_files']==2089,'file denominators')
a=sum(x['bytes'] for x in old);b=sum(x['bytes'] for x in new);need(a==metrics['old_bytes']==2864509379 and b==metrics['new_bytes']==10115800,'byte denominators')
need(metrics['byte_fraction_removed']==1-b/a and metrics['candidate_subset_same_bytes'],'byte ratio')
need(any(f['path'].startswith('research/live_control/results/') for f in old) and not any('/' in f['path'].removeprefix('research/live_control/') for f in new if f['path'].startswith('research/live_control/')),'nested research omitted')
runner=z.read('tested-native-runner.py');runner_sha=hashlib.sha256(runner).hexdigest()
commands=[]
for label in ('baseline-v2','candidate-v2'):
 need(load(label+'-checkout.receipt.json')['args'][-1]==plan['base'],'fixed commit checkout')
 node=load(label+'-node.receipt.json');native=load(label+'-native.receipt.json');need(node['exit']==native['exit']==0,'original child exits');commands.append(node['args'])
 txt=z.read(label+'-node.stdout.log').decode();need('tests 47' in txt and 'pass 47' in txt and 'fail 0' in txt and 'skipped 0' in txt,'Node test coverage')
 result=load(label+'-native-checks/result.json');need(result['status']=='PASS' and result['runner_sha256']==runner_sha,'unchanged native runner')
 for suite,n in [('protocol',324),('harness',141)]:
  txt=z.read(label+'-native-checks/'+suite+'.stderr.log').decode();need(re.search(r'Ran '+str(n)+r' tests',txt) and txt.rstrip().endswith('OK'),'Python suite coverage')
need(commands[0]==commands[1],'same Node commands')
old_workflow=z.read('baseline-workflow.yml').decode();new_workflow=z.read('final-workflow.yml').decode();marker='      - uses: actions/setup-python@v5'
need(old_workflow.split(marker,1)[1]==new_workflow.split(marker,1)[1],'unchanged installs/tests/retention')
need('timeout-minutes: 5' in old_workflow and 'timeout-minutes: 5' in new_workflow,'timeout unchanged')
chunk=new_workflow.split('          sparse-checkout: |\n',1)[1].split('          sparse-checkout-cone-mode:',1)[0];need([s.strip() for s in chunk.splitlines() if s.strip()]==plan['candidate_patterns'] and 'sparse-checkout-cone-mode: false' in new_workflow,'tested patterns integrated')
need(load('baseline-clone.receipt.json')['exit']==128 and 'promisor remote' in z.read('baseline-clone.stderr.txt').decode(),'setup failure retained')
cleanup=load('cleanup.json');need(len(cleanup)==2 and all(x['exit']==0 and x['exists_after'] is False and x['tracked_changed']==[] for x in cleanup),'owned worktree cleanup')
print(json.dumps({'status':'PASS_RETAINED_NATIVE_CI_SOURCE_SCOPE','files':len(names),'materialized_bytes':[a,b],'fraction_removed':1-b/a,'scope':'Local same-commit file/test closure; not network, hosted stability, GUI speed or token saving.'}))
