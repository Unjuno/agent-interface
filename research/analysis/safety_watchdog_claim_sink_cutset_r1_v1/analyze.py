from __future__ import annotations
import argparse, ast, hashlib, itertools, json
from pathlib import Path
TASK='SAFETY-WATCHDOG-CLAIM-SINK-CUTSET-R1-20260919-001'
PASS='PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED'
EXPECTED={'watchdog.py':'8c296923db25cd6ec5c948e55ebdad8b82e56fda8123ede4549534172417fe31','run_case.py':'5d477ef04719cc81671d4b5d79af23c2896f11e5ac4a5abed64d1016572a5a1c','run_case_a2.py':'7f4df5cd664e0adbf188abde368f7b3783d570d08cd2e49f6f672efa7fc546a4'}
WA=['verified_empty_ns=time.monotonic_ns()',"receipt['journal_write_start_ns']=time.monotonic_ns()",'os.fsync(f.fileno())',"receipt['journal_write_done_ns']=time.monotonic_ns()",'os.set_blocking(receipt_fd,False)','os.write(receipt_fd,']
RA=['os.set_blocking(receipt_r,False)','os.read(receipt_r,65536)','data_recovery_ns=time.monotonic_ns()','journal_rows=[',"if a.arm=='watchdog_journal'","recovered={'recovery_source':'watchdog_local_journal'"]
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def lines(s,anchors):
    a=s.splitlines(); out=[]
    for x in anchors:
        hits=[i+1 for i,v in enumerate(a) if x in v]
        if len(hits)!=1: raise ValueError((x,hits))
        out.append(hits[0])
    return out
def structural(wd,rc,a2,hashes=True):
    err=[]
    for s in (wd,rc,a2): ast.parse(s)
    if hashes:
        for n,s in [('watchdog.py',wd),('run_case.py',rc),('run_case_a2.py',a2)]:
            if sha(s)!=EXPECTED[n]: err.append('hash:'+n)
    try:
        w=lines(wd,WA); r=lines(rc,RA)
    except Exception as e: return None,['anchor:'+repr(e)]
    if w!=sorted(w): err.append('watchdog_order')
    if r!=sorted(r): err.append('recovery_order')
    if a2.count("with_name('run_case.py')")!=1 or a2.count('.replace(old,new)')!=1 or 'watchdog.py' in a2: err.append('a2_scope')
    return {'watchdog_lines':w,'run_case_lines':r},err
def reach(edges,s,t,failed=frozenset()):
    if s in failed or t in failed: return False
    adj={}
    for a,b in edges:
        if a not in failed and b not in failed: adj.setdefault(a,[]).append(b)
    seen={s}; q=[s]
    while q:
        x=q.pop()
        if x==t: return True
        for y in adj.get(x,[]):
            if y not in seen: seen.add(y); q.append(y)
    return False
def subs(d):
    d=sorted(d)
    for k in range(len(d)+1):
        for c in itertools.combinations(d,k): yield frozenset(c)
def classify(name,edges,s,t,d):
    base=reach(edges,s,t); oracle=all(reach(edges,s,t,f) for f in subs(d)); theorem=reach(edges,s,t,frozenset(d)); cut=None
    for f in subs(d):
        if not reach(edges,s,t,f): cut=len(f); break
    return {'name':name,'base_reachable':base,'arbitrary_oracle':oracle,'arbitrary_theorem':theorem,'min_data_cut':cut,'theorem_match':oracle==theorem,'data':sorted(d),'sink':t}
def classes():
    c=[('owner_dead','release_verified')]
    return [
      classify('release_vs_postrelease_data',c,'owner_dead','release_verified',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      classify('durable_receipt_vs_ordinary_pipe',c+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'ordinary_pipe','ordinary_recovery'}),
      classify('durable_receipt_vs_all_evidence_storage',c+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      classify('republished_receipt_vs_recovery_phase',c+[('release_verified','local_journal'),('local_journal','durable_receipt'),('durable_receipt','ordinary_recovery'),('ordinary_recovery','republished_receipt')],'owner_dead','republished_receipt',{'ordinary_recovery'}),
      classify('pipe_only_local_evidence',c,'owner_dead','local_evidence',{'ordinary_pipe'})]
def move(s,target,anchor,after=False,dedent=0):
    a=s.splitlines(); i=next(i for i,v in enumerate(a) if target in v); line=a.pop(i)
    if dedent: line=' '*dedent+line.lstrip()
    j=next(i for i,v in enumerate(a) if anchor in v)+(1 if after else 0); a.insert(j,line)
    return chr(10).join(a)+chr(10)
def mutations(wd,rc,a2):
    tests={}
    tests['pipe_before_verified']=bool(structural(move(wd,'os.set_blocking(receipt_fd,False)','verified_empty_ns=time.monotonic_ns()'),rc,a2,False)[1])
    tests['verified_after_journal']=bool(structural(move(wd,'verified_empty_ns=time.monotonic_ns()',"receipt['journal_write_done_ns']=time.monotonic_ns()",True),rc,a2,False)[1])
    tests['recovered_before_recovery']=bool(structural(wd,move(rc,"recovered={'recovery_source':'watchdog_local_journal'",'# Ordinary data path recovers only now.',False,8),a2,False)[1])
    tests['a2_scope_change']=bool(structural(wd,rc,a2.replace("with_name('run_case.py')","with_name('watchdog.py')"),False)[1])
    return tests
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pinned',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); p=Path(a.pinned)
    src={n:(p/n).read_text() for n in EXPECTED}; facts,errors=structural(src['watchdog.py'],src['run_case.py'],src['run_case_a2.py']); cls=classes(); muts=mutations(src['watchdog.py'],src['run_case.py'],src['run_case_a2.py'])
    exp={'release_vs_postrelease_data':(True,True,None),'durable_receipt_vs_ordinary_pipe':(True,True,None),'durable_receipt_vs_all_evidence_storage':(True,False,1),'republished_receipt_vs_recovery_phase':(True,False,1),'pipe_only_local_evidence':(False,False,0)}
    for x in cls:
        got=(x['base_reachable'],x['arbitrary_oracle'],x['min_data_cut'])
        if got!=exp[x['name']] or not x['theorem_match']: errors.append('class:'+x['name'])
    if not all(muts.values()): errors.append('mutation_detection')
    result={'task':TASK,'decision':PASS if not errors else 'FAIL_TYPED_SINK_ANALYSIS','errors':errors,'source_sha256':{n:sha(s) for n,s in src.items()},'facts':facts,'classifications':cls,'mutation_controls':muts,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+chr(10)); raise SystemExit(0 if not errors else 2)
if __name__=='__main__': main()
