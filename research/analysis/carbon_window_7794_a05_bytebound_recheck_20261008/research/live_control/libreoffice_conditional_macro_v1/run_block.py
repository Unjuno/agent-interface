#!/usr/bin/env python3
import argparse,json,subprocess
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(a.root);out=Path(a.out);out.mkdir(parents=True,exist_ok=False);sched=json.loads((root/'schedule.json').read_text())['cases'];ledger=[]
 for i,s in enumerate(sched):
  cid=f'{i:02d}-{s}';cp=subprocess.run(['/usr/bin/python3',str(root/'run_case.py'),'--scenario',s,'--case-id',cid,'--out-dir',str(out/cid),'--macro-source',str(root/'conditional_macro.py'),'--external-writer',str(root/'external_writer.py')],capture_output=True,text=True);row={'index':i,'case_id':cid,'scenario':s,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr};rp=out/cid/'result.json';row['result']=json.loads(rp.read_text()) if rp.exists() else None;ledger.append(row);(out/'ledger.json').write_text(json.dumps(ledger,indent=2,sort_keys=True)+'\n')
  if cp.returncode!=0: print(json.dumps(row,indent=2));return 2
 print(json.dumps({'completed':len(ledger)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
