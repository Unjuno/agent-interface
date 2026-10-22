from __future__ import annotations
import hashlib,json,pathlib,re,subprocess
root=pathlib.Path(__file__).resolve().parent
inp=root/'INPUT'; freeze=json.loads((inp/'FREEZE.json').read_text(encoding='utf-8'))
image=json.loads((root/'image-inspect.json').read_text(encoding='utf-8-sig'))[0]
current_main=subprocess.run(['git','rev-parse','origin/main'],cwd=root.parents[2],capture_output=True,text=True,check=True).stdout.strip()
def git_blob(ref,path):
 r=subprocess.run(['git','rev-parse',f'{ref}:{path}'],cwd=root.parents[2],capture_output=True,text=True)
 return r.stdout.strip() if r.returncode==0 else None
source_rows=[]
for item in list(freeze['sources'].values())+list(freeze['inputs'].values()):
 p=inp/item['path'].split('/')[-1] if item in freeze['sources'].values() else inp/'inputs'/item['path'].split('/')[-1]
 data=p.read_bytes() if p.is_file() else b''
 blob=git_blob(current_main,item['path'])
 source_rows.append({'path':item['path'],'file_bytes_match':p.is_file() and len(data)==item['bytes'],'sha256_match':p.is_file() and hashlib.sha256(data).hexdigest()==item['sha256'],'current_main_git_blob':blob,'current_main_blob_match':blob==item['git_blob']})
log=(root/'results/a01-01/candidate-combined.log').read_text(encoding='utf-8',errors='replace')
rows={}
for name in ('VISUAL_CHANGED','VISUAL_CONTROL'):
 m=re.search(r'^'+name+r'=(\{.*\})\s*$',log,re.M)
 rows[name]=json.loads(m.group(1)) if m else None
checks={
 'source_bytes_and_sha_match':all(x['file_bytes_match'] and x['sha256_match'] for x in source_rows),
 'all_frozen_sources_inputs_match_current_main':all(x['current_main_blob_match'] for x in source_rows),
 'image_id_matches_frozen_run':image.get('Id')=='sha256:4fc7258eb9f2430d573bcbd352fc9851eee6ce96a65ff026274dfb317119bb7b',
 'candidate_exit_zero':(root/'results/a01-01/candidate.exit').read_text().strip()=='0',
 'two_tests_passed':'Ran 2 tests' in log and '\nOK\n' in log,
 'changed_image_hash_differs':bool(rows['VISUAL_CHANGED']) and rows['VISUAL_CHANGED']['source_frame_rgb_sha256']!=rows['VISUAL_CHANGED']['current_frame_rgb_sha256'] and rows['VISUAL_CHANGED']['source_png_sha256']!=rows['VISUAL_CHANGED']['current_png_sha256'],
 'hud_values_identical':bool(rows['VISUAL_CHANGED']) and rows['VISUAL_CHANGED']['source_health_ammo']==rows['VISUAL_CHANGED']['current_health_ammo']==[97,48],
 'changed_visual_did_not_invalidate':bool(rows['VISUAL_CHANGED']) and rows['VISUAL_CHANGED']['monitor_invalidation'] is None and rows['VISUAL_CHANGED']['answer_eligible'] is True,
 'result_stops_before_input_authority':bool(rows['VISUAL_CHANGED']) and rows['VISUAL_CHANGED']['final_status']=='READY_FOR_FRESH_EXECUTOR_ADMISSION' and rows['VISUAL_CHANGED']['executor_admission'] is None and rows['VISUAL_CHANGED']['input_authority_admitted'] is False,
 'same_hash_control_matches_admission':bool(rows['VISUAL_CONTROL']) and rows['VISUAL_CONTROL']['source_frame_rgb_sha256']==rows['VISUAL_CONTROL']['current_frame_rgb_sha256'] and rows['VISUAL_CONTROL']['final_status']=='READY_FOR_FRESH_EXECUTOR_ADMISSION' and rows['VISUAL_CONTROL']['executor_admission'] is None and rows['VISUAL_CONTROL']['input_authority_admitted'] is False,
 'container_removed':(root/'container-inventory-before.txt').read_text(encoding='utf-8-sig').strip()==(root/'container-inventory-after.txt').read_text(encoding='utf-8-sig').strip(),
}
audit={'schema':'visual-context-staleness-a01-independent-audit-v1','decision':'PASS_CONSTRUCTION_VISUAL_FRESHNESS_BOUNDARY' if all(checks.values()) else 'FAIL_AUDIT','checks':checks,'experiment':{'id':freeze['experiment_id'],'frozen_main_commit':freeze['main_commit'],'current_main_commit':current_main,'image_id':image.get('Id'),'source_identity_rows':source_rows,'changed_visual':rows['VISUAL_CHANGED'],'same_hash_control':rows['VISUAL_CONTROL']},'scope':'Historical adjacent V39 observation bytes; exact tested code/input blobs match current main; synthetic planner; no model, game, OS input, executor grant, threat interpretation, recovery or task outcome. READY_FOR_FRESH_EXECUTOR_ADMISSION is not input authority or task success.'}
(root/'results/a01-01/audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
