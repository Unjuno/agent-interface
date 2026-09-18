import argparse, json, os, pathlib, random, socket, struct, subprocess, sys, time, hashlib
from protocol import *
from guard import composite_guard,currentness_only
from oracle import decide as oracle_decide
HERE=pathlib.Path(__file__).parent
REQ=struct.Struct('<B');OP_SET=1;OP_GET=2;OP_STOP=9

def recv_exact(c,n):
    out=bytearray()
    while len(out)<n:
        b=c.recv(n-len(out))
        if not b:raise EOFError
        out.extend(b)
    return bytes(out)

def q(xs,p):
    ys=sorted(xs); return ys[int((len(ys)-1)*p)]
def stats(xs):
    return {'n':len(xs),'min_ns':min(xs),'p50_ns':q(xs,.5),'p95_ns':q(xs,.95),'p99_ns':q(xs,.99),'max_ns':max(xs),'mean_ns':sum(xs)/len(xs)}
def connect(path):
    p=subprocess.Popen([sys.executable,str(HERE/'server.py'),path],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    dl=time.monotonic()+3
    while time.monotonic()<dl:
        if os.path.exists(path):
            c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            try:c.connect(path);return p,c
            except OSError:c.close()
        if p.poll() is not None:raise RuntimeError(p.stderr.read())
        time.sleep(.001)
    p.kill();raise TimeoutError('server')
def family_rows(seed, counts):
    fam=[]
    for name,n in counts:
        fam += [name]*n
    r=random.Random(seed); r.shuffle(fam); return fam
def row_spec(name,base_ready_gen):
    if name=='normal_ready':return REG_VALID,base_ready_gen,READY,base_ready_gen
    if name=='readiness_nonready':return REG_VALID,base_ready_gen+1,NONREADY,base_ready_gen+1
    if name=='readiness_aba_old':return REG_VALID,base_ready_gen,READY,base_ready_gen+2
    if name=='hard':return REG_HARD,base_ready_gen,READY,base_ready_gen
    if name=='ambig':return REG_AMBIG,base_ready_gen,READY,base_ready_gen
    if name=='fresh_post_transition':return REG_VALID,base_ready_gen+1,READY,base_ready_gen+1
    raise ValueError(name)
def malformed_controls():
    now=time.perf_counter_ns(); rg=11;base=encode_record(10,REG_VALID,rg,READY,now);out=[]
    def chk(name,data,last=0,erg=rg,scope=SCOPE,gen=GENERATION,nowv=now+1):
        try:composite_guard(data,last,erg,nowv,scope,gen);ok=False
        except ValueError:ok=True
        out.append({'name':name,'rejected':ok})
    bad=bytearray(base);bad[-1]^=1;chk('checksum',bytes(bad));chk('truncated',base[:-1]);chk('nonadvancing',base,last=10);chk('wrong_scope',base,scope=b'other'.ljust(16,b'\0'));chk('wrong_generation',base,gen=GENERATION+1);chk('stale_time',encode_record(11,REG_VALID,rg,READY,now-100_000_000));
    core=CORE.pack(SCOPE,GENERATION,12,99,now,rg,READY);chk('unknown_regime',core+hashlib.blake2b(core,digest_size=DIGEST).digest())
    core=CORE.pack(SCOPE,GENERATION,13,REG_VALID,now,rg,9);chk('unknown_readiness',core+hashlib.blake2b(core,digest_size=DIGEST).digest())
    assert all(x['rejected'] for x in out),out
    return out
def run(seed,counts,warmup=1000):
    controls=malformed_controls(); fams=family_rows(seed,counts); path=f'/tmp/guard1372-{os.getpid()}.sock';p,c=connect(path)
    in_ns=[];sock_ns=[];mismatch=0;identity_mismatch=0;candidate_effects={};negative_stale=0;hard_effect=ambig_effect=0;authority_promotions=0;last_in=last_sock=last_neg=0;base_rg=100
    try:
        for i in range(warmup):
            seq=i+1;data=encode_record(seq,REG_VALID,base_rg,READY);composite_guard(data,i,base_rg)
            c.sendall(REQ.pack(OP_SET)+data);recv_exact(c,1);c.sendall(REQ.pack(OP_GET));back=recv_exact(c,RECORD_SIZE);composite_guard(back,i,base_rg)
        c.sendall(REQ.pack(OP_STOP));c.close();p.wait(timeout=3);p,c=connect(path)
        for idx,name in enumerate(fams,1):
            regime,record_rg,rs,expected_rg=row_spec(name,base_rg)
            data=encode_record(idx,regime,record_rg,rs)
            nd,last_neg=currentness_only(data,last_neg)
            if name in ('readiness_nonready','readiness_aba_old') and nd=='ADMIT':negative_stale+=1
            t0=time.perf_counter_ns();disp,last_in=composite_guard(data,last_in,expected_rg);in_ns.append(time.perf_counter_ns()-t0)
            od=oracle_decide(regime,record_rg,rs,expected_rg)
            if disp!=od:mismatch+=1
            if disp=='ADMIT':candidate_effects[name]=candidate_effects.get(name,0)+1
            if regime==REG_HARD and disp=='ADMIT':hard_effect+=1
            if regime==REG_AMBIG and disp=='ADMIT':ambig_effect+=1
            c.sendall(REQ.pack(OP_SET)+data);recv_exact(c,1)
            t1=time.perf_counter_ns();c.sendall(REQ.pack(OP_GET));back=recv_exact(c,RECORD_SIZE);sdisp,last_sock=composite_guard(back,last_sock,expected_rg);sock_ns.append(time.perf_counter_ns()-t1)
            if back!=data:identity_mismatch+=1
            if sdisp!=disp:mismatch+=1
        c.sendall(REQ.pack(OP_STOP));c.close();p.wait(timeout=3)
    finally:
        try:c.close()
        except Exception:pass
        if p.poll() is None:p.kill();p.wait()
    delta=[b-a for a,b in zip(in_ns,sock_ns)]
    return {'task':'READINESS-CURRENTNESS-AFUNIX-COMPOSITION-20260918-001','seed':seed,'formal_invocations':1,'reruns':0,'counts':dict(counts),'record_size':RECORD_SIZE,'controls':controls,'candidate_oracle_mismatch':mismatch,'record_identity_mismatch':identity_mismatch,'candidate_effects':candidate_effects,'currentness_only_stale_readiness_effects':negative_stale,'hard_effects':hard_effect,'ambiguous_effects':ambig_effect,'readiness_authority_promotions':authority_promotions,'inproc':stats(in_ns),'socket':stats(sock_ns),'delta':stats(delta),'raw_sha256':hashlib.sha256(json.dumps({'in':in_ns,'sock':sock_ns},separators=(',',':')).encode()).hexdigest()}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--small',action='store_true');a=ap.parse_args()
    if a.out.exists():raise SystemExit('result exists')
    counts=[('normal_ready',120000),('readiness_nonready',30000),('readiness_aba_old',30000),('hard',20000),('ambig',20000),('fresh_post_transition',20000)]
    if a.small:counts=[('normal_ready',20),('readiness_nonready',5),('readiness_aba_old',5),('hard',5),('ambig',5),('fresh_post_transition',5)]
    t=time.perf_counter_ns();r=run(a.seed,counts,warmup=20 if a.small else 1000);r['wall_ns']=time.perf_counter_ns()-t;a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
