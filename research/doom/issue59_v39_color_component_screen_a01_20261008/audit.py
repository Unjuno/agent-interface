import hashlib,json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
S=json.loads((HERE/'SAMPLE.json').read_text()); L={x['code']:x for x in json.loads((HERE/'BLIND_LABELS.json').read_text())['labels']}; O=json.loads((HERE/'CANDIDATE_OUTPUT.json').read_text())
RELATIVE=Path('research/doom/results/map01-v39-coast-liveness-live-01/runtime')
ROOT=next((parent/RELATIVE for parent in HERE.parents if (parent/RELATIVE).is_dir()), None)
if ROOT is None:
 ROOT=HERE.parents[1]/'work'/'pr7662-audit-chronology'/RELATIVE
def independent_component_max(path):
 with Image.open(path) as im: pix=list(im.convert('RGB').crop((450,250,830,520)).getdata())
 width=380; height=270; active=set()
 for i,(r,g,b) in enumerate(pix):
  if (r>70 and r>1.25*g and r>1.25*b) or (r>180 and g>100 and b<100 and r>.8*g and g>1.5*b): active.add(i)
 max_area=0
 while active:
  todo=[active.pop()]; area=0
  while todo:
   j=todo.pop();area+=1; x=j%width; y=j//width
   for yy in range(max(0,y-1),min(height,y+2)):
    for xx in range(max(0,x-1),min(width,x+2)):
     k=yy*width+xx
     if k in active:active.remove(k);todo.append(k)
  max_area=max(max_area,area)
 return max_area
checks={}; rows={x['code']:x for x in O['rows']}
checks['sample_size_36']=len(S['entries'])==36==len(rows)
checks['label_inventory_36']=len(L)==36
checks['sample_codes_unique']=len({x['code'] for x in S['entries']})==36
freeze=json.loads((HERE/'FREEZE.json').read_text())
checks['candidate_rule_matches_freeze']=freeze['candidate_rule']['positive']=='at least one component has area >= 8 pixels'
checks['label_access_chronology_disclosed']=freeze['candidate_rule']['labels_accessed_before_candidate_rule_authored'] is True and freeze['candidate_rule']['threshold_frozen_before_label_join'] is False
conf={'tp':0,'fp':0,'fn':0,'tn':0,'uncertain_excluded':0}; assets_ok=True; component_ok=True
for e in S['entries']:
 row=rows[e['code']]; path=ROOT/f"{e['sequence']:03}.png"; raw=path.read_bytes(); assets_ok &= len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
 component_ok &= independent_component_max(path)==row['largest_component']
 label=L[e['code']]['enemy_visible']; pred=row['candidate_positive']
 if label=='uncertain':conf['uncertain_excluded']+=1
 elif pred and label=='present':conf['tp']+=1
 elif pred and label=='absent':conf['fp']+=1
 elif not pred and label=='present':conf['fn']+=1
 else:conf['tn']+=1
checks['all_36_input_asset_hashes']=assets_ok
checks['independent_component_recomputation']=component_ok
checks['candidate_confusion_recomputed']=conf==O['candidate_confusion']
checks['comparison_baseline_matches_merged_record']=O['published_yellow_baseline']=={'tp':3,'fp':0,'fn':13,'tn':18,'uncertain_excluded':2}
checks['candidate_rejects_as_interrupt_trigger']=conf['fp']>0 and conf['tn']==0
checks['scope_is_offline_exploratory']=json.loads((HERE/'FREEZE.json').read_text())['classification']=='offline_exploratory_candidate_screen'
result={'status':'PASS_REPRODUCIBILITY_POSTHOC_CANDIDATE_REJECTED','checks':checks,'independent_confusion':conf,'all_checks_pass':all(checks.values())}
(HERE/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)


