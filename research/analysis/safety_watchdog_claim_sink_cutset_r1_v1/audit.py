from __future__ import annotations
import ast, hashlib, itertools, json, sys
from pathlib import Path
EXPECTED={'watchdog.py':'8c296923db25cd6ec5c948e55ebdad8b82e56fda8123ede4549534172417fe31','run_case.py':'5d477ef04719cc81671d4b5d79af23c2896f11e5ac4a5abed64d1016572a5a1c','run_case_a2.py':'7f4df5cd664e0adbf188abde368f7b3783d570d08cd2e49f6f672efa7fc546a4'}
WA=['verified_empty_ns=time.monotonic_ns()',"receipt['journal_write_start_ns']=time.monotonic_ns()",'os.fsync(f.fileno())',"receipt['journal_write_done_ns']=time.monotonic_ns()",'os.set_blocking(receipt_fd,False)','os.write(receipt_fd,']
RA=['os.set_blocking(receipt_r,False)','os.read(receipt_r,65536)','data_recovery_ns=time.monotonic_ns()','journal_rows=[',"if a.arm=='watchdog_journal'","recovered={'recovery_source':'watchdog_local_journal'"]
def h(s): return hashlib.sha256(s.encode()).hexdigest()
def order(s,a):
    z=s.splitlines(); out=[]
    for x in a:
        q=[i for i,v in enumerate(z) if x in v]
        if len(q)!=1: return False
        out.append(q[0])
    return out==sorted(out)
def reach(e,s,t,f=frozenset()):
    if s in f or t in f: return False
    q=[s]; seen={s}
    while q:
        x=q.pop(0)
        if x==t: return True
        for a,b in e:
            if a==x and a not in f and b not in f and b not in seen: seen.add(b); q.append(b)
    return False
def subs(d):
    d=sorted(d)
    for k in range(len(d)+1):
        for c in itertools.combinations(d,k): yield frozenset(c)
def calc(name,e,s,t,d):
    base=reach(e,s,t); arb=all(reach(e,s,t,f) for f in subs(d)); th=reach(e,s,t,frozenset(d)); cut=None
    for f in subs(d):
        if not reach(e,s,t,f): cut=len(f); break
    return name,base,arb,th,cut
def main():
    p=Path(sys.argv[1]); result=json.loads(Path(sys.argv[2]).read_text()); out=Path(sys.argv[3]); err=[]; src={n:(p/n).read_text() for n in EXPECTED}
    for n,s in src.items():
        ast.parse(s)
        if h(s)!=EXPECTED[n] or result['source_sha256'].get(n)!=EXPECTED[n]: err.append('hash:'+n)
    if not order(src['watchdog.py'],WA): err.append('watchdog_order')
    if not order(src['run_case.py'],RA): err.append('recovery_order')
    a2=src['run_case_a2.py']
    if a2.count("with_name('run_case.py')")!=1 or a2.count('.replace(old,new)')!=1 or 'watchdog.py' in a2: err.append('a2_scope')
    c=[('owner_dead','release_verified')]
    specs=[('release_vs_postrelease_data',c,'owner_dead','release_verified',{'local_journal','ordinary_pipe','ordinary_recovery'}),('durable_receipt_vs_ordinary_pipe',c+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'ordinary_pipe','ordinary_recovery'}),('durable_receipt_vs_all_evidence_storage',c+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'local_journal','ordinary_pipe','ordinary_recovery'}),('republished_receipt_vs_recovery_phase',c+[('release_verified','local_journal'),('local_journal','durable_receipt'),('durable_receipt','ordinary_recovery'),('ordinary_recovery','republished_receipt')],'owner_dead','republished_receipt',{'ordinary_recovery'}),('pipe_only_local_evidence',c,'owner_dead','local_evidence',{'ordinary_pipe'})]
    expected={x[0]:calc(*x) for x in specs}; got={x['name']:(x['name'],x['base_reachable'],x['arbitrary_oracle'],x['arbitrary_theorem'],x['min_data_cut']) for x in result['classifications']}
    if got!=expected: err.append('classifications')
    if result.get('decision')!='PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED': err.append('decision')
    if set(result.get('mutation_controls',{}))!={'pipe_before_verified','verified_after_journal','recovered_before_recovery','a2_scope_change'} or not all(result['mutation_controls'].values()): err.append('mutations')
    out.write_text(json.dumps({'decision':'PASS' if not err else 'FAIL','errors':err,'classification_count':5,'source_hashes':EXPECTED},indent=2,sort_keys=True)+chr(10)); raise SystemExit(0 if not err else 2)
if __name__=='__main__': main()
