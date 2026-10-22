from __future__ import annotations
import hashlib,json,pathlib,re,subprocess
root=pathlib.Path(__file__).resolve().parent; inp=root/'INPUT'; freeze=json.loads((inp/'FREEZE.json').read_text(encoding='utf-8')); image=json.loads((root/'image-inspect.json').read_text(encoding='utf-8-sig'))[0]; repo=root.parents[2]
main=subprocess.run(['git','rev-parse','origin/main'],cwd=repo,capture_output=True,text=True,check=True).stdout.strip()
def blob(ref,path):
 r=subprocess.run(['git','rev-parse',f'{ref}:{path}'],cwd=repo,capture_output=True,text=True);return r.stdout.strip() if r.returncode==0 else None
sources=[]
for v in freeze['sources'].values():
 p=inp/v['path'].split('/')[-1]; b=p.read_bytes() if p.is_file() else b''; sources.append({'path':v['path'],'bytes_match':p.is_file() and len(b)==v['bytes'],'sha256_match':p.is_file() and hashlib.sha256(b).hexdigest()==v['sha256'],'current_main_blob':blob(main,v['path']),'current_main_blob_match':blob(main,v['path'])==v['git_blob']})
log=(root/'results/a16-01/candidate-combined.log').read_text(encoding='utf-8',errors='replace'); arms={}
for label in ('A16_HARD','A16_SOFT'):
 m=re.search(r'^'+label+r'=(\{.*\})\s*$',log,re.M);arms[label]=json.loads(m.group(1)) if m else None
hard=arms['A16_HARD'];soft=arms['A16_SOFT']
checks={
 'frozen_sources_match_current_main':all(x['bytes_match'] and x['sha256_match'] and x['current_main_blob_match'] for x in sources),
 'image_digest_matches':image.get('Id')=='sha256:3fdfb56e36e335629eb0442de560c4d78a199dd7443ad99de6c33cfab087460d',
 'candidate_exit_zero':(root/'results/a16-01/candidate.exit').read_text().strip()=='0',
 'two_tests_passed':'Ran 2 tests' in log and '\nOK\n' in log,
 'soft_ammo_preserves_turn_and_rejects_minimum':bool(soft) and soft['pending_source_ammo']==6 and soft['observed_ammo']==4 and soft['monitor_invalidation'] is None and soft['turn_answer_eligible'] is True and soft['final_admission']=='REJECTED_ACTION_NOT_CURRENT' and soft['final_reason']=='ammo_minimum_failed',
 'hard_ammo_invalidates_before_response_eligibility':bool(hard) and hard['pending_source_ammo']==6 and hard['observed_ammo']==0 and hard['monitor_invalidation']['outcome']['status']=='HARD_INVALIDATED' and hard['monitor_invalidation']['outcome']['requires_new_decision'] is True and hard['event_order'].index('pre_interrupt_callback')<hard['event_order'].index('interrupt_request') and hard['turn_answer_eligible'] is False and hard['turn_error']=='answer belongs to an invalidated observation',
 'no_executor_or_input_authority':all(x is not None and x.get('executor_admission') is None and x.get('input_authority_admitted') is False for x in (hard,soft)),
 'container_removed':(root/'container-inventory-before.txt').read_text(encoding='utf-8-sig').strip()==(root/'container-inventory-after.txt').read_text(encoding='utf-8-sig').strip(),
}
audit={'schema':'v39-pending-ammo-a16-independent-audit-v1','decision':'PASS_CONSTRUCTION_SOFT_HARD_PENDING_TURN_BOUNDARY' if all(checks.values()) else 'FAIL_AUDIT','checks':checks,'source_closure':sources,'current_main':main,'frozen_main':freeze['main_commit'],'image_id':image.get('Id'),'arms':arms,'scope':'Synthetic planner and typed observations through frozen current-main V39 monitor, persistent planner adapter, and final action admission. No model inference, game, OS input, executor authority, physical release, recovery, task effect, or live allocation.'}
(root/'results/a16-01/audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,indent=2))
