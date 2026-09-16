import argparse,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--chunk',type=int,required=True);ap.add_argument('--out',required=True);a=ap.parse_args();p=json.loads((ROOT/'plan.json').read_text());rows=p['chunks'][a.chunk];out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=False);ledger=[]
 for arm,sc,cid in rows:
  q=subprocess.run([sys.executable,str(ROOT/'run_case.py'),'--arm',arm,'--scenario',sc,'--case-id',cid,'--out',str(out/cid)],capture_output=True,text=True,timeout=20);ledger.append({'case_id':cid,'arm':arm,'scenario':sc,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr})
  if q.returncode:(out/'ledger.json').write_text(json.dumps(ledger,sort_keys=True,indent=2)+'\n');raise SystemExit(q.returncode)
 (out/'ledger.json').write_text(json.dumps(ledger,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
