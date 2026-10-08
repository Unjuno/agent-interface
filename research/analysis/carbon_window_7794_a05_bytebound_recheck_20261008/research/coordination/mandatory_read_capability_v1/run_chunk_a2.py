import argparse,json,pathlib,subprocess,sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--chunk',type=int,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    plan=json.loads(pathlib.Path(args.plan).read_text()); size=plan['chunk_size']; start=args.chunk*size; items=plan['schedule'][start:start+size]
    if not items: raise SystemExit('empty chunk')
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False); rows=[]
    case_runner=pathlib.Path(__file__).with_name('run_case.py')
    for item in items:
        p=subprocess.run([sys.executable,str(case_runner),'--arm',item['arm'],'--scenario',item['scenario'],'--case-id',item['id'],'--out',str(out/item['id'])],capture_output=True,text=True,timeout=20)
        if p.returncode != 0: raise RuntimeError(f"{item['id']} rc={p.returncode} stderr={p.stderr}")
        rows.append(json.loads(p.stdout))
    result={'task':plan['task'],'chunk':args.chunk,'rows':rows}
    (out/'chunk_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
