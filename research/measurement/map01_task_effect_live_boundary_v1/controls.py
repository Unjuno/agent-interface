import json,pathlib,shutil,tempfile,subprocess,sys,hashlib
ROOT=pathlib.Path(__file__).parent
MUTS=['drop_row','duplicate_row','promote_background','promote_state','wrong_plan','early_time','nonneutral','bad_exit','authority']
def reh(root):
 def sh(p): return hashlib.sha256(p.read_bytes()).hexdigest()
 fs={str(p.relative_to(root)):sh(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
 json.dump({'files':fs,'count':len(fs)},open(root/'MANIFEST.json','w'),sort_keys=True,indent=2)
def mutate(root,m):
 rawp=root/'RAW.json'; rows=json.load(open(rawp)); x=rows[0]
 if m=='drop_row': rows.pop()
 elif m=='duplicate_row': rows[-1]=rows[0]
 elif m=='nonneutral': x['final_down']=True
 elif m=='bad_exit': x['app_exit']=3
 else:
  if m in ('promote_background','promote_state'):
   target=next(r for r in rows if r['schedule']==('BACKGROUND_EFFECT' if m=='promote_background' else 'STATE_ONLY'))
   target['score'].update({'disposition':'TASK_EFFECT','scored':True,'t_ns':target['down_ack_ns'],'source':'key_press'})
   json.dump(target['score'],open(root/target['case_id']/'score.json','w'),sort_keys=True,indent=2)
  elif m=='wrong_plan':
   x['score']['plan_id']='forged'; json.dump(x['score'],open(root/x['case_id']/'score.json','w'),sort_keys=True,indent=2)
  elif m=='early_time':
   x['score']['t_ns']=x['down_emit_ns']-1; json.dump(x['score'],open(root/x['case_id']/'score.json','w'),sort_keys=True,indent=2)
  elif m=='authority':
   x['score']['authority']='input'; json.dump(x['score'],open(root/x['case_id']/'score.json','w'),sort_keys=True,indent=2)
 json.dump(rows,open(rawp,'w'),sort_keys=True,indent=2); reh(root)
def main():
 import argparse
 ap=argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--expected-reps',type=int,default=3); a=ap.parse_args()
 src=pathlib.Path(a.src); results={}
 for m in MUTS:
  with tempfile.TemporaryDirectory() as td:
   dst=pathlib.Path(td)/'e'; shutil.copytree(src,dst); mutate(dst,m)
   p=subprocess.run([sys.executable,str(ROOT/'audit.py'),str(dst),'--expected-reps',str(a.expected_reps)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   results[m]=p.returncode!=0
 print(json.dumps(results,sort_keys=True)); return 0 if all(results.values()) else 1
if __name__=='__main__': raise SystemExit(main())
