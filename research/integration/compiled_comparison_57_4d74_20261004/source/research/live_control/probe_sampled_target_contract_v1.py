"""Replay sampled target contract across actual game and desktop observations."""
import copy,hashlib,json
from pathlib import Path
from PIL import Image
from sampled_target_contract_v1 import evaluate
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 root=HERE/'results/sampled-target-contract-01';root.mkdir(exist_ok=False)
 report={'scope':'offline replay of actual observations, not new live input','sources':{n:sha(HERE/n) for n in ('sampled_target_contract_v1.py','probe_sampled_target_contract_v1.py')},'cases':[],'controls':{}}
 baseline=None
 for cohort in ('live-menu-intent-01','live-menu-mutation-patch-02','live-menu-mutation-focus-01'):
  r=HERE.parent/'benchmark_discovery/results'/cohort;d=read(r/'decision.json');state=read(r/'state.json');source=state['source_observation'];fresh=d['fresh_observation']
  contract={'name':'select_basic_conveyor','box':[985,551,1032,603],'point':[1008,578],'max_age_ms':1000}
  op=r/'runtime'/Path(source['image']).name;np=r/'runtime'/Path(fresh['image']).name
  with Image.open(op) as old,Image.open(np) as new:
   result=evaluate(contract,d['model_answer'],source,fresh,old,new,d['revalidation_clock_ns'])
  assert result['eligible']==d['guard']['eligible'],(cohort,result)
  if result['eligible']:assert result['point']==d['guard']['point'] and result['valid_until_ns']==d['guard']['valid_until_ns']
  report['cases'].append({'cohort':cohort,'result':result,'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in (r/'decision.json',r/'state.json',op,np)}})
 r=HERE/'results/inkscape-fallback-live-01/runtime';ep=r/'events.jsonl';events=[json.loads(l) for l in ep.read_text().splitlines()]
 source=next(e for e in events if e['event']=='observation' and e['sequence']==12);fresh=next(e for e in events if e['event']=='observation' and e['sequence']==15)
 contract={'name':'focus_x_coordinate','box':[509,90,606,123],'point':[550,106],'max_age_ms':1000};intent={'intent':'focus_x_coordinate','execute_once':True};now=fresh['image_ready_ns']
 op=r/Path(source['image']).name;np=r/Path(fresh['image']).name
 with Image.open(op) as old,Image.open(np) as new:
  result=evaluate(contract,intent,source,fresh,old,new,now);assert result['eligible'],result
  assert source['pointer_binding']['focus']!=source['pointer_binding']['surface']
  report['cases'].append({'cohort':'inkscape archived x coordinate field','result':result,'sources':{str(p.relative_to(HERE.parent)):sha(p) for p in (ep,op,np)},'age_clock':'historical image_ready_ns, not current time'})
  for name in ('boolean_age','point_outside_patch','expired','boolean_sequence','focus_disagreement','held_key','invalid_intent_type','changed_target_pixels','same_sequence'):
   c,i,s,f,t=copy.deepcopy(contract),copy.deepcopy(intent),copy.deepcopy(source),copy.deepcopy(fresh),now;image=new.copy()
   if name=='boolean_age':c['max_age_ms']=True
   elif name=='point_outside_patch':c['point']=[700,106]
   elif name=='expired':t=f['capture_ns']+1_000_000_000
   elif name=='boolean_sequence':f['sequence']=True
   elif name=='focus_disagreement':f['input_focus_after']=0
   elif name=='held_key':f['input_state_before']['owned_keycodes']=[38]
   elif name=='invalid_intent_type':i['execute_once']=1
   elif name=='changed_target_pixels':image.paste('red',(509,90,606,123))
   else:f['sequence']=s['sequence']
   outcome=evaluate(c,i,s,f,old,image,t);assert outcome['eligible'] is False,(name,outcome);report['controls'][name]=outcome
 (root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':[(c['cohort'],c['result']['eligible'],c['result']['reason']) for c in report['cases']],'controls':report['controls']},indent=2))
if __name__=='__main__':main()
