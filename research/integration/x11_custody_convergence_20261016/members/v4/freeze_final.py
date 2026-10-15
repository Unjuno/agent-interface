import datetime, hashlib, json, os, pathlib, subprocess
P=pathlib.Path(__file__).resolve().parent
repo=P.parents[1]/'work/agent-interface'
source=P/'sources/candidate_final'
out=P/'freeze-final'
out.mkdir(exist_ok=False)
parent='5244afd4b88f7dacf6852d350f4c6af40ef33f36'
oldtree='7033516f468398a4abf819d208024969921524ee'
review='4e3a5531072be6953c2b4751c6477570c3ded389'
changed=['runtime/backends/x11_v1/backend.py','runtime/backends/x11_v1/test_sidebutton_ledger.py','.github/workflows/runtime-x11-v1.yml','runtime/integration_checks/native.py']
sha=lambda b:hashlib.sha256(b).hexdigest()
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
env=dict(os.environ,GIT_INDEX_FILE=str(out/'source.index'),GIT_NO_LAZY_FETCH='1')
records=[]
def git(args,input=None):
    start=utc()
    child=subprocess.Popen(['git','-C',str(repo),*args],stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    stdout,stderr=child.communicate(input,timeout=30)
    number=len(records)+1
    for name,raw in [('stdout',stdout),('stderr',stderr)]:
        (out/f'git-{number:02}.{name}').write_bytes(raw)
    records.append({'pid':child.pid,'argv':args,'start':start,'end':utc(),'exit':child.returncode,'streams':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in [('stdout',stdout),('stderr',stderr)]}})
    (out/'GIT_COMMANDS.json').write_bytes((json.dumps(records,indent=2)+'\n').encode())
    if child.returncode:raise RuntimeError('git failed '+str(number))
    return stdout
git(['read-tree',oldtree])
elements=[]
for path in changed:
    raw=(source/path).read_bytes()
    blob=git(['hash-object','-w','--stdin'],raw).decode().strip()
    git(['update-index','--add','--cacheinfo','100644,'+blob+','+path])
    elements.append({'path':path,'mode':'100644','type':'blob','content':raw.decode('utf8')})
tree=git(['write-tree','--missing-ok']).decode().strip()
def inventory(ref):
    raw=git(['ls-tree','-r','-z',ref])
    return {r.split(b'\t',1)[1].decode():tuple(r.split(b'\t',1)[0].decode().split()) for r in raw.split(b'\0') if r}
before,after=inventory(oldtree),inventory(tree)
actual={p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}
if actual!=set(changed):raise RuntimeError('unexpected full tree delta')
images=[]
for p in sorted(set(changed)|{'runtime/backends/x11_v1/test_mapping_boundary.py','runtime/backends/x11_v1/test_text_plan.py','runtime/backends/x11_v1/test_explicit_up_ledger.py','runtime/backends/x11_v1/test_scroll_ledger.py','runtime/backends/x11_v1/test_partial_execution.py'}):
    raw=(source/p).read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if after[p]!=('100644','blob',blob):raise RuntimeError('image differs from tree')
    images.append({'path':p,'mode':'100644','blob':blob,'bytes':len(raw),'sha256':sha(raw)})
full=git(['diff','--binary','--full-index','--no-ext-diff',review,tree,'--',*[i['path'] for i in images]])
(out/'FULL_NINE_DELTA.diff').write_bytes(full)
delta=git(['diff','--binary','--full-index','--no-ext-diff',oldtree,tree,'--',*changed])
(out/'DELTA_FROM_V3.diff').write_bytes(delta)
git(['diff','--check',oldtree,tree,'--',*changed])
git(['diff','--check',review,tree,'--',*[i['path'] for i in images]])
review_delta=git(['diff-tree','-r','--no-commit-id','--name-only',review,tree]).decode().splitlines()
if set(review_delta)!={i['path'] for i in images}:raise RuntimeError('full review path scope')
freeze={'utc':utc(),'parent':parent,'old_tree':oldtree,'review_base':review,'tree':tree,'images':images,'whole_before_entries':len(before),'whole_after_entries':len(after),'modified_existing':3,'added_paths':1,'unchanged_identities':len(before)-3,'full_diff':{'bytes':len(full),'sha256':sha(full)},'delta_from_V3':{'bytes':len(delta),'sha256':sha(delta)},'ref_updated':False,'main_writes':0,'scope':'source content candidate only; not current-main/native application tree'}
(out/'FREEZE.json').write_bytes((json.dumps(freeze,indent=2)+'\n').encode())
(out/'TREE_PAYLOAD.json').write_bytes((json.dumps({'repository_full_name':'Unjuno/agent-interface','base_tree_sha':oldtree,'tree_elements':elements},indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in freeze.items() if k!='images'}))
