"""Repair packaging only; reuse original staged objects and suppress irrelevant lazy fetch."""
import hashlib,json,os,pathlib,shutil,subprocess
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parent/'agent-interface'
BASE='3e93df3755b8ae8e2e063ed8f61524989e4bf3df'
BRANCH='research/review-accepted-child-6919-7772-20261003'
PREFIX='research/reviews/accepted_child_input_6919_7772_20261003/'
env=os.environ.copy();env['GIT_INDEX_FILE']=str(ROOT/'publication-v2.index');env['GIT_NO_LAZY_FETCH']='1'
def git(*args,data=None):return subprocess.check_output(['git',*args],cwd=REPO,env=env,input=data)
def put(name,value):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
if (ROOT/'PUBLICATION.json').exists():raise ValueError('original push outcome exists; reconcile it instead')
if git('ls-remote','origin','refs/heads/'+BRANCH).strip():raise ValueError('remote review branch already exists')
gitdir=pathlib.Path(subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=REPO).decode().strip())
ordinary_index_before=hashlib.sha256((gitdir/'index').read_bytes()).hexdigest()
shutil.copyfile(ROOT/'publication.index',ROOT/'publication-v2.index')
captures=ROOT/'execution/publication-v1';captures.mkdir()
for p in sorted((ROOT.parent/'primary-relay-input-error-7772-execution/publish').iterdir()):
    if p.is_file():shutil.copyfile(p,captures/p.name)
shutil.copyfile(ROOT.parent/'primary-relay-input-error-7772-execution/publication-owned-stop.json',captures/'owned-stop.json')
excluded={'PUBLICATION.json','READBACK.json','PUBLICATION_V2.json','READBACK_V2.json','SHA256SUMS','SHA256SUMS_V2'}
files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in excluded and not p.name.startswith('publication') and '__pycache__' not in p.parts]
files.append(ROOT/'SHA256SUMS')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)).replace('\\','/')+'\n' for p in files)
with (ROOT/'SHA256SUMS_V2').open('x',encoding='utf-8',newline='\n') as f:f.write(manifest)
files.append(ROOT/'SHA256SUMS_V2')
staged={line.split(b'\t',1)[1].decode():line.split(b' ',2)[1].decode() for line in git('ls-files','--stage').splitlines()}
entries=[];updates=[]
for p in files:
    data=p.read_bytes();path=PREFIX+str(p.relative_to(ROOT)).replace('\\','/')
    oid=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if staged.get(path)!=oid:
        observed=git('hash-object','-w','--stdin',data=data).decode().strip()
        if observed!=oid:raise ValueError('Git blob hash')
        updates.append(('100644 '+oid+'\t'+path+'\0').encode())
    entries.append(dict(path=path,blob=oid,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
if updates:git('update-index','-z','--index-info',data=b''.join(updates))
tree=git('write-tree','--missing-ok').decode().strip()
commit=git('commit-tree',tree,'-p',BASE,data=b'review(#6919): retain first accepted-child FAIL and scoped transport cleanup\n').decode().strip()
git('update-ref','refs/heads/'+BRANCH,commit,'0'*40)
result=subprocess.run(['git','push','origin',commit+':refs/heads/'+BRANCH],cwd=REPO,env=env,capture_output=True)
put('PUBLICATION_V2.json',dict(utc=datetime.now(timezone.utc).isoformat(),branch=BRANCH,commit=commit,tree=tree,parent=BASE,entries=entries,
  manifest_sha256=hashlib.sha256((ROOT/'SHA256SUMS_V2').read_bytes()).hexdigest(),push_argv=['git','push','origin',commit+':refs/heads/'+BRANCH],
  push_exit=result.returncode,push_stdout=result.stdout.decode(errors='replace'),push_stderr=result.stderr.decode(errors='replace'),main_updated=False,
  first_publication='failed before any ref send; original source/capture preserved',lazy_fetch_disabled=True,byte_projection='none; exact bytes'))
if result.returncode:raise RuntimeError('branch push failure/unknown; inspect first v2 result before any retry')
remote=git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]
if remote!=commit:raise ValueError('remote identity')
for entry in entries:
    actual=git('cat-file','blob',entry['blob'])
    if hashlib.sha256(actual).hexdigest()!=entry['sha256']:raise ValueError('Git byte custody')
parents=git('show','-s','--format=%P',remote).decode().strip()
ordinary_index_after=hashlib.sha256((gitdir/'index').read_bytes()).hexdigest()
if parents!=BASE or ordinary_index_after!=ordinary_index_before:raise ValueError('parent/index changed')
put('READBACK_V2.json',dict(utc=datetime.now(timezone.utc).isoformat(),commit=remote,parents=[BASE],files=len(entries),bytes=sum(e['bytes'] for e in entries),
  all_git_bytes_match=True,ordinary_index_before=ordinary_index_before,ordinary_index_after=ordinary_index_after,
  note='actual remote ref identity plus immutable object byte custody; no main change',main_updated=False))
print(json.dumps(dict(branch=BRANCH,commit=remote,files=len(entries),bytes=sum(e['bytes'] for e in entries),all_match=True)))
