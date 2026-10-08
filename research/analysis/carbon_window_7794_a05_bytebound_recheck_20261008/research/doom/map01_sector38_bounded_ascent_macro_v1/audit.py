from pathlib import Path
import argparse,json,statistics
ARMS={'short_control':1.25,'bounded_macro':1.60}
def main():
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--plan',required=True);a=p.parse_args();root=Path(a.root);plan=json.loads(Path(a.plan).read_text());errs=[];rows=[]
 for c in plan['cases']:
  d=root/f"case-{c['case']:02d}";f=d/'score.json'
  if not f.exists():errs.append(f"missing:{c['case']}");continue
  s=json.loads(f.read_text());
  for k in ('case','arm','seed','heading'):
   if k=='case': continue
   if s.get(k)!=c[k]:errs.append(f"{c['case']}:{k}")
  if s.get('error') is not None:errs.append(f"{c['case']}:error")
  if not s.get('release_ok'):errs.append(f"{c['case']}:release")
  if s.get('dead'):errs.append(f"{c['case']}:dead")
  if s.get('before',{}).get('sector')!=38 or s.get('before',{}).get('z')>-120:errs.append(f"{c['case']}:precondition")
  req=ARMS[c['arm']];elapsed=s.get('hold_elapsed_ns',0)/1e9
  if abs(elapsed-req)>.12:errs.append(f"{c['case']}:duration")
  rows.append({'case':c,'upper_complete':s.get('upper_complete'),'final_z':s.get('after',{}).get('z'),'final_sector':s.get('after',{}).get('sector'),'elapsed_s':elapsed,'release_ok':s.get('release_ok'),'dead':s.get('dead')})
 bm=[r for r in rows if r['case']['arm']=='bounded_macro'];sc=[r for r in rows if r['case']['arm']=='short_control'];bpass=sum(bool(r['upper_complete']) for r in bm);spass=sum(bool(r['upper_complete']) for r in sc)
 integrity=not errs and len(rows)==len(plan['cases']);decision='FAIL_BOUNDED_ASCENT_MACRO'
 if integrity and bpass==5 and spass<=2:decision='PASS_BOUNDED_ASCENT_MACRO_SCOPED'
 elif integrity and all(r['release_ok'] and not r['dead'] for r in rows):decision='HOLD_NO_ASCENT_HORIZON_DISCRIMINATOR'
 out={'schema':'agent-interface/map01-sector38-ascent-macro-audit-v1','status':'PASS_AUDIT' if integrity else 'FAIL_AUDIT','scientific_decision':decision,'bounded_complete':bpass,'short_complete':spass,'errors':errs,'rows':rows};print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if integrity else 2)
if __name__=='__main__':main()
