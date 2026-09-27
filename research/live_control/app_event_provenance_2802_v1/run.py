from __future__ import annotations
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from policy import candidate, unsafe_timestamp_only

ROOT=Path(__file__).resolve().parent
BOUND_NS=20_000_000
LATE_SLEEP_S=0.040
SCENARIOS=['SAME_DOMAIN_CONTIGUOUS','CROSS_DOMAIN','GAPPED_SEQUENCE','REGRESSED_SEQUENCE','CROSS_SOURCE','LATE_B']
EXPECTED={
 'SAME_DOMAIN_CONTIGUOUS':'SATISFIED',
 'CROSS_DOMAIN':'UNKNOWN_CLOCK_DOMAIN',
 'GAPPED_SEQUENCE':'UNKNOWN_GAP',
 'REGRESSED_SEQUENCE':'UNKNOWN_ORDER',
 'CROSS_SOURCE':'UNKNOWN_SOURCE',
 'LATE_B':'EXPIRED',
}

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def formal(out_dir):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=False)
    rows=[]
    schedule=[]
    for rep in range(3):
        rot=SCENARIOS[rep:]+SCENARIOS[:rep]
        for scenario in rot: schedule.append((rep,scenario))
    for idx,(rep,scenario) in enumerate(schedule):
        case=out/f'case-{idx:02d}-{scenario.lower()}-r{rep}'
        case.mkdir()
        state=case/'state.json'
        cfg={'scenario':scenario,'state_path':str(state),'late_sleep_s':LATE_SLEEP_S}
        started=time.monotonic_ns()
        p=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'emitter.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        stdout,stderr=p.communicate(json.dumps(cfg)+'\n',timeout=3)
        ended=time.monotonic_ns()
        events=[json.loads(x) for x in stdout.splitlines() if x.strip()]
        final_state=json.loads(state.read_text()) if state.exists() else None
        cand=candidate(events,BOUND_NS)
        unsafe=unsafe_timestamp_only(events,BOUND_NS)
        row={
          'index':idx,'rep':rep,'scenario':scenario,'events':events,
          'candidate':cand,'unsafe':unsafe,'expected':EXPECTED[scenario],
          'child_returncode':p.returncode,'stderr':stderr,'final_state':final_state,
          'runner_started_ns':started,'runner_ended_ns':ended,
        }
        (case/'row.json').write_text(json.dumps(row,sort_keys=True,indent=2)+'\n')
        rows.append(row)
    result={'allocation':'app-event-provenance-2802-20260923-01','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'bound_ns':BOUND_NS,'rows':rows}
    (out/'RAW.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'raw_sha256':sha256(out/'RAW.json')},sort_keys=True))

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1] != 'formal': raise SystemExit('usage: run.py formal OUT_DIR')
    formal(sys.argv[2])
