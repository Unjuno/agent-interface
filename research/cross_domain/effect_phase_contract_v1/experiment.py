from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, subprocess, sys, time
from pathlib import Path

REQUESTED='desired'

def sha256(p:Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def dump(p:Path,obj): p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def run_case(case:dict,out:Path,receiver:Path):
    out.mkdir(parents=True,exist_ok=False)
    klass=case['effect_class']; behavior=case['behavior']
    start=time.perf_counter_ns()
    pre_effect_reject=False; executed=False; effect_present=False; effect_value=None
    receiver_ack=None; candidate_sha=None; target_sha_before=None; target_sha_after=None
    if klass=='stageable':
        target=out/'authoritative.txt'; candidate=out/'candidate.txt'
        target.write_text('old\n'); target_sha_before=sha256(target)
        candidate.write_text((REQUESTED if behavior=='correct' else 'wrong')+'\n')
        candidate_sha=sha256(candidate)
        candidate_value=candidate.read_text().rstrip('\n')
        if candidate_value != REQUESTED:
            pre_effect_reject=True
        else:
            os.replace(candidate,target); executed=True
        target_sha_after=sha256(target)
        effect_value=target.read_text().rstrip('\n')
        effect_present=(effect_value != 'old')
    elif klass=='direct':
        db=out/'effects.sqlite'
        p=subprocess.run([sys.executable,str(receiver),'--db',str(db),'--effect-id',case['id'],'--requested',REQUESTED,'--behavior',behavior],text=True,capture_output=True)
        if p.returncode != 0: raise RuntimeError((p.returncode,p.stdout,p.stderr))
        executed=True; receiver_ack=json.loads(p.stdout)
        con=sqlite3.connect(db)
        row=con.execute('SELECT value,applied_ns FROM effects WHERE effect_id=?',(case['id'],)).fetchone(); con.close()
        if row:
            effect_present=True; effect_value=row[0]
    else: raise ValueError(klass)
    verified=(effect_value==REQUESTED)
    # Deliberately conflated control vocabulary: any verification failure -> REJECTED_NO_EFFECT.
    legacy_label='COMMITTED' if verified else 'REJECTED_NO_EFFECT'
    if klass=='stageable':
        phase_label='PUBLISHED_VERIFIED' if verified else 'REJECTED_PRE_EFFECT'
    else:
        phase_label='EFFECT_VERIFIED' if verified else 'EFFECT_CONTRADICTED'
    end=time.perf_counter_ns()
    row={**case,'requested':REQUESTED,'start_ns':start,'end_ns':end,
         'pre_effect_reject':pre_effect_reject,'executed':executed,
         'effect_present':effect_present,'effect_value':effect_value,'verified':verified,
         'legacy_label':legacy_label,'phase_label':phase_label,
         'receiver_ack':receiver_ack,'candidate_sha256':candidate_sha,
         'target_sha256_before':target_sha_before,'target_sha256_after':target_sha_after}
    dump(out/'result.json',row); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); ap.add_argument('--receiver',type=Path,required=True); a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for c in plan['cases']: rows.append(run_case(c,a.out/c['id'],a.receiver))
    dump(a.out/'rows.json',rows)

if __name__=='__main__': main()
