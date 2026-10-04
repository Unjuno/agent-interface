import hashlib, importlib, importlib.util, json, pathlib, sys
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=ROOT/'research/integration/planner_contract_56_4d74_20261004'
TASK=BASE/'r02/formal-output/block-2/C/task-1.json'
IMAGE=BASE/'r02/formal-output/block-2/C/client/runtime/005.png'
CAND=ROOT/'research/integration/compiled_gui_bundle_57_20261004/a12-predicate-lifecycle-guard/candidate.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok: raise ValueError(msg)
need(sha(HERE/'PLAN.md')=='dc72930ebd77dd96c6997bf9ceb63d8f14b75ebdb0cf92b092b5d7714e5d6d90','plan pin')
need(sha(TASK)=='80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64','task pin')
need(sha(IMAGE)=='dceef5c6abee047328d99007369db0fade828b26a02fb83ba931896ae818ed21','image pin')
need(sha(CAND)=='48549d1000a0a307436479fe64ae47fb0322d1e42f2a90a70e613691445526a7','candidate pin')
raw=json.loads((HERE/'RAW.json').read_text()); ans=raw.get('answer')
need(raw['provider_attempts']==1 and raw['exit_code']==0 and not raw['timed_out'],'provider did not return successful one-call result')
need(ans is not None and raw['answer_sha256']==hashlib.sha256((HERE/'answer.json').read_bytes()).hexdigest(),'answer missing/hash mismatch')
need(sha(HERE/'PROMPT.txt')==raw['inputs']['prompt_sha256'],'prompt hash mismatch')
need(sha(HERE/'schema.json')==raw['inputs']['schema_sha256'],'schema hash mismatch')
need(sha(HERE/'MODEL.json')==raw['inputs']['model_catalog_sha256'],'model catalog hash mismatch')
need(sha(TASK)==raw['inputs']['task_sha256'] and sha(IMAGE)==raw['inputs']['image_sha256'] and sha(CAND)==raw['inputs']['candidate_sha256'],'raw source pins mismatch')
need(set(ans)=={'field_point','submit_point','contract','value_crop'},'unexpected output keys')
for key in ('field_point','submit_point'):
 p=ans[key]; need(type(p) is list and len(p)==2 and all(type(x) is int for x in p),f'{key} malformed')
 need(0<=p[0]<1280 and 0<=p[1]<800,f'{key} out of screenshot bounds')
x1,y1,x2,y2=ans['value_crop']; need(all(type(v) is int for v in ans['value_crop']) and 0<=x1<x2<=1280 and 0<=y1<y2<=800,'crop outside 1280x800 source')
row=json.loads(TASK.read_text()); aliases=row['caller']['selected_target']['aliases']; contract=ans['contract']
need(len(contract['actions'])==2,'expected exactly two actions')
need({a['operation'] for a in contract['actions']}=={'enter_token','submit_form'},'required operations absent')
need(all(not any(e['predicate']=='target_valid' for e in a['expected_effect']) for a in contract['actions']),'target_valid in postcondition')
need(any(e['predicate']=='exact_token_visible' and e['value'] is True for a in contract['actions'] if a['operation']=='enter_token' for e in a['expected_effect']),'entry exact-token effect absent')
need(any(e['predicate']=='exact_saved_title' and e['value'] is True for a in contract['actions'] if a['operation']=='submit_form' for e in a['expected_effect']),'submit exact-save effect absent')
action_branches=[b for s in contract['method']['states'] for b in s['branches'] if b['outcome']=='action']
need(len(action_branches)==2 and all(any(c['predicate']=='target_valid' and c['value'] is True for c in b['when']) for b in action_branches),'target_valid true action branches not retained')
need(any(b['outcome']=='complete' and any(c['predicate']=='exact_saved_title' and c['value'] is True for c in b['when']) for s in contract['method']['states'] for b in s['branches']),'completion exact-save gate absent')
sys.path.insert(0,str(BASE/'r02')); sys.path.insert(0,str(BASE/'source/research/live_control'))
baseline=importlib.import_module('planner_contract_schema')
spec=importlib.util.spec_from_file_location('candidate',CAND); candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
compiled=candidate.compile_contract_v2(contract,aliases,'a13-retained-synthetic-only',compile_contract=baseline.compile_contract)
need(len(compiled['actions'])==2,'A12 candidate compilation failed')
report={'pass':True,'provider_attempts':1,'schema_claimevidence':'Codex CLI exited 0 with --output-schema; independent A12 lifecycle compiler accepted contract','field_point':ans['field_point'],'submit_point':ans['submit_point'],'value_crop':ans['value_crop'],'action_branch_count':len(action_branches),'target_valid_postconditions':0,'task_effect_or_efficiency_claim':False,'limitations':['single sampled retained synthetic screenshot','no GUI/input/formal allocation','no grounding correctness or live effect validation','no prompt compliance robustness estimate']}
(HERE/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2))
