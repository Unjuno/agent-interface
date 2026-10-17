import ast, itertools, json, os, subprocess, sys, time
from pathlib import Path
P=Path(__file__).resolve().parent; I=P/'inputs'; R=P/'results'; REPO=os.environ.get('A06_GIT_REPO','/mnt/d/codex-research/issue59-stale-replan-pr-20261008')
EXPECT={'current_main.py':'50c63fa83969ed518a91e39c08d1ee52064eb636','pr8687_candidate.py':'576d481a3503e8be4d8ceded8a6371b3fe8850fc'}
def frozen_parser(name):
    path=I/name
    git_oid=subprocess.check_output(['git','-c','core.autocrlf=true','-C',REPO,'hash-object','--path=research/doom/doom_controller_failure_cleanup_v1.py',str(path)],text=True).strip()
    if git_oid!=EXPECT[name]: raise RuntimeError(f'blob mismatch: {name} {git_oid}')
    module=ast.parse(path.read_text(encoding='utf-8-sig'))
    c=next(x for x in module.body if isinstance(x,ast.ClassDef) and x.name=='ControllerFailureCleanup')
    m=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name=='__exit__')
    lo=next(i for i,x in enumerate(m.body) if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='events' for y in x.targets))
    hi=next(i for i,x in enumerate(m.body[lo:],lo) if isinstance(x,ast.Assign) and any(isinstance(y,ast.Subscript) and isinstance(y.value,ast.Name) and y.value.id=='receipt' and isinstance(y.slice,ast.Constant) and y.slice.value=='input_release_verified_empty' for y in x.targets))
    body=m.body[lo:hi+1]
    fn=ast.FunctionDef(name='f',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='receipt')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body+[ast.Return(value=ast.Name(id='receipt',ctx=ast.Load()))],decorator_list=[])
    scope={}; exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(path),'exec'),scope)
    return scope['f']
class Reader:
    stdout_reader_retired=True; stdout_reader_errors=[]
    def __init__(self,x): self.events=x
def oracle(rows):
    aa=[x for x in rows if isinstance(x,dict) and x.get('event')=='accepted' and isinstance(x.get('id'),str)]
    tt=[x for x in rows if isinstance(x,dict) and x.get('event')=='terminal' and isinstance(x.get('id'),str)]
    ids=[x['id'] for x in aa]; tids=[x['id'] for x in tt]
    dup=len(set(ids))<len(ids) or len(set(tids))<len(tids)
    complete=not dup and set(ids)<=set(tids)
    safe=complete
    if safe:
        amap={x['id']:x for x in aa}; tmap={x['id']:x for x in tt}
        for key in ids:
            release=tmap[key].get('release')
            if not isinstance(release,dict) or release.get('verified') is not True or release.get('keys_down')!=[] or release.get('buttons_down')!=[]: safe=False; break
            if 'intent_token' in release:
                tok=amap[key].get('intent_token')
                if not isinstance(tok,str) or tok=='' or release['intent_token']!=tok: safe=False; break
    return complete,safe
OMIT=object()
def a(i,t):
    x={'event':'accepted','id':i}
    if t is not OMIT: x['intent_token']=t
    return x
def z(i,k):
    x={'event':'terminal','id':i}
    if k=='none': return x
    if k=='malformed': x['release']='bad'; return x
    d={'verified':k!='unverified','keys_down':[7] if k=='key' else [],'buttons_down':[2] if k=='button' else []}
    if k=='token-a': d['intent_token']='lease-a'
    if k=='token-b': d['intent_token']='lease-b'
    x['release']=d; return x
atoms=[a(i,t) for i in ('cmd-a','cmd-b') for t in (OMIT,'lease-a','lease-b')]+[z(i,k) for i in ('cmd-a','cmd-b') for k in ('none','malformed','empty','token-a','token-b','unverified','key','button')]
def run(fn,rows):
    rec={'stdout_reader_retired':True,'stdout_reader_errors':[],'input_terminals_complete':False,'input_releases_verified_empty':False}
    fn(Reader(rows),rec)
    return rec['input_terminals_complete'],rec['input_releases_verified_empty']
def main():
    mainfn=frozen_parser('current_main.py'); fixfn=frozen_parser('pr8687_candidate.py')
    seen=0; bad=0; fp=0; prof0={}; prof1={}; started=time.perf_counter()
    for n in range(5):
        for seq in itertools.product(range(len(atoms)),repeat=n):
            rows=[atoms[j] for j in seq]; wanted=oracle(rows); old=run(mainfn,rows); new=run(fixfn,rows); seen+=1
            fp+=int(old[1] and not wanted[1]); bad+=int(new!=wanted)
            key=tuple(sorted(seq)); prof0.setdefault(key,set()).add(old); prof1.setdefault(key,set()).add(new)
    saved=json.loads((R/'candidate.json').read_text(encoding='utf-8'))
    audit={'status':'PASS_INDEPENDENT_REPLAY','verified_git_blobs':EXPECT,'atoms':len(atoms),'sequences_replayed':seen,'candidate_oracle_mismatches':bad,'main_false_positive_recount':fp,'main_order_sensitive_multisets':sum(len(v)>1 for v in prof0.values()),'candidate_order_sensitive_multisets':sum(len(v)>1 for v in prof1.values()),'candidate_result_matches_replay':saved['sequence_count']==seen and saved['candidate_mismatches']==bad and saved['current_main_false_positive']==fp and saved['main_order_sensitive_profiles']==sum(len(v)>1 for v in prof0.values()) and saved['candidate_order_sensitive_profiles']==sum(len(v)>1 for v in prof1.values()),'elapsed_seconds':round(time.perf_counter()-started,3)}
    if bad or audit['candidate_order_sensitive_multisets'] or not audit['candidate_result_matches_replay']: audit['status']='FAIL_INDEPENDENT_REPLAY'
    (R/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(audit,sort_keys=True))
    if audit['status']!='PASS_INDEPENDENT_REPLAY': raise SystemExit(1)
if __name__=='__main__': main()



