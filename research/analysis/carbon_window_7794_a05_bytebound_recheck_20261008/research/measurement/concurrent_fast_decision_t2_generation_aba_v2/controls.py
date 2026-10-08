import argparse, copy, json, pathlib, subprocess, sys, tempfile

def audit_copy(audit_py, data, name, mutate):
    d=copy.deepcopy(data); mutate(d)
    with tempfile.TemporaryDirectory(prefix='aba-control-') as td:
        td=pathlib.Path(td); inp=td/'FORMAL.json'; out=td/'AUDIT.json'
        inp.write_text(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n')
        cp=subprocess.run([sys.executable,'-B',str(audit_py),str(inp),'--out',str(out)],capture_output=True,text=True,timeout=30)
        if cp.returncode != 0 or not out.exists():
            return {"name":name,"rejected":True,"mode":"auditor_process_failure"}
        a=json.loads(out.read_text())
        return {"name":name,"rejected":a.get('decision')=='FAIL_AUDIT',"errors":a.get('errors',[])}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); args=ap.parse_args()
    p=pathlib.Path(args.result); data=json.loads(p.read_text()); audit_py=pathlib.Path(__file__).with_name('audit.py')
    muts=[
      ('row_count', lambda d: d['rows'].pop()),
      ('aba_escape', lambda d: next(r for r in d['rows'] if r['class']=='ABA_CLEAR').__setitem__('stale_candidate',True)),
      ('discriminator', lambda d: next(r for r in d['rows'] if r['class']=='ABA_BOUNCE').__setitem__('stale_comparator',False)),
      ('fresh_overinvalidated', lambda d: next(r for r in d['rows'] if r['class']=='FRESH_G2').__setitem__('fresh_effect',False)),
      ('schedule', lambda d: d['rows'][0].__setitem__('class','WATCH' if d['rows'][0]['class']!='WATCH' else 'HARD')),
      ('candidate_oracle', lambda d: d['rows'][1].__setitem__('mismatch',1)),
      ('decision', lambda d: d['summary'].__setitem__('decision','FAIL_T2_GENERATION_ABA_GUARD')),
    ]
    rows=[audit_copy(audit_py,data,n,m) for n,m in muts]
    out={"controls":rows,"rejected":sum(r['rejected'] for r in rows),"total":len(rows),"pass":all(r['rejected'] for r in rows)}
    pathlib.Path(args.out).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
