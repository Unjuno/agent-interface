"""Read-only audit; does not import policy model or runner."""
import hashlib,json
from pathlib import Path
from oracle import score

ARMS=('NO_CROSS_PRODUCER','COMMON_WORK_ID','ONE_PER_GENERATION','SEMANTIC')

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(directory):
    root=Path(__file__).resolve().parent
    cases=json.loads((root/'CASE_MANIFEST.json').read_text())['cases']
    frozen=json.loads((root/'FREEZE.json').read_text())
    errors=[]
    for name,sha in frozen['files'].items():
        if digest(root/name)!=sha: errors.append('source_hash:'+name)
    raw=[json.loads(l) for l in (Path(directory)/'RAW.jsonl').read_text().splitlines()]
    expected={(c['id'],a) for c in cases for a in ARMS}
    got=[(r['case_id'],r['arm']) for r in raw]
    if len(got)!=len(set(got)) or set(got)!=expected: errors.append('row_coverage')
    index={c['id']:c for c in cases}
    totals={a:{s:dict(duplicates=0,missing=0,unauthorized=0,cross_goal_merges=0,integrity_errors=0) for s in ('shared_id_primary','identity_assignment_boundary')} for a in ARMS}
    for row in raw:
        if row['case_id'] not in index or row['arm'] not in ARMS: continue
        case=index[row['case_id']]
        metrics=score(case,row['outcome'])
        if row['metrics']!=metrics: errors.append('metrics_mismatch:'+row['case_id']+':'+row['arm'])
        for k,v in metrics.items(): totals[row['arm']][case['subset']][k]+=len(v) if isinstance(v,list) else v
        if row['outcome']['peak_entries']>48: errors.append('unbounded_state')
    result=json.loads((Path(directory)/'RESULT.json').read_text())
    if result['totals']!=totals: errors.append('aggregate_mismatch')
    if result['raw_sha256']!=digest(Path(directory)/'RAW.jsonl'): errors.append('raw_digest_mismatch')
    if result['trace_count']!=len(cases) or result['arm_rows']!=len(cases)*4: errors.append('declared_coverage')
    if result['phase']!='construction' or result['formal_invocations']!=0 or result['reruns']!=0: errors.append('invocation_discipline')
    for arm in ('COMMON_WORK_ID','SEMANTIC'):
        if any(totals[arm]['shared_id_primary'].values()): errors.append('primary_correctness:'+arm)
    if any(totals['SEMANTIC']['identity_assignment_boundary'].values()): errors.append('boundary_correctness')
    if totals['NO_CROSS_PRODUCER']['shared_id_primary']['duplicates']<=0: errors.append('baseline_not_exposed')
    if totals['ONE_PER_GENERATION']['shared_id_primary']['missing']<=0: errors.append('scheduler_not_exposed')
    if result['model_disposition']!='HOLD_EXISTING_IDEMPOTENCY_ALREADY_SUFFICIENT': errors.append('model_disposition')
    if result['overall_disposition']!='STOP_CONTAINER_RUNTIME_UNAVAILABLE_NO_PROMOTION': errors.append('promotion_boundary')
    return dict(audit='PASS' if not errors else 'FAIL',errors=errors,raw_rows=len(raw),totals=totals)

if __name__=='__main__':
    import sys
    result=audit(sys.argv[1]);print(json.dumps(result,sort_keys=True,indent=2));sys.exit(bool(result['errors']))
