from __future__ import annotations
import argparse, ast, hashlib, itertools, json
from pathlib import Path

TASK='SAFETY-WATCHDOG-CLAIM-SINK-CUTSET-R1-20260919-001'
PASS='PASS_WATCHDOG_TYPED_SINK_CUTSET_SCOPED'
EXPECTED={
 'watchdog.py':'8c296923db25cd6ec5c948e55ebdad8b82e56fda8123ede4549534172417fe31',
 'run_case.py':'5d477ef04719cc81671d4b5d79af23c2896f11e5ac4a5abed64d1016572a5a1c',
 'run_case_a2.py':'7f4df5cd664e0adbf188abde368f7b3783d570d08cd2e49f6f672efa7fc546a4',
}

def sha(s:str)->str: return hashlib.sha256(s.encode()).hexdigest()
def one(xs,name):
    if len(xs)!=1: raise ValueError(f'{name}: expected 1, got {xs}')
    return xs[0]
def name_assign_lines(tree,key):
    out=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets): out.append(n.lineno)
    return sorted(out)
def subscript_assign_lines(tree,base,key):
    out=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Assign): continue
        for t in n.targets:
            if isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id==base:
                sl=t.slice
                if isinstance(sl,ast.Constant) and sl.value==key: out.append(n.lineno)
    return sorted(out)
def call_lines(tree,module,attr,first_name=None):
    out=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call): continue
        f=n.func
        if isinstance(f,ast.Attribute) and f.attr==attr and isinstance(f.value,ast.Name) and f.value.id==module:
            if first_name is None or (n.args and isinstance(n.args[0],ast.Name) and n.args[0].id==first_name): out.append(n.lineno)
    return sorted(out)
def if_arm_lines(tree):
    out=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.If): continue
        s=ast.unparse(n.test)
        if "a.arm == 'watchdog_journal'" in s or "arm == 'watchdog_journal'" in s: out.append(n.lineno)
    return sorted(out)
def recovered_dict_lines(tree):
    out=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='recovered' for t in n.targets) and isinstance(n.value,ast.Dict): out.append(n.lineno)
    return sorted(out)

def facts(wd:str,rc:str,a2:str):
    tw,tr,ta=map(ast.parse,(wd,rc,a2))
    f={
      'wd_verified':one(name_assign_lines(tw,'verified_empty_ns'),'wd_verified'),
      'wd_journal_if':one(if_arm_lines(tw),'wd_journal_if'),
      'wd_journal_start':one(subscript_assign_lines(tw,'receipt','journal_write_start_ns'),'wd_journal_start'),
      'wd_fsync':one(call_lines(tw,'os','fsync'),'wd_fsync'),
      'wd_journal_done':one(subscript_assign_lines(tw,'receipt','journal_write_done_ns'),'wd_journal_done'),
      'wd_pipe_nonblock':one(call_lines(tw,'os','set_blocking','receipt_fd'),'wd_pipe_nonblock'),
      'wd_pipe_write':one(call_lines(tw,'os','write','receipt_fd'),'wd_pipe_write'),
      'rc_pipe_recovery_nonblock':one(call_lines(tr,'os','set_blocking','receipt_r'),'rc_pipe_recovery_nonblock'),
      'rc_pipe_read':one(call_lines(tr,'os','read','receipt_r'),'rc_pipe_read'),
      'rc_data_recovery':one(name_assign_lines(tr,'data_recovery_ns'),'rc_data_recovery'),
      'rc_journal_rows':one(name_assign_lines(tr,'journal_rows'),'rc_journal_rows'),
      'rc_recovered':one(recovered_dict_lines(tr),'rc_recovered'),
      'rc_journal_if':one(if_arm_lines(tr),'rc_journal_if'),
    }
    base_calls=[n for n in ast.walk(ta) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='with_name']
    base_literals=[n.args[0].value for n in base_calls if n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str)]
    replace_calls=[n for n in ast.walk(ta) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='replace']
    f['a2_base_literals']=base_literals
    f['a2_replace_calls']=len(replace_calls)
    return f

def validate_sources(wd:str,rc:str,a2:str,enforce_hash=True):
    errors=[]
    if enforce_hash:
        for n,s in [('watchdog.py',wd),('run_case.py',rc),('run_case_a2.py',a2)]:
            if sha(s)!=EXPECTED[n]: errors.append(f'hash:{n}')
    try: f=facts(wd,rc,a2)
    except Exception as e: return None,[f'anchor:{e}']
    if not (f['wd_verified'] < f['wd_journal_if'] <= f['wd_journal_start'] <= f['wd_fsync'] <= f['wd_journal_done'] < f['wd_pipe_nonblock'] < f['wd_pipe_write']): errors.append('watchdog_order')
    if not (f['rc_pipe_recovery_nonblock'] < f['rc_pipe_read'] < f['rc_data_recovery'] < f['rc_journal_rows'] < f['rc_journal_if'] < f['rc_recovered']): errors.append('recovery_order')
    if f['a2_base_literals'] != ['run_case.py'] or f['a2_replace_calls']!=1: errors.append('a2_scope')
    if 'watchdog.py' in a2: errors.append('a2_watchdog_substitution')
    return f,errors

def reachable(edges,source,sink,failed=frozenset()):
    if source in failed or sink in failed: return False
    adj={}
    for a,b in edges:
        if a in failed or b in failed: continue
        adj.setdefault(a,[]).append(b)
    seen={source}; stack=[source]
    while stack:
        x=stack.pop()
        if x==sink:return True
        for y in adj.get(x,[]):
            if y not in seen:seen.add(y);stack.append(y)
    return sink in seen

def subsets(items):
    items=sorted(items)
    for k in range(len(items)+1):
        for c in itertools.combinations(items,k): yield frozenset(c)

def classify(name,edges,source,sink,data):
    base=reachable(edges,source,sink)
    oracle=all(reachable(edges,source,sink,f) for f in subsets(data))
    theorem=reachable(edges,source,sink,frozenset(data))
    cut=None
    for f in subsets(data):
        if not reachable(edges,source,sink,f): cut=len(f); break
    return {'name':name,'source':source,'sink':sink,'data':sorted(data),'base_reachable':base,'arbitrary_oracle':oracle,'arbitrary_theorem':theorem,'min_data_cut':cut,'theorem_match':oracle==theorem}

def classifications():
    common=[('owner_dead','release_verified')]
    return [
      classify('release_vs_postrelease_data',common,'owner_dead','release_verified',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      classify('durable_receipt_vs_ordinary_pipe',common+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'ordinary_pipe','ordinary_recovery'}),
      classify('durable_receipt_vs_all_evidence_storage',common+[('release_verified','local_journal'),('local_journal','durable_receipt')],'owner_dead','durable_receipt',{'local_journal','ordinary_pipe','ordinary_recovery'}),
      classify('republished_receipt_vs_recovery_phase',common+[('release_verified','local_journal'),('local_journal','durable_receipt'),('durable_receipt','ordinary_recovery'),('ordinary_recovery','republished_receipt')],'owner_dead','republished_receipt',{'ordinary_recovery'}),
      classify('pipe_only_local_evidence',common,'owner_dead','local_evidence',{'ordinary_pipe'}),
    ]

def mutations(wd,rc,a2):
    out={}
    x=wd.replace('os.set_blocking(receipt_fd,False)\n','')
    x=x.replace('verified_empty_ns=time.monotonic_ns()\n','os.set_blocking(receipt_fd,False)\nverified_empty_ns=time.monotonic_ns()\n')
    out['pipe_before_verified']=bool(validate_sources(x,rc,a2,False)[1])
    x=wd.replace('verified_empty_ns=time.monotonic_ns()\n','')
    x=x.replace("    receipt['journal_write_done_ns']=time.monotonic_ns()\n","    receipt['journal_write_done_ns']=time.monotonic_ns()\nverified_empty_ns=time.monotonic_ns()\n")
    out['verified_after_journal']=bool(validate_sources(x,rc,a2,False)[1])
    rec_line="            recovered={'recovery_source':'watchdog_local_journal','authority':'none','recovered_publish_ns':time.monotonic_ns(),'receipt':journal_rows[0]}\n"
    x=rc.replace(rec_line,'')
    insert="        recovered={'recovery_source':'watchdog_local_journal','authority':'none','recovered_publish_ns':time.monotonic_ns(),'receipt':None}\n"
    x=x.replace('        # Ordinary data path recovers only now.\n',insert+'        # Ordinary data path recovers only now.\n')
    out['recovered_before_recovery']=bool(validate_sources(wd,x,a2,False)[1])
    x=a2.replace("with_name('run_case.py')","with_name('watchdog.py')")
    out['a2_scope_change']=bool(validate_sources(wd,rc,x,False)[1])
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pinned',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    p=Path(a.pinned); src={n:(p/n).read_text() for n in EXPECTED}
    f,errors=validate_sources(src['watchdog.py'],src['run_case.py'],src['run_case_a2.py'],True)
    cls=classifications(); muts=mutations(src['watchdog.py'],src['run_case.py'],src['run_case_a2.py'])
    expected_cls={
      'release_vs_postrelease_data':(True,True,None),
      'durable_receipt_vs_ordinary_pipe':(True,True,None),
      'durable_receipt_vs_all_evidence_storage':(True,False,1),
      'republished_receipt_vs_recovery_phase':(True,False,1),
      'pipe_only_local_evidence':(False,False,0),
    }
    class_errors=[]
    for c in cls:
        exp=expected_cls[c['name']]
        got=(c['base_reachable'],c['arbitrary_oracle'],c['min_data_cut'])
        if got!=exp or not c['theorem_match']:class_errors.append([c['name'],got,exp,c['theorem_match']])
    errors += [f'class:{x}' for x in class_errors]
    if not all(muts.values()): errors.append('mutation_detection')
    result={'task':TASK,'decision':PASS if not errors else 'FAIL_TYPED_SINK_ANALYSIS','errors':errors,'source_sha256':{n:sha(s) for n,s in src.items()},'facts':f,'classifications':cls,'mutation_controls':muts,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__':main()
