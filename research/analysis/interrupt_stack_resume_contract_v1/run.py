import hashlib,json,sys,time
from pathlib import Path
from policy import POLICIES,evaluate

ROOT=Path(__file__).resolve().parent

def safe_truth(s):
    return (s['task_active'] is True and s['interrupt_resolved'] is True and
            s['pending_result'] in ('NONE','KNOWN') and s['source_fresh'] is True and
            s['queue_version_same'] is True and s['target_identity_same'] is True)

def main(out):
    corpus=json.loads((ROOT/'CORPUS.json').read_text())
    rows=[]; started=time.monotonic_ns()
    for s in corpus:
        outputs={p:evaluate(p,s) for p in POLICIES}
        rows.append({'state':s,'safe_resume_truth':safe_truth(s),'outputs':outputs})
    result={
      'schema':'agent-interface/interrupt-stack-resume-contract-v1',
      'allocation':'interrupt-stack-resume-4201-20260923-01',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'started_ns':started,'ended_ns':time.monotonic_ns(),'rows':rows,
      'corpus_sha256':hashlib.sha256((ROOT/'CORPUS.json').read_bytes()).hexdigest(),
    }
    Path(out).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'out':str(out)}))
if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: run.py OUT')
    main(sys.argv[1])
