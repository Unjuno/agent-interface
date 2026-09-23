import argparse, json, os, pathlib, socket, statistics, struct, subprocess, sys, time, hashlib
from protocol import encode_record, schedule, REG_VALID, REG_HARD, REG_AMBIG, SCOPE, GENERATION, CORE, DIGEST
from guard import validate_and_decide

HERE=pathlib.Path(__file__).parent
REQ=struct.Struct('<BQ'); OP_GET=1; OP_HARD=2; OP_STOP=9

def recv_exact(c,n):
    out=bytearray()
    while len(out)<n:
        b=c.recv(n-len(out))
        if not b: raise EOFError
        out.extend(b)
    return bytes(out)

def q(xs,p):
    ys=sorted(xs)
    if not ys:return None
    return ys[int((len(ys)-1)*p)]

def stats(xs):
    return {'n':len(xs),'min_ns':min(xs),'p50_ns':q(xs,.50),'p95_ns':q(xs,.95),'p99_ns':q(xs,.99),'max_ns':max(xs),'mean_ns':sum(xs)/len(xs)}

def malformed_controls():
    now=time.perf_counter_ns(); base=encode_record(10,REG_VALID,now)
    controls=[]
    def rejects(name,data,last_seq=0,now_ns=None,scope=SCOPE,generation=GENERATION):
        try:validate_and_decide(data,last_seq,now_ns or time.perf_counter_ns(),scope,generation);ok=False
        except ValueError:ok=True
        controls.append({'name':name,'rejected':ok})
    bad=bytearray(base);bad[-1]^=1;rejects('checksum',bytes(bad))
    rejects('wrong_scope',base,expected_scope:=0) if False else None
    try:validate_and_decide(base,0,time.perf_counter_ns(),b'other'.ljust(16,b'\0'),GENERATION);controls.append({'name':'wrong_scope','rejected':False})
    except ValueError:controls.append({'name':'wrong_scope','rejected':True})
    try:validate_and_decide(base,0,time.perf_counter_ns(),SCOPE,GENERATION+1);controls.append({'name':'wrong_generation','rejected':False})
    except ValueError:controls.append({'name':'wrong_generation','rejected':True})
    rejects('nonadvancing_seq',base,last_seq=10)
    # unknown regime with valid checksum
    core=CORE.pack(SCOPE,GENERATION,11,99,now); unknown=core+hashlib.blake2b(core,digest_size=DIGEST).digest();rejects('unknown_regime',unknown)
    rejects('truncated',base[:-1])
    stale=encode_record(12,REG_VALID,now-100_000_000);rejects('stale_time',stale,now_ns=now)
    assert all(x['rejected'] for x in controls),controls
    return controls

def connect_server(path):
    proc=subprocess.Popen([sys.executable,str(HERE/'server.py'),path],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        if os.path.exists(path):
            c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            try:c.connect(path);return proc,c
            except OSError:c.close()
        if proc.poll() is not None: raise RuntimeError(proc.stderr.read())
        time.sleep(.001)
    proc.kill();raise TimeoutError('server')

def run(seed,reads,inv,block,warmup):
    regimes=schedule(seed,reads+warmup)
    controls=malformed_controls()
    path=f'/tmp/guard1179-{os.getpid()}.sock';proc,c=connect_server(path)
    inproc=[];sock=[];deltas=[]; invlat=[]; last_in=0;last_sock=0
    hard_effects=0;ambig_effects=0; mismatches=0
    try:
        # warm both paths equally, no retained metrics
        for i in range(warmup):
            regime=regimes[i]
            t0=time.perf_counter_ns(); data=encode_record(i+1,regime); disp, last_in=validate_and_decide(data,last_in); _=time.perf_counter_ns()-t0
            c.sendall(REQ.pack(OP_GET,regime));data=recv_exact(c,len(data)); disp2,last_sock=validate_and_decide(data,last_sock); 
            if disp!=disp2:mismatches+=1
        last_in=0;last_sock=0
        # restart sequence domains by restarting server so both measured arms use seq1..reads
        c.sendall(REQ.pack(OP_STOP,0));c.close();proc.wait(timeout=2)
        proc,c=connect_server(path)
        measured=regimes[warmup:]
        # block counterbalance. Each arm runs exactly same regime block.
        for bs in range(0,reads,block):
            sub=measured[bs:bs+block]; first='inproc' if (bs//block)%2==0 else 'socket'
            for arm in (first,'socket' if first=='inproc' else 'inproc'):
                if arm=='inproc':
                    for j,regime in enumerate(sub,bs+1):
                        t0=time.perf_counter_ns();data=encode_record(j,regime);disp,last_in=validate_and_decide(data,last_in);dt=time.perf_counter_ns()-t0;inproc.append(dt)
                        if regime==REG_HARD and disp=='ADMIT':hard_effects+=1
                        if regime==REG_AMBIG and disp=='ADMIT':ambig_effects+=1
                else:
                    for j,regime in enumerate(sub,bs+1):
                        t0=time.perf_counter_ns();c.sendall(REQ.pack(OP_GET,regime));data=recv_exact(c,57);disp,last_sock=validate_and_decide(data,last_sock);dt=time.perf_counter_ns()-t0;sock.append(dt)
                        if regime==REG_HARD and disp=='ADMIT':hard_effects+=1
                        if regime==REG_AMBIG and disp=='ADMIT':ambig_effects+=1
        # matched by ordinal after counterbalanced blocks; regimes are same, timings are arm vectors.
        deltas=[b-a for a,b in zip(inproc,sock)]
        # invalidation publish -> response -> typed refusal. Server seq continues.
        for _ in range(inv):
            c.sendall(REQ.pack(OP_HARD,0));data=recv_exact(c,57); row_pub=struct.unpack('<16sQQBQ',data[:-16])[4]
            disp,last_sock=validate_and_decide(data,last_sock);end=time.perf_counter_ns();
            if disp!='REFUSE_HARD':hard_effects+=1
            invlat.append(end-row_pub)
        c.sendall(REQ.pack(OP_STOP,0));c.close();proc.wait(timeout=2)
    finally:
        try:c.close()
        except Exception:pass
        if proc.poll() is None: proc.kill();proc.wait()
    return {
      'controls':controls,'reads_per_arm':reads,'invalidation_probes':inv,'warmup_per_arm':warmup,
      'inproc':stats(inproc),'socket':stats(sock),'delta':stats(deltas),'invalidation_to_refusal':stats(invlat),
      'hard_admitted_effects':hard_effects,'ambiguous_admitted_effects':ambig_effects,'disposition_mismatches':mismatches,
      'raw':{'inproc_ns':inproc,'socket_ns':sock,'invalidation_ns':invlat}
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,required=True);ap.add_argument('--reads',type=int,required=True);ap.add_argument('--invalidations',type=int,required=True);ap.add_argument('--block',type=int,required=True);ap.add_argument('--warmup',type=int,default=2000);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
    if a.out.exists():raise SystemExit('result exists')
    t=time.perf_counter_ns();r=run(a.seed,a.reads,a.invalidations,a.block,a.warmup);r['wall_ns']=time.perf_counter_ns()-t;r['seed']=a.seed
    a.out.write_text(json.dumps(r,separators=(',',':'))+'\n'); print(json.dumps({k:v for k,v in r.items() if k!='raw'},indent=2))
if __name__=='__main__':main()
