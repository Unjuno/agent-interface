import argparse,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--chunk',type=int,required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    plan=json.loads((ROOT/'plan.json').read_text()); rows=plan['chunks'][a.chunk]
    out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); ledger=[]
    for arm,scenario,cid in rows:
        d=out/cid
        p=subprocess.run([sys.executable,str(ROOT/'run_case.py'),'--arm',arm,'--scenario',scenario,'--case-id',cid,'--out',str(d)],capture_output=True,text=True,timeout=20)
        ledger.append({'case_id':cid,'arm':arm,'scenario':scenario,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode:
            (out/'ledger.json').write_text(json.dumps(ledger,sort_keys=True,indent=2)+'\n')
            raise SystemExit(p.returncode)
    (out/'ledger.json').write_text(json.dumps(ledger,sort_keys=True,indent=2)+'\n')
if __name__=='__main__': main()
