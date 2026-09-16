from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main(out: Path):
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for i in range(3):
        case=out/f'case-{i:02d}'
        p=subprocess.run(['xvfb-run','-a',sys.executable,str(HERE/'run_case.py'),str(case)],capture_output=True,text=True,timeout=20)
        (out/f'case-{i:02d}.stdout').write_text(p.stdout);(out/f'case-{i:02d}.stderr').write_text(p.stderr)
        r=json.loads((case/'report.json').read_text()) if (case/'report.json').exists() else {'error':'missing_report'}
        r['case']=i;r['process_returncode']=p.returncode;rows.append(r)
        if p.returncode!=0: break
    (out/'results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'cases':len(rows),'returncodes':[r.get('process_returncode') for r in rows]}))
if __name__=='__main__': main(Path(sys.argv[1]))
