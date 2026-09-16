import argparse,json,pathlib,subprocess,sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    plan=json.loads(pathlib.Path(args.plan).read_text()); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False)
    rows=[]; case_runner=pathlib.Path(__file__).with_name('run_case.py')
    for item in plan['schedule']:
        case_out=out/item['id']
        cmd=[sys.executable,str(case_runner),'--arm',item['arm'],'--scenario',item['scenario'],'--case-id',item['id'],'--out',str(case_out)]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
        if p.returncode != 0: raise RuntimeError(f"{item['id']} rc={p.returncode} stderr={p.stderr}")
        rows.append(json.loads(p.stdout))
    aggregate={'task':plan['task'],'rows':rows,'formal_reruns':0}
    (out/'aggregate.json').write_text(json.dumps(aggregate,sort_keys=True,indent=2)+'\n')
    print(json.dumps(aggregate,sort_keys=True))
if __name__=='__main__': main()
