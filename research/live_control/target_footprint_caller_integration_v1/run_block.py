from pathlib import Path
import argparse,json,subprocess,sys,time
SCENARIOS=['stable_static','stable_pan','moved_decoy','replaced_square','missing','duplicate','post_repair_pan']
SEED=2041; MODES=['baseline','candidate']
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=False);rows=[];schedule=[]
 for j,sc in enumerate(SCENARIOS):
  pan=0 if sc=='stable_static' else 4
  order=MODES if j%2==0 else list(reversed(MODES))
  for mode in order:schedule.append((SEED,pan,sc,mode))
 (out/'schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
 for i,(seed,pan,sc,mode) in enumerate(schedule):
  name=f'{i:02d}-{seed}-{sc}-{mode}';dest=out/name
  cmd=[sys.executable,str(Path(__file__).with_name('integration_case.py')),'--source',a.source,'--out',str(dest),'--seed',str(seed),'--pan',str(pan),'--scenario',sc,'--mode',mode]
  t=time.time()
  with open(out/(name+'.stdout'),'w') as so,open(out/(name+'.stderr'),'w') as se:
   r=subprocess.run(cmd,stdout=so,stderr=se,text=True,timeout=25)
  row=json.loads((dest/'score.json').read_text());row.update(case=name,exit_code=r.returncode,wall_s=time.time()-t);rows.append(row)
  print(json.dumps({k:row.get(k) for k in ('case','independent_success','caller_outcome','caller_reason','repair_path','wrong_target_deleted','task_input_count','error')}),flush=True)
 (out/'summary.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
 print('done',len(rows),sum(bool(r.get('independent_success')) for r in rows))
if __name__=='__main__':main()
