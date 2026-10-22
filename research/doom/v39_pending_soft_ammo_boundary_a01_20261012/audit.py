from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
FREEZE=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
RAW=json.loads((ROOT/'results/raw.json').read_text(encoding='utf-8'))
PROBE=json.loads((ROOT/'results/cover_fire_probe.json').read_text(encoding='utf-8'))
FREEZE=json.loads((ROOT/'FREEZE.json').read_text(encoding='utf-8'))
checks=[]
def ck(name,condition): checks.append({'name':name,'pass':bool(condition)})
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.run(['git','-C',str(REPO),*args],check=True,capture_output=True,text=True).stdout.strip()
ck('source_commit',FREEZE['source_commit']=='f185a9059d485a4f8d5a65e9e7f6782897f67eae' and RAW['source_commit']==FREEZE['source_commit'])
ck('controller_sha256',sha(ROOT/'source/map01_overlap_controller_v39.py')==FREEZE['controller_sha256']==RAW['controller_sha256'])
ck('guard_sha256',sha(ROOT/'source/observable_signal_guard_v2.py')==FREEZE['guard_sha256']==RAW['guard_sha256'])
ck('controller_git_blob',git('hash-object',str(ROOT/'source/map01_overlap_controller_v39.py'))==FREEZE['controller_blob'])
ck('guard_git_blob',git('hash-object',str(ROOT/'source/observable_signal_guard_v2.py'))==FREEZE['guard_blob'])
for mode in ('normal','optimized'):
    captured=json.loads((ROOT/f'results/{mode}.stdout.txt').read_text(encoding='utf-8-sig'))
    ck(f'{mode}_matches_raw',captured==RAW)
for item in RAW['checks']:
    ck('runner_'+item['name'],item['pass'])
ck('soft_boundary_decision',RAW['cases'][0]['current_ammo']==4 and RAW['cases'][0]['next_action_minimum_ammo']==5 and RAW['cases'][0]['cover_guard_hard_ammo_floor']==1 and RAW['cases'][0]['monitor_result'] is None and RAW['cases'][0]['soft_event_count']==1 and not RAW['cases'][0]['pending_turn_cancel_signal'])
ck('hard_boundary_decision',RAW['cases'][1]['current_ammo']==0 and RAW['cases'][1]['monitor_result']=='ammo:below_hard_minimum' and RAW['cases'][1]['pending_turn_cancel_signal'])
ck('schema_sha256',sha(ROOT/'source/map01_cover_policy_schema_v6.json')==FREEZE['schema_sha256']==PROBE['schema_sha256'])
ck('schema_git_blob',git('hash-object',str(ROOT/'source/map01_cover_policy_schema_v6.json'))==FREEZE['schema_blob'])
ck('followup_probe_sha256',sha(ROOT/'cover_fire_probe.py')==FREEZE['followup_probe_sha256'])
ck('cover_probe_stdout_matches_raw',json.loads((ROOT/'results/cover_fire_probe.stdout.txt').read_text(encoding='utf-8-sig'))==PROBE)
ck('followup_source_commit',PROBE['source_commit']==FREEZE['source_commit']==RAW['source_commit'])
ck('compiled_fire_schedule',PROBE['fire_hold_count']==8 and PROBE['fire_hold_total_ms']==800 and sum(x['duration_ms'] for x in PROBE['cover_program'])==10000)
ck('schema_separates_cover_and_action_floors','minimum_ammo' not in json.loads((ROOT/'source/map01_cover_policy_schema_v6.json').read_text(encoding='utf-8'))['properties']['next_cover_validity']['items']['properties'] and 'minimum_ammo' in json.loads((ROOT/'source/map01_cover_policy_schema_v6.json').read_text(encoding='utf-8'))['properties']['action_validity']['items']['properties'])
ck('pending_loop_renews_cover',PROBE['pending_loop_renewal_call'] is True)
ck('soft_event_composes_with_cover_schedule',PROBE['soft_case']['current_ammo']==4 and PROBE['soft_case']['monitor_result'] is None and PROBE['soft_case']['pending_turn_cancel_signal'] is False and PROBE['fire_hold_count']==8)
for item in PROBE['checks']:
    ck('cover_probe_'+item['name'],item['pass'])
passed=sum(item['pass'] for item in checks)
out={'schema':'issue59-pending-soft-boundary-independent-audit-v1','status':'PASS_SYNTHETIC_BOUNDARY' if passed==len(checks) else 'FAIL','passed':passed,'total':len(checks),'checks':checks,'scope':'frozen source identity and synthetic control-flow replay only'}
(ROOT/'results/audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2,sort_keys=True))
if passed!=len(checks): raise SystemExit(1)

