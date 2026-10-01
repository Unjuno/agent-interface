"""Single finite allocation. No network, backend, GUI, or model calls."""
import argparse,hashlib,json,os,platform,resource,signal,time
from pathlib import Path
from model import ARMS,simulate
from oracle import score

ROOT=Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value): path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['construction','formal'],required=True);ap.add_argument('--output',required=True);ap.add_argument('--freeze-comment');args=ap.parse_args()
    # In-process resource controls; no worker threads/processes are spawned.
    resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    signal.alarm(60)
    out=Path(args.output);out.mkdir(exist_ok=False)
    dump(out/'STARTED.json',dict(phase=args.phase,pid=os.getpid(),freeze_comment=args.freeze_comment,started_ns=time.time_ns()))
    if args.phase=='formal':
        assert args.freeze_comment and args.freeze_comment.startswith('https://github.com/Unjuno/agent-interface/issues/5265#issuecomment-')
        for name,expected in json.loads((ROOT/'FREEZE.json').read_text())['files'].items():
            assert sha(ROOT/name)==expected,('STOP_SOURCE_DRIFT',name)
    start=time.monotonic()
    cases=json.loads((ROOT/'CASE_MANIFEST.json').read_text())['cases']
    totals={a:{s:dict(duplicates=0,missing=0,unauthorized=0,cross_goal_merges=0,integrity_errors=0) for s in ('shared_id_primary','identity_assignment_boundary')} for a in ARMS}
    with (out/'RAW.jsonl').open('x') as raw:
        for case in cases:
            # Remove every oracle fact before policies receive the schedule.
            events=[{k:v for k,v in e.items() if not k.startswith('oracle_')} for e in case['events']]
            for arm in ARMS:
                outcome=simulate(arm,events);metrics=score(case,outcome)
                raw.write(json.dumps(dict(case_id=case['id'],arm=arm,outcome=outcome,metrics=metrics),sort_keys=True)+'\n')
                for k,v in metrics.items(): totals[arm][case['subset']][k]+=len(v) if isinstance(v,list) else v
    safe=lambda m: not any(m.values())
    sem=totals['SEMANTIC']['shared_id_primary'];simple=totals['COMMON_WORK_ID']['shared_id_primary']
    if not safe(sem): decision='FAIL_SEMANTIC_FINITE_GATES'
    elif safe(simple): decision='HOLD_EXISTING_IDEMPOTENCY_ALREADY_SUFFICIENT'
    else: decision='PASS_CROSS_PRODUCER_EFFECT_COALESCING_SCOPED'
    result=dict(phase=args.phase,model_disposition=decision,overall_disposition='STOP_CONTAINER_RUNTIME_UNAVAILABLE_NO_PROMOTION',trace_count=len(cases),arm_rows=4*len(cases),formal_invocations=int(args.phase=='formal'),reruns=0,totals=totals,raw_sha256=sha(out/'RAW.jsonl'),elapsed_seconds=time.monotonic()-start,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,python=platform.python_version(),platform=platform.platform(),affinity=sorted(os.sched_getaffinity(0)),address_space_limit=resource.getrlimit(resource.RLIMIT_AS),cpu_seconds_limit=resource.getrlimit(resource.RLIMIT_CPU),source_freeze_sha256=sha(ROOT/'FREEZE.json') if (ROOT/'FREEZE.json').exists() else None)
    dump(out/'RESULT.json',result);print(json.dumps(result,sort_keys=True));signal.alarm(0)

if __name__=='__main__':main()
