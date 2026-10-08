from __future__ import annotations
import hashlib,json,subprocess,sys,time
from pathlib import Path
from policy import target_candidate,unsafe_shared
ROOT=Path(__file__).resolve().parent
SCENARIOS=['BOTH_COMPLETE','CROSS_ONLY','WRONG_B_THEN_RIGHT','O2_COMPLETE_ONLY','INTERLEAVED_COMPLETE','MISSING_ID']
EXPECTED={'BOTH_COMPLETE':'SATISFIED','CROSS_ONLY':'PENDING','WRONG_B_THEN_RIGHT':'SATISFIED','O2_COMPLETE_ONLY':'PENDING','INTERLEAVED_COMPLETE':'SATISFIED','MISSING_ID':'UNKNOWN_ID'}

def formal(out_dir):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=False); rows=[]; schedule=[]
    for rep in range(3):
        rot=SCENARIOS[rep:]+SCENARIOS[:rep]
        schedule += [(rep,s) for s in rot]
    for idx,(rep,s) in enumerate(schedule):
        case=out/f'case-{idx:02d}-{s.lower()}-r{rep}'; case.mkdir(); state=case/'state.json'
        cfg={'scenario':s,'state_path':str(state),'logical_tick':1000+rep}
        p=subprocess.Popen([sys.executable,'-I','-S','-B',str(ROOT/'emitter.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        stdout,stderr=p.communicate(json.dumps(cfg)+'\n',timeout=3)
        events=[json.loads(x) for x in stdout.splitlines() if x.strip()]
        cand,cp=target_candidate(events,'o1'); unsafe,up=unsafe_shared(events)
        final=json.loads(state.read_text()) if state.exists() else None
        row={'index':idx,'rep':rep,'scenario':s,'events':events,'candidate':cand,'candidate_prefix':cp,'unsafe':unsafe,'unsafe_prefix':up,'expected':EXPECTED[s],'target':'o1','final_state':final,'child_returncode':p.returncode,'stderr':stderr}
        (case/'row.json').write_text(json.dumps(row,sort_keys=True,indent=2)+'\n'); rows.append(row)
    raw={'allocation':'app-obligation-keying-2802-20260923-01','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'rows':rows}
    (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'raw_sha256':hashlib.sha256((out/'RAW.json').read_bytes()).hexdigest()},sort_keys=True))
if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='formal': raise SystemExit('usage: run.py formal OUT')
    formal(sys.argv[2])
