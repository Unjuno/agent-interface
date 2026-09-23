from __future__ import annotations
import hashlib,json,random
from model import decide, immediate
from oracle import expected

TASK='TEMPORAL-SPECULATION-FRESH-REVERSAL-GATE-20260918-001'
SEED=120820260918001
N=250000
MALFORMED=(None,0,2,'1',True)

def fixed_rows():
    rows=[]
    for pair in range(1,33):
        mode='continue' if pair<=16 else 'reverse'
        for side in ('L','R'):
            h=1 if side=='L' else -1
            f=h if mode=='continue' else -h
            rows.append({'pair_id':pair,'side':side,'mode':mode,'history_dir':h,'fresh_dir':f,
                         'nuisance':{'current_identity':'CENTER','roi':'80,60,160,120'}})
    return rows

def random_rows():
    r=random.Random(SEED)
    for i in range(N):
        h=r.choice((-1,1))
        malformed=r.random()<0.10
        if malformed:
            f=r.choice(MALFORMED)
            mode='malformed'
        else:
            rev=bool(r.getrandbits(1)); f=-h if rev else h; mode='reverse' if rev else 'continue'
        nuisance={
            'case_id':i,
            'current_identity':f"center-{r.randrange(1<<20):05x}",
            'history_sha':f"{r.getrandbits(64):016x}",
            'fresh_sha':f"{r.getrandbits(64):016x}",
            'fresh_delay_ns':r.randrange(1_000_000,50_000_001),
        }
        yield {'i':i,'mode':mode,'history_dir':h,'fresh_dir':f,'nuisance':nuisance}

def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)

def main():
    fixed=fixed_rows(); fixed_continue=fixed_reverse=fixed_mismatch=baseline_reverse_miss=0
    fixed_digest=hashlib.sha256()
    for row in fixed:
        got=decide(row['history_dir'],row['fresh_dir'])
        exp=expected(row['history_dir'],row['fresh_dir'])
        fixed_mismatch += got['disposition']!=exp
        fixed_continue += row['mode']=='continue' and got['disposition']=='CONTINUE'
        fixed_reverse += row['mode']=='reverse' and got['disposition']=='YIELD_REVERSAL'
        baseline_reverse_miss += row['mode']=='reverse' and immediate(row['history_dir'])['disposition']=='CONTINUE'
        fixed_digest.update(canon([row,got]).encode())
    mismatch=retro=malformed_fail_closed=valid_continue=valid_reverse=authority=task_input=0
    digest=hashlib.sha256()
    for row in random_rows():
        got=decide(row['history_dir'],row['fresh_dir']); exp=expected(row['history_dir'],row['fresh_dir'])
        mismatch += got['disposition']!=exp
        malformed=row['mode']=='malformed'
        malformed_fail_closed += malformed and got['disposition']=='YIELD_UNKNOWN'
        valid_continue += row['mode']=='continue' and got['disposition']=='CONTINUE'
        valid_reverse += row['mode']=='reverse' and got['disposition']=='YIELD_REVERSAL'
        retro += row['mode']=='reverse' and got['disposition']=='CONTINUE'
        authority += got.get('authority')!='none'
        task_input += got.get('task_input') is not False
        digest.update(canon([row,got]).encode())
    out={
        'task':TASK,'seed':SEED,'primary_invocations':1,'reruns':0,
        'fixed_rows':len(fixed),'fixed_continue_correct':fixed_continue,'fixed_reverse_yielded':fixed_reverse,
        'fixed_candidate_oracle_mismatch':fixed_mismatch,'immediate_baseline_reversal_misses':baseline_reverse_miss,
        'fixed_digest_sha256':fixed_digest.hexdigest(),
        'random_cases':N,'random_candidate_oracle_mismatch':mismatch,'random_reversal_continue_escapes':retro,
        'random_malformed_fail_closed':malformed_fail_closed,'random_continue_correct':valid_continue,'random_reverse_yielded':valid_reverse,
        'authority_grants':authority,'task_input_grants':task_input,'random_digest_sha256':digest.hexdigest(),
    }
    ok=(fixed_continue==32 and fixed_reverse==32 and fixed_mismatch==0 and baseline_reverse_miss==32 and
        mismatch==0 and retro==0 and authority==0 and task_input==0)
    out['decision']='PASS_FRESH_REVERSAL_GATE_SCOPED' if ok else 'FAIL_FRESH_REVERSAL_GATE'
    with open('RESULT.json','x') as f: json.dump(out,f,indent=2,sort_keys=True); f.write('\n')
    print(canon(out))
if __name__=='__main__': main()
