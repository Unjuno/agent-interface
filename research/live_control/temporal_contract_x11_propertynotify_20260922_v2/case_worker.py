from __future__ import annotations
import argparse, json
from pathlib import Path
import case_runner

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    ap.add_argument('--scenario',choices=sorted(case_runner.SCENARIOS),required=True)
    ap.add_argument('--case-id',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    out=Path(a.out); assert not out.exists()
    row=case_runner.run_case(Path(a.root),a.scenario,a.case_id)
    out.write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'case_id':a.case_id,'scenario':a.scenario,'terminal':row['candidate_terminal']},sort_keys=True))
if __name__=='__main__': main()
