from __future__ import annotations
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path

POLICIES=('bytes_only','full_entry')
SCENARIOS=('correct','wrong_bytes','wrong_mode','wrong_kind','unrelated_preserved','write_conflict','ref_race')
WRITE='output/effect.txt'; READS=('declared.txt','hidden.txt'); REF='refs/heads/target'

def dump(p,v): Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def env():
    e={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    e.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',LC_ALL='C',
             GIT_AUTHOR_NAME='Fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',
             GIT_COMMITTER_NAME='Fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid',
             GIT_AUTHOR_DATE='2026-09-16T00:00:00+00:00',GIT_COMMITTER_DATE='2026-09-16T00:00:00+00:00')
    return e
class G:
    def __init__(self,d): self.d=Path(d); self.repo=self.d/'repo.git'
    def run(self,*a,data=None,check=True,extra=None):
        ee=env(); ee.update(extra or {})
        p=subprocess.run(['git','--no-replace-objects','-C',str(self.repo),*a],input=data,capture_output=True,env=ee,timeout=10)
        if check and p.returncode: raise RuntimeError((a,p.returncode,p.stderr.decode()))
        return p
    def text(self,*a,**kw): return self.run(*a,**kw).stdout.decode().strip()
    def init(self):
        t=self.d/'template'; t.mkdir(); subprocess.run(['git','init','--bare','-q','--object-format=sha1','--template='+str(t.resolve()),str(self.repo)],env=env(),check=True)
        self.run('config','core.logAllRefUpdates','true'); self.run('config','gc.auto','0')
    def entries(self,oid):
        out={}
        for item in self.run('ls-tree','-rz',oid).stdout.split(b'\0'):
            if item:
                meta,name=item.split(b'\t',1); mode,kind,obj=meta.decode().split(); out[name.decode()]=(mode,kind,obj)
        return out
    def blob_bytes(self,oid,path): return self.run('show',f'{oid}:{path}').stdout
    def build(self,files,parent,msg):
        idx=self.d/f'idx-{time.time_ns()}'; ex={'GIT_INDEX_FILE':str(idx)}; self.run('read-tree','--empty',extra=ex)
        for path,(mode,data) in sorted(files.items()):
            blob=self.text('hash-object','-w','--stdin',data=data); self.run('update-index','--add','--cacheinfo',f'{mode},{blob},{path}',extra=ex)
        tree=self.text('write-tree',extra=ex); a=['commit-tree',tree,'-m',msg];
        if parent: a += ['-p',parent]
        return self.text(*a)
    def parents(self,oid):
        h=self.run('cat-file','-p',oid).stdout.split(b'\n\n',1)[0]; return [x[7:].decode() for x in h.splitlines() if x.startswith(b'parent ')]

def one(root,case):
    d=Path(root)/case['id']; d.mkdir(parents=True); g=G(d); g.init(); token=case['id']
    files={'declared.txt':('100644',b'allow\n'),'hidden.txt':('100644',b'allow\n'),WRITE:('100644',b'old\n'),'keep.txt':('100644',b'keep\n')}
    A=g.build(files,None,'A'); g.run('update-ref','-m','A',REF,A)
    desired=('desired-'+token+'\n').encode(); base=g.entries(A)
    current_files=dict(files)
    if case['scenario']=='unrelated_preserved': current_files['keep.txt']=('100644',b'new keep\n')
    if case['scenario']=='write_conflict': current_files[WRITE]=('100644',b'competing\n')
    current=A
    if current_files!=files:
        current=g.build(current_files,A,'current'); g.run('update-ref','-m','current',REF,current,A)
    cur=g.entries(current)
    reads={p:cur[p] for p in READS}; write_before=base[WRITE]
    candidate_files=dict(current_files); candidate_files[WRITE]=('100644',desired)
    if case['scenario']=='wrong_bytes': candidate_files[WRITE]=('100644',b'wrong\n')
    if case['scenario']=='wrong_mode': candidate_files[WRITE]=('100755',desired)
    if case['scenario']=='wrong_kind': candidate_files[WRITE]=('120000',desired)
    candidate=g.build(candidate_files,current,'candidate')
    cent=g.entries(candidate)
    changed=sorted(p.decode() for p in g.run('diff-tree','--no-commit-id','--name-only','-r','-z',current,candidate).stdout.split(b'\0') if p)
    read_ok=all(cur[p]==reads[p] for p in READS)
    write_ok=(cur[WRITE]==write_before)
    scope_ok=(changed==[WRITE]); parent_ok=(g.parents(candidate)==[current])
    bytes_ok=(WRITE in cent and g.blob_bytes(candidate,WRITE)==desired)
    full_ok=(cent.get(WRITE)==('100644','blob',hashlib.sha1(b'blob '+str(len(desired)).encode()+b'\0'+desired).hexdigest()))
    reason='eligible'
    for ok,name in ((read_ok,'read_conflict'),(write_ok,'write_conflict'),(scope_ok,'scope_mismatch'),(parent_ok,'parent_mismatch')):
        if not ok: reason=name; break
    if reason=='eligible' and not bytes_ok: reason='bytes_postcondition_mismatch'
    if reason=='eligible' and case['policy']=='full_entry' and not full_ok: reason='entry_postcondition_mismatch'
    validated=time.perf_counter_ns(); precommit=current
    if case['scenario']=='ref_race':
        raced=dict(current_files); raced['keep.txt']=('100644',b'race\n'); precommit=g.build(raced,current,'race'); g.run('update-ref','-m','race',REF,precommit,current)
    rc=None; err=''
    if reason=='eligible':
        p=g.run('update-ref','-m','publish',REF,candidate,current,check=False); rc=p.returncode; err=p.stderr.decode(); reason='applied' if rc==0 else 'cas_rejected'
    final=g.text('rev-parse',REF)
    should_apply=case['scenario'] in ('correct','unrelated_preserved')
    correct=(reason=='applied') if should_apply else (reason!='applied')
    row=dict(case, A=A,current=current,candidate=candidate,precommit=precommit,final=final,changed=changed,
             read_ok=read_ok,write_ok=write_ok,scope_ok=scope_ok,parent_ok=parent_ok,bytes_ok=bytes_ok,full_ok=full_ok,
             reason=reason,returncode=rc,stderr=err,should_apply=should_apply,ground_truth_correct=correct,validated_ns=validated)
    dump(d/'result.json',row); return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('plan',type=Path); ap.add_argument('out',type=Path); a=ap.parse_args(); plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True)
    for n,h in plan['source_sha256'].items():
        if hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest()!=h: raise RuntimeError('source mismatch '+n)
    rows=[]
    for c in plan['cases']: rows.append(one(a.out,c))
    dump(a.out/'rows.json',rows)
if __name__=='__main__': main()
