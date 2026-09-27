import argparse,copy,json,subprocess,sys,tempfile
from pathlib import Path
def mut(d,i):
 x=copy.deepcopy(d)
 if i==0:x['rows']=x['rows'][:-1]
 elif i==1:x['rows'].append(copy.deepcopy(x['rows'][0]))
 elif i==2:x['rows'][0]['candidate_decision']='ALLOW'
 elif i==3:x['rows'][0]['candidate_input_authority']=False
 elif i==4:x['rows'][0]['oracle_decision']='ALLOW'
 elif i==5:x['rows'][0]['scores']=[999]
 elif i==6:x['summary']['candidate_false_allow']=9
 elif i==7:x['decision']='FAIL_TARGET_BELIEF_ADMISSION_CONTRACT'
 elif i==8:x['source_sha256']['experiment.py']='0'*64
 elif i==9:x['formal_invocations']=2
 elif i==10:x['rows'][1]['profile']=x['rows'][0]['profile'];x['rows'][1]['provenance']=x['rows'][0]['provenance'];x['rows'][1]['probe_available']=x['rows'][0]['probe_available']
 else:x['rows'][0]['provenance']='BOGUS'
 return x
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',type=Path,required=True);ap.add_argument('--source-dir',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=json.loads(a.result.read_text());checks=[]
 with tempfile.TemporaryDirectory() as td:
  td=Path(td)
  for i in range(12):
   p=td/f'm{i}.json';p.write_text(json.dumps(mut(d,i),sort_keys=True));cp=subprocess.run([sys.executable,str(a.audit),'--result',str(p),'--source-dir',str(a.source_dir)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);checks.append({'mutation':i,'rejected':cp.returncode!=0})
 o={'controls':12,'rejected':sum(z['rejected'] for z in checks),'checks':checks,'pass':all(z['rejected'] for z in checks)};a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,sort_keys=True));raise SystemExit(0 if o['pass'] else 1)
if __name__=='__main__':main()
