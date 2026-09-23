import argparse,hashlib,json,statistics,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'parent'
sys.path.insert(0,str(PARENT))
import runner as parent_runner
from contract import DURATION_NS
TASK='TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-A2-20260918-002'
DELAYS=[130,145,160]*8

def load_batches(d):
    files=[d/f'BATCH_{i:02d}.json' for i in range(8)]
    if not all(p.exists() for p in files): raise RuntimeError('missing_batch')
    rows=[];meta=[]
    for i,p in enumerate(files):
        raw=p.read_bytes();x=json.loads(raw)
        if x.get('task')!=TASK or x.get('batch_index')!=i or x.get('start_pair')!=i*3 or x.get('end_pair_exclusive')!=i*3+3:raise RuntimeError('batch_metadata')
        if x.get('formal_batch_invocation')!=1 or x.get('batch_reruns')!=0:raise RuntimeError('batch_invocation')
        if len(x.get('rows',[]))!=3:raise RuntimeError('batch_rows')
        rows.extend(x['rows']);meta.append({'batch_index':i,'file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    return rows,meta

def validate_rows(rows):
    if [x.get('pair') for x in rows]!=list(range(24)):raise RuntimeError('pair_order')
    for i,x in enumerate(rows):
        if x.get('delay_ms')!=DELAYS[i]:raise RuntimeError('delay')
        arms=x.get('arms',[])
        order=['SOURCE_APPLIED','CURRENT_EVIDENCE'] if i%2==0 else ['CURRENT_EVIDENCE','SOURCE_APPLIED']
        if [a.get('anchor') for a in arms]!=order:raise RuntimeError('arm_order')

def aggregate(d,out):
    p=Path(out)
    if p.exists():raise FileExistsError(out)
    rows,meta=load_batches(d);validate_rows(rows)
    neg=parent_runner.controls(next(x for x in rows[0]['arms'] if x['anchor']=='CURRENT_EVIDENCE'))
    pos=[x for pair in rows for x in pair['arms']]
    src=[x for x in pos if x['anchor']=='SOURCE_APPLIED'];ev=[x for x in pos if x['anchor']=='CURRENT_EVIDENCE']
    lat=[x['future_to_effect_ns'] for x in ev if x['future_to_effect_ns'] is not None]
    r={'task':TASK,'parent_task':'TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-20260918-001',
       'formal_invocations':1,'formal_batch_invocations':8,'batch_reruns':0,'reruns':0,'pairs':len(rows),'rows':rows,'batch_manifest':meta,'negative_controls':neg,
       'source_admissions':sum(x['decision']['admitted'] for x in src),'source_effects':sum(x['status']['effects'] for x in src),'source_expired':sum(x['decision']['reason']=='EXPIRED' for x in src),
       'evidence_admissions':sum(x['decision']['admitted'] for x in ev),'evidence_effects':sum(x['status']['effects'] for x in ev),
       'wrong_effects':sum((x['effect'] is not None and not x['effect'].get('accepted')) for x in pos),
       'negative_admissions':sum(x['admitted'] for x in neg),'negative_effects':sum(x['effect'] for x in neg),
       'future_to_effect_p50_ns':statistics.median(lat),'future_to_effect_p95_ns':sorted(lat)[int(.95*(len(lat)-1))],
       'durations_exact':all(x['duration_ns']==DURATION_NS for x in pos if x['decision']['valid_until_ns'] is not None),'authority_grants':0,'task_input_actions':0}
    p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('rows','negative_controls','batch_manifest')},indent=2,sort_keys=True))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch_dir');ap.add_argument('--out',required=True);a=ap.parse_args();aggregate(Path(a.batch_dir),a.out)
if __name__=='__main__':main()
