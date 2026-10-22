from __future__ import annotations
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PKG=ROOT/'research/doom/v39_v15_keymap_after_batch_a05_20261005';OUT=PKG/'results/a01'
def sha(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def stop(reason):
 OUT.mkdir(parents=True,exist_ok=False);(OUT/'STOP.json').write_text(json.dumps({'schema':'v39-v15-keymap-after-batch-stop-v1','reason':reason,'candidate_started':False},indent=2)+'\n');return 2
freeze=json.loads((PKG/'FREEZE.json').read_text(encoding='utf-8-sig'))
head=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
if head!=freeze['base_commit']:raise SystemExit(stop('base_commit_mismatch'))
for rel,expected in freeze['source_sha256'].items():
 p=ROOT/rel
 if not p.is_file() or sha(p.read_bytes())!=expected:raise SystemExit(stop('source_sha256:'+rel))
if OUT.exists():raise SystemExit('STOP: candidate output path already exists')
OUT.mkdir(parents=True,exist_ok=False)
spec=importlib.util.spec_from_file_location('v39_a05_candidate',PKG/'candidate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
raw=mod.run();(OUT/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'CANDIDATE_EXECUTED','cases':[{'name':x['case'],'keymap_queries_between_ups':x['keymap_queries_between_ups'],'sample_count':x['sample_count'],'dispositions':[r.get('server_keymap_disposition') for r in x['events'] if r.get('event')=='input_release_transition'],'fake_physical_after':x['fake_physical_after']} for x in raw['cases']]},sort_keys=True))
