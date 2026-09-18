from __future__ import annotations
import ast, hashlib, itertools, json, sys
from pathlib import Path
EXPECTED={
 'watchdog.py':'8c296923db25cd6ec5c948e55ebdad8b82e56fda8123ede4549534172417fe31',
 'run_case.py':'5d477ef04719cc81671d4b5d79af23c2896f11e5ac4a5abed64d1016572a5a1c',
 'run_case_a2.py':'7f4df5cd664e0adbf188abde368f7b3783d570d08cd2e49f6f672efa7fc546a4',
}
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def reach(edges,s,t,failed=frozenset()):
    if s in failed or t in failed:return False
    adj={}
    for a,b in edges:
        if a in failed or b in failed:continue
        adj.setdefault(a,[]).append(b)
    seen={s}; q=[s]
    while q:
        x=q.pop(0)
        if x==t:return True
        for y in adj.get(x,[]):
            if y not in seen:seen.add(y);q.append(y)
    return False
def subs(d):
    d=sorted(d)
    for k in range(len(d)+1):
        for c in itertools.combinations(d,k):yield frozenset(c)
def calc(name,edges,s,t,d):
    base=reach(edges,s,t); arb=all(reach(edges,s,t,f) for f in subs(d)); th=reach(edges,s,t,frozenset(d)); cut=None
    for f in subs(d):
        if not reach(edges,s,t,f):cut=len(f);break
    return (name,base,arb,th,cut)
def main():
    pinned=Path(sys.argv[1]); result=json.loads(Path(sys.argv[2]).read_text()); out=Path(sys.argv[3]); errors=[]
    src={n:(pinned/n).read_text() for n in EXPECTED}
    for n,s in src.items():
        if h(s)!=EXPECTED[n] or result['source_sha256'].get(n)!=EXPECTED[n]: errors.append(['hash',n])
        ast.parse(s)
    wd=src['watchdog.py']; rc=src['run_case.py']; a2=src['run_case_a2.py']
    anchors_w=['verified_empty_ns=time.monotonic_ns()',"receipt['journal_write_start_ns']=time.monotonic_ns()",'os.fsync(f.fileno())',"receipt['journal_write_done_ns']=time.monotonic_ns()",'os.set_blocking(receipt_fd,False)','os.write(receipt_fd,']
    pos=[]
    for x in anchors_w:
        if wd.count(x)!=1:errors.append(['wd_anchor',x,wd.count(x)])
        pos.append(wd.find(x))
    if pos!=sorted(pos):errors.append(['wd_order',pos])
    anchors_r=['os.set_blocking(receipt_r,False)','os.read(receipt_r,65536)','data_recovery_ns=time.monotonic_ns()','journal_rows=[',"if a.arm=='watchdog_journal'","recovered={'recovery_source':'watchdog_local_journal'"]
    pos=[]
    for x in anchors_r:
        if rc.count(x)!=1:errors.append(['rc_anchor',x,rc.count(x)])
        pos.append(rc.find(x))
    if pos!=sorted(pos):errors.append(['rc_order',pos])
    if a2.count("with_name('run_case.py')")!=1 or 'watchdog.py' in a2 or a2.count('.replace(old,new)')!=1:errors.append(['a2_scope'])
    common=[('owner_dead','release_verified')]
    specs=[
      ('release_vs_postrelease_data',common,'owner_dead','release_verified',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      ('durable_receipt_vs_ordinary_pipe',common+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'ordinary_pipe','ordinary_recovery'}),
      ('durable_receipt_vs_all_evidence_storage',common+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      ('republished_receipt_vs_recovery_phase',common+[('release_verified','local_journal'),('local_journal','durable_receipt'),('durable_receipt','ordinary_recovery'),('ordinary_recovery','republished_receipt')],'owner_dead','republished_receipt',{'ordinary_recovery'}),
      ('pipe_only_local_evidence',common,'owner_dead','local_evidence',{'ordinary_pipe'}),
    ]
    expected={x[0]:calc(*x) for x in specs}
    got={c['name']:(c['name'],c['base_reachable'],c['arbitrary_oracle'],c['arbitrary_theorem'],c['min_data_cut']) for c in result['classifications']}
    if got!=expected:errors.append(['classifications',got,expected])
    if result.get('decision')!='PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED':errors.append(['decision'])
    if set(result.get('mutation_controls',{}))!={'pipe_before_verified','verified_after_journal','recovered_before_recovery','a2_scope_change'} or not all(result['mutation_controls'].values()):errors.append(['mutations'])
    aud={'decision':'PASS' if not errors else 'FAIL','errors':errors,'source_hashes':EXPECTED,'classification_count':len(expected)}
    out.write_text(json.dumps(aud,indent=2,sort_keys=True)+'\n'); raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
