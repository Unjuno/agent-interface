"""One-shot local allocation. Infrastructure failure stops; task failure is retained."""
from pathlib import Path
import argparse,json,subprocess,sys,time,hashlib

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(__file__).parent;plan=json.loads((root/'prereg.json').read_text());out=Path(a.out);out.mkdir(exist_ok=False)
    for name,sha in plan['source_sha256'].items():
        if digest(root/name)!=sha:raise RuntimeError(f'frozen source mismatch: {name}')
    rows=[];(out/'STARTED.json').write_text(json.dumps({'allocation':plan['allocation_id'],'started_ns':time.time_ns(),'prereg_sha256':digest(root/'prereg.json')}))
    for spec in plan['schedule']:
        case=out/spec['case_id'];cmd=[sys.executable,str(root/'run_case.py'),'--source',str(Path(a.source).resolve()),'--out',str(case),'--scenario',spec['scenario'],'--mode',spec['mode'],'--seed',str(spec['seed']),'--pan',str(spec['pan'])]
        try:
            r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            (out/(spec['case_id']+'.stdout')).write_text(r.stdout);(out/(spec['case_id']+'.stderr')).write_text(r.stderr)
            score=json.loads((case/'score.json').read_text());rows.append(score)
            print(json.dumps({k:score.get(k) for k in ['scenario','mode','seed','pan','decision','independent_success','removed_ids','error']}),flush=True)
            if r.returncode or 'error' in score:raise RuntimeError(f'case infrastructure failure: {spec["case_id"]}')
        except Exception as exc:
            (out/'ABORTED.json').write_text(json.dumps({'error':repr(exc),'completed':len(rows),'planned':len(plan['schedule'])},indent=2));raise
    (out/'COMPLETED.json').write_text(json.dumps({'completed':len(rows),'planned':len(plan['schedule']),'finished_ns':time.time_ns()},indent=2))
if __name__=='__main__':main()
