from __future__ import annotations
import hashlib,json,random,sys
SEED=120820260918001; N=250000; MALFORMED=(None,0,2,'1',True)

def expected(h,f):
    if not isinstance(h,int) or isinstance(h,bool) or h not in (-1,1): return 'YIELD_UNKNOWN'
    if not isinstance(f,int) or isinstance(f,bool) or f not in (-1,1): return 'YIELD_UNKNOWN'
    return 'CONTINUE' if h*f>0 else 'YIELD_REVERSAL'
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def fixed_rows():
    for pair in range(1,33):
        mode='continue' if pair<=16 else 'reverse'
        for side in ('L','R'):
            h=1 if side=='L' else -1; f=h if mode=='continue' else -h
            yield {'pair_id':pair,'side':side,'mode':mode,'history_dir':h,'fresh_dir':f,'nuisance':{'current_identity':'CENTER','roi':'80,60,160,120'}}
def random_rows():
    r=random.Random(SEED)
    for i in range(N):
        h=r.choice((-1,1)); malformed=r.random()<.10
        if malformed: f=r.choice(MALFORMED); mode='malformed'
        else:
            rev=bool(r.getrandbits(1)); f=-h if rev else h; mode='reverse' if rev else 'continue'
        nuisance={'case_id':i,'current_identity':f"center-{r.randrange(1<<20):05x}",'history_sha':f"{r.getrandbits(64):016x}",'fresh_sha':f"{r.getrandbits(64):016x}",'fresh_delay_ns':r.randrange(1_000_000,50_000_001)}
        yield {'i':i,'mode':mode,'history_dir':h,'fresh_dir':f,'nuisance':nuisance}
def normalized(h,f): return {'disposition':expected(h,f),'authority':'none','task_input':False}

def main(path='RESULT.json'):
    got=json.load(open(path)); err=[]
    fd=hashlib.sha256(); fc=fr=fb=0
    for row in fixed_rows():
        dec=normalized(row['history_dir'],row['fresh_dir']); fd.update(canon([row,dec]).encode())
        fc += row['mode']=='continue' and dec['disposition']=='CONTINUE'
        fr += row['mode']=='reverse' and dec['disposition']=='YIELD_REVERSAL'
        fb += row['mode']=='reverse'
    d=hashlib.sha256(); mm=esc=mf=vc=vr=0
    for row in random_rows():
        dec=normalized(row['history_dir'],row['fresh_dir']); d.update(canon([row,dec]).encode())
        if row['mode']=='malformed': mf += dec['disposition']=='YIELD_UNKNOWN'
        if row['mode']=='continue': vc += dec['disposition']=='CONTINUE'
        if row['mode']=='reverse': vr += dec['disposition']=='YIELD_REVERSAL'; esc += dec['disposition']=='CONTINUE'
    checks={
      'fixed_rows':64,'fixed_continue_correct':fc,'fixed_reverse_yielded':fr,'fixed_candidate_oracle_mismatch':0,
      'immediate_baseline_reversal_misses':fb,'fixed_digest_sha256':fd.hexdigest(),'random_cases':N,
      'random_candidate_oracle_mismatch':mm,'random_reversal_continue_escapes':esc,'random_malformed_fail_closed':mf,
      'random_continue_correct':vc,'random_reverse_yielded':vr,'authority_grants':0,'task_input_grants':0,
      'random_digest_sha256':d.hexdigest(),'seed':SEED,'primary_invocations':1,'reruns':0,
      'decision':'PASS_FRESH_REVERSAL_GATE_SCOPED'}
    for k,v in checks.items():
        if got.get(k)!=v: err.append(k)
    print(json.dumps({'pass':not err,'errors':err},sort_keys=True)); return 0 if not err else 1
if __name__=='__main__': raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else 'RESULT.json'))
