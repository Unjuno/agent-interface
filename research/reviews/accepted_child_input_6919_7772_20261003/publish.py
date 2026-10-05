"""One additive review branch. Exact byte publication, no checkout/index/main mutation."""
import hashlib,json,os,pathlib,subprocess
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parent/'agent-interface'
BASE='3e93df3755b8ae8e2e063ed8f61524989e4bf3df'
BRANCH='research/review-accepted-child-6919-7772-20261003'
PREFIX='research/reviews/accepted_child_input_6919_7772_20261003/'
env=os.environ.copy();env['GIT_INDEX_FILE']=str(ROOT/'publication.index')
def git(*args,data=None):
    return subprocess.check_output(['git',*args],cwd=REPO,env=env,input=data)
def put(name,value):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
excluded={'publication.index','publication.index.lock','PUBLICATION.json','READBACK.json','SHA256SUMS'}
files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts]
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)).replace('\\','/')+'\n' for p in files)
with (ROOT/'SHA256SUMS').open('x',encoding='utf-8',newline='\n') as f:f.write(manifest)
files.append(ROOT/'SHA256SUMS')
git('read-tree',BASE)
entries=[]
for p in files:
    data=p.read_bytes();path=PREFIX+str(p.relative_to(ROOT)).replace('\\','/')
    oid=git('hash-object','-w','--stdin',data=data).decode().strip()
    git('update-index','--add','--cacheinfo','100644',oid,path)
    entries.append(dict(path=path,blob=oid,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
tree=git('write-tree').decode().strip()
commit=git('commit-tree',tree,'-p',BASE,data=b'review(#6919): retain accepted-child input-error first FAIL and scoped cleanup evidence\n').decode().strip()
git('update-ref','refs/heads/'+BRANCH,commit,'0'*40)
status_before=git('status','--porcelain').decode()
result=subprocess.run(['git','push','origin',commit+':refs/heads/'+BRANCH],cwd=REPO,env=env,capture_output=True)
put('PUBLICATION.json',dict(utc=datetime.now(timezone.utc).isoformat(),branch=BRANCH,commit=commit,tree=tree,parent=BASE,entries=entries,
  manifest_sha256=hashlib.sha256((ROOT/'SHA256SUMS').read_bytes()).hexdigest(),push_argv=['git','push','origin',commit+':refs/heads/'+BRANCH],
  push_exit=result.returncode,push_stdout=result.stdout.decode(errors='replace'),push_stderr=result.stderr.decode(errors='replace'),
  main_updated=False,ordinary_index_unchanged=True,status_before=status_before,byte_projection='none; exact bytes'))
if result.returncode:raise RuntimeError('branch push uncertain/failure; read original publication before any retry')
remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
if remote!=commit:raise ValueError('remote branch identity')
for entry in entries:
    actual=git('show',remote+':'+entry['path'])
    if hashlib.sha256(actual).hexdigest()!=entry['sha256']:raise ValueError('published bytes '+entry['path'])
parents=git('show','-s','--format=%P',remote).decode().strip()
if parents!=BASE or git('status','--porcelain').decode()!=status_before:raise ValueError('parent or ordinary worktree status changed')
put('READBACK.json',dict(utc=datetime.now(timezone.utc).isoformat(),commit=remote,parents=[BASE],files=len(entries),bytes=sum(e['bytes'] for e in entries),all_git_bytes_match=True,
  note='actual ls-remote identity plus local immutable Git-object readback; no main change',main_updated=False))
print(json.dumps(dict(branch=BRANCH,commit=remote,files=len(entries),bytes=sum(e['bytes'] for e in entries),all_match=True)))
